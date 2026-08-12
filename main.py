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
        print(f"[ERROR] Config file '{CONFIG_PATH}' not found!")
        sys.exit(1)
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="SKYNET Simple Presence Monitoring")
    parser.add_argument("--source", type=str, default=None, help="Video source (path or camera index)")
    parser.add_argument("--output", type=str, default=None, help="Optional output video file path")
    parser.add_argument("--no-display", action="store_true", help="Run headlessly without GUI display")
    args = parser.parse_args()

    config = load_config()

    # Determine video source
    source = args.source if args.source is not None else config.get("source", "video.mp4")

    # Check chair zones in config
    chair_zones = config.get("chair_zones", [])
    if not chair_zones:
        print("\n" + "!"*60)
        print("[PERINGATAN] Belum ada zona kursi yang terdaftar di config.json!")
        print("Jalankan zone_drawer.py dulu untuk mengeset zona kursi video ini:")
        print(f"    python zone_drawer.py {source}")
        print("!"*60 + "\n")
        sys.exit(1)

    print(f"[INFO] Initializing SKYNET Simple Presence Monitoring...")
    print(f"[INFO] Source: {source}")
    print(f"[INFO] Total Chair Zones: {len(chair_zones)}")
    print(f"[INFO] Confidence Threshold: {config.get('confidence', 0.25)}")
    print(f"[INFO] IoU Threshold: {config.get('iou_threshold', 0.15)}")
    print(f"[INFO] Persistence Frames: {config.get('persistence_frames', 15)}")

    # Initialize components
    detector = PersonDetector(
        model_name=config.get("model_name", "yolov8m.pt"),
        confidence=config.get("confidence", 0.1),
        upper_body_ratio=config.get("upper_body_ratio", 0.5)
    )
    rule_engine = RuleZonePresence(config)
    visualizer = Visualizer()

    # Open video capture
    cap_source = int(source) if str(source).isdigit() else source
    cap = cv2.VideoCapture(cap_source)

    if not cap.isOpened():
        print(f"[ERROR] Cannot open video source: {source}")
        sys.exit(1)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps_in = cap.get(cv2.CAP_PROP_FPS)
    if fps_in <= 0:
        fps_in = 25.0

    # Initialize video writer if requested
    writer = None
    if args.output:
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(args.output, fourcc, fps_in, (width, height))
        print(f"[INFO] Saving output video to: {args.output}")

    window_name = "SKYNET Simple Presence Monitoring"
    if not args.no_display:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    print("\n" + "="*50)
    print(" SKYNET MONITORING RUNNING")
    print(" Hotkeys:")
    print("  'q' / ESC : Quit")
    print("  'r'       : Reset all timers/counters")
    print("="*50 + "\n")

    prev_time = time.time()
    fps = 0.0
    frame_count = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print(f"[INFO] End of video stream after {frame_count} frames.")
                break

            frame_count += 1
            curr_time = time.time()
            time_diff = curr_time - prev_time
            if time_diff > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / time_diff)
            prev_time = curr_time

            # Use video time for offline videos, or system time for webcam
            is_live = str(source).isdigit()
            simulated_time = curr_time if is_live else (frame_count / fps_in)

            # 1. Detect person & crop upper body
            detections = detector.detect(frame)

            # 2. Process zone presence rule (with fallback head detection on frame)
            presence_results = rule_engine.process(frame, detections, current_time=simulated_time)

            # 3. Visualize results
            annotated_frame = visualizer.render(frame, presence_results, fps=fps)

            # Write frame to file if output is configured
            if writer:
                writer.write(annotated_frame)

            if frame_count % 50 == 0 or frame_count == total_frames:
                print(f"[INFO] Processed frame {frame_count}/{total_frames}...")

            # Display GUI window
            if not args.no_display:
                cv2.imshow(window_name, annotated_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    print("[INFO] Quit key pressed.")
                    break
                elif key == ord('r'):
                    rule_engine.reset()
                    print("[INFO] All timers and presence counters have been reset.")

    except KeyboardInterrupt:
        print("[INFO] Interrupted by user.")
    finally:
        cap.release()
        if writer:
            writer.release()
            print(f"[INFO] Output video successfully saved to {args.output}")
        if not args.no_display:
            cv2.destroyAllWindows()
        print("[INFO] Application finished.")

if __name__ == "__main__":
    main()
