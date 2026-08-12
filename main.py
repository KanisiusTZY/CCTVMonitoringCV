import argparse
import cv2
import json
import os
import sys
import time

from detectors.person_detector import PersonDetector
from rules.rule_zone_presence import RuleZonePresence
from visualizer import Visualizer

CONFIG_PATH = "config.json"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"[ERROR] File konfigurasi '{CONFIG_PATH}' tidak ditemukan!")
        sys.exit(1)
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="SKYNET Sistem Monitoring Kehadiran Personel")
    parser.add_argument("--source", type=str, default=None, help="Sumber video (path file atau index kamera/RTSP)")
    parser.add_argument("--output", type=str, default=None, help="Path opsional untuk menyimpan video hasil")
    parser.add_argument("--no-display", action="store_true", help="Jalankan dalam mode headless tanpa tampilan GUI")
    args = parser.parse_args()

    config = load_config()

    # Tentukan sumber video
    source = args.source if args.source is not None else config.get("source", "video.mp4")

    # Periksa zona kursi di config
    chair_zones = config.get("chair_zones", [])
    if not chair_zones:
        print("\n" + "!"*60)
        print("[PERINGATAN] Belum ada zona kursi yang terdaftar di config.json!")
        print("Jalankan zone_drawer.py terlebih dahulu untuk mengeset zona kursi:")
        print(f"    python zone_drawer.py {source}")
        print("!"*60 + "\n")
        sys.exit(1)

    print(f"[INFO] Menginisialisasi SKYNET Sistem Monitoring Kehadiran...")
    print(f"[INFO] Sumber Video: {source}")
    print(f"[INFO] Total Zona Kursi: {len(chair_zones)}")
    print(f"[INFO] Model: {config.get('model_name', 'yolov8m.pt')}")
    print(f"[INFO] Confidence Threshold: {config.get('confidence', 0.1)}")
    print(f"[INFO] IoU Threshold: {config.get('iou_threshold', 0.2)}")
    print(f"[INFO] Ambang Waktu Masuk (Enter): {config.get('enter_seconds', 2.0)} detik")
    print(f"[INFO] Ambang Waktu Keluar (Exit): {config.get('exit_seconds', 0.5)} detik")

    # Inisialisasi komponen
    detector = PersonDetector(
        model_name=config.get("model_name", "yolov8m.pt"),
        confidence=config.get("confidence", 0.1),
        upper_body_ratio=config.get("upper_body_ratio", 0.5)
    )
    rule_engine = RuleZonePresence(config)
    visualizer = Visualizer()

    # Buka video capture
    cap_source = int(source) if str(source).isdigit() else source
    cap = cv2.VideoCapture(cap_source)

    if not cap.isOpened():
        print(f"[ERROR] Tidak dapat membuka sumber video: {source}")
        sys.exit(1)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps_in = cap.get(cv2.CAP_PROP_FPS)
    if fps_in <= 0:
        fps_in = 25.0

    # Inisialisasi video writer jika diminta simpan output
    writer = None
    if args.output:
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(args.output, fourcc, fps_in, (width, height))
        print(f"[INFO] Menyimpan video hasil ke: {args.output}")

    window_name = "SKYNET Monitoring Kehadiran Real-Time"
    if not args.no_display:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    print("\n" + "="*50)
    print(" SKYNET MONITORING BERJALAN")
    print(" Tombol Pintas (Hotkeys):")
    print("  'q' / ESC : Keluar (Quit)")
    print("  'r'       : Reset ulang semua timer & counter")
    print("="*50 + "\n")

    prev_time = time.time()
    fps = 0.0
    frame_count = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print(f"[INFO] Akhir aliran video setelah {frame_count} frame.")
                break

            frame_count += 1
            curr_time = time.time()
            time_diff = curr_time - prev_time
            if time_diff > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / time_diff)
            prev_time = curr_time

            # Gunakan waktu simulasi video untuk file offline, atau waktu sistem untuk webcam live
            is_live = str(source).isdigit()
            simulated_time = curr_time if is_live else (frame_count / fps_in)

            # 1. Deteksi personel & potong area upper-body
            detections = detector.detect(frame)

            # 2. Proses aturan kehadiran berbasis waktu (presence rule engine)
            presence_results = rule_engine.process(frame, detections, current_time=simulated_time)

            # 3. Visualisasikan hasil pada frame
            annotated_frame = visualizer.render(frame, presence_results, fps=fps)

            # Tulis frame ke file jika output dikonfigurasi
            if writer:
                writer.write(annotated_frame)

            if frame_count % 50 == 0 or frame_count == total_frames:
                print(f"[INFO] Memproses frame {frame_count}/{total_frames}...")

            # Tampilkan jendela GUI jika bukan mode no-display
            if not args.no_display:
                cv2.imshow(window_name, annotated_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    print("[INFO] Tombol keluar ditekan.")
                    break
                elif key == ord('r'):
                    rule_engine.reset()
                    print("[INFO] Semua timer dan counter kehadiran telah di-reset.")

    except KeyboardInterrupt:
        print("[INFO] Dihentikan oleh pengguna.")
    finally:
        cap.release()
        if writer:
            writer.release()
            print(f"[INFO] Video hasil berhasil disimpan ke {args.output}")
        if not args.no_display:
            cv2.destroyAllWindows()
        print("[INFO] Aplikasi selesai.")

if __name__ == "__main__":
    main()
