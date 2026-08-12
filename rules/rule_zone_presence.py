import time
import cv2
import numpy as np

try:
    import python_bridge
except ImportError:
    python_bridge = None

def compute_box_metrics(boxA, boxB):
    """
    Menghitung Intersection over Union (IoU), rasio Containment boxA di dalam boxB,
    serta memeriksa apakah titik tengah boxA berada di dalam boxB.
    """
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    if interArea == 0:
        return 0.0, 0.0, False

    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    unionArea = float(boxAArea + boxBArea - interArea)
    iou = interArea / unionArea if unionArea > 0 else 0.0
    containment_a = interArea / float(boxAArea) if boxAArea > 0 else 0.0

    center_x = (boxA[0] + boxA[2]) / 2.0
    center_y = (boxA[1] + boxA[3]) / 2.0
    center_inside = (boxB[0] <= center_x <= boxB[2]) and (boxB[1] <= center_y <= boxB[3])

    return iou, containment_a, center_inside

def compute_iou(boxA, boxB):
    """Fungsi pembantu kompatibilitas mundur untuk IoU."""
    iou, _, _ = compute_box_metrics(boxA, boxB)
    return iou

class RuleZonePresence:
    def __init__(self, config: dict):
        """
        Aturan untuk memeriksa kehadiran pada zona kursi statis menggunakan ambang batas waktu.
        
        :param config: Dictionary berisi iou_threshold, enter_seconds, exit_seconds,
                       miss_tolerance_seconds, chair_zones, dll.
        """
        self.update_config(config)

        self.occupied_since  = {}   # Timestamp saat deteksi berturut-turut dimulai
        self.empty_since     = {}   # Timestamp saat zona kosong berturut-turut dimulai
        self.last_seen       = {}   # Timestamp deteksi terakhir (untuk toleransi miss)

        self.status          = {}
        self.away_start_time = {}
        self.matched_bbox    = {}
        self.frame_count     = 0

    def update_config(self, config: dict):
        self.iou_threshold   = float(config.get("iou_threshold", 0.15))

        # Ambang batas berbasis waktu (detik)
        _fallback_fps = 25.0
        self.enter_seconds = float(config.get(
            "enter_seconds",
            config.get("enter_frames", config.get("persistence_frames", 12)) / _fallback_fps
        ))
        self.exit_seconds = float(config.get(
            "exit_seconds",
            config.get("exit_frames", config.get("persistence_frames", 12)) / _fallback_fps
        ))
        # Berapa lama deteksi terputus yang ditoleransi sebelum timer di-reset
        self.miss_tolerance_seconds = float(config.get("miss_tolerance_seconds", 0.5))

        self.chair_zones = config.get("chair_zones", [])

    def reset(self):
        """Mereset semua timer dan status zona."""
        self.occupied_since.clear()
        self.empty_since.clear()
        self.last_seen.clear()
        self.status.clear()
        self.away_start_time.clear()
        self.matched_bbox.clear()
        self.frame_count = 0

    def process(self, frame, detections: list, current_time: float = None):
        """
        Mengevaluasi kehadiran untuk setiap zona kursi yang terdaftar berbasis waktu.
        
        :param frame: Citra BGR saat ini
        :param detections: List dictionary deteksi yang berisi 'upper_body_bbox'
        :param current_time: Timestamp saat ini dalam detik (default: time.time())
        :return: Dict yang memetakan zone_id ke rincian status kehadiran
        """
        if current_time is None:
            current_time = time.time()

        self.frame_count += 1
        results = {}

        # 1. Bangun semua pasangan kandidat yang valid (score, det_idx, zone_id, upper_body_bbox)
        candidate_pairs = []

        for det_idx, det in enumerate(detections):
            upper_body = det["upper_body_bbox"]
            for zone in self.chair_zones:
                zone_id    = zone["id"]
                chair_bbox = zone["bbox"]

                # Perluas toleransi pencarian (15px) untuk zona kursi yang sebagian terhalang
                expanded_chair_bbox = [
                    max(0, chair_bbox[0] - 15), max(0, chair_bbox[1] - 15),
                    chair_bbox[2] + 15,          chair_bbox[3] + 15
                ]

                iou, containment, center_inside = compute_box_metrics(upper_body, expanded_chair_bbox)
                is_match = (iou >= self.iou_threshold) or (containment >= 0.12) or (center_inside and containment >= 0.06)

                if is_match:
                    score = max(iou, containment)
                    candidate_pairs.append((score, det_idx, zone_id, upper_body))

        # 2. Greedy 1-to-1 matching: urutkan dari skor tertinggi
        candidate_pairs.sort(key=lambda x: x[0], reverse=True)

        assigned_detections = set()
        assigned_zones      = {}

        for score, det_idx, zone_id, upper_body in candidate_pairs:
            if det_idx not in assigned_detections and zone_id not in assigned_zones:
                assigned_detections.add(det_idx)
                assigned_zones[zone_id] = upper_body

        # 3. Perbarui tracker kehadiran berbasis waktu untuk setiap zona kursi
        for zone in self.chair_zones:
            zone_id    = zone["id"]
            chair_bbox = zone["bbox"]

            # Inisialisasi struktur pelacakan untuk zona baru
            if zone_id not in self.status:
                self.occupied_since[zone_id]  = None
                self.empty_since[zone_id]     = current_time
                self.last_seen[zone_id]       = None
                self.status[zone_id]          = "TIDAK_DI_TEMPAT"
                self.away_start_time[zone_id] = current_time
                self.matched_bbox[zone_id]    = None

            if zone_id in assigned_zones:
                temp_matched_bbox = assigned_zones[zone_id]
                self.last_seen[zone_id] = current_time

                # Mulai timer terisi (occupied) jika ini beruntun deteksi baru
                if self.occupied_since[zone_id] is None:
                    self.occupied_since[zone_id] = current_time

                # Reset timer kosong (empty)
                self.empty_since[zone_id] = None

            else:
                temp_matched_bbox = None

                # Periksa apakah durasi deteksi terputus melebihi toleransi
                last = self.last_seen[zone_id]
                miss_duration = (current_time - last) if last is not None else float("inf")

                if miss_duration > self.miss_tolerance_seconds:
                    # Toleransi terlampaui — reset timer beruntun terisi
                    self.occupied_since[zone_id] = None

                # Mulai timer kosong jika belum berjalan
                if self.empty_since[zone_id] is None:
                    self.empty_since[zone_id] = current_time

            # Hitung durasi untuk transisi status
            occupied_duration = (
                current_time - self.occupied_since[zone_id]
                if self.occupied_since[zone_id] is not None else 0.0
            )
            empty_duration = (
                current_time - self.empty_since[zone_id]
                if self.empty_since[zone_id] is not None else 0.0
            )

            # Transisi status berbasis waktu
            old_status = self.status[zone_id]
            if occupied_duration >= self.enter_seconds:
                self.status[zone_id]          = "BEKERJA"
                self.away_start_time[zone_id] = None
                if temp_matched_bbox is not None:
                    self.matched_bbox[zone_id] = temp_matched_bbox
                if old_status != "BEKERJA" and python_bridge:
                    python_bridge.send_incident(zone_id, "ENTER", person_count=1, duration_seconds=round(occupied_duration, 2))

            elif empty_duration >= self.exit_seconds:
                self.status[zone_id] = "TIDAK_DI_TEMPAT"
                if self.away_start_time[zone_id] is None:
                    self.away_start_time[zone_id] = current_time
                self.matched_bbox[zone_id] = None
                if old_status != "TIDAK_DI_TEMPAT" and python_bridge:
                    python_bridge.send_incident(zone_id, "EXIT", person_count=0, duration_seconds=round(empty_duration, 2))

            else:
                # Dalam transisi — pertahankan bbox terakhir jika masih bekerja
                if self.status[zone_id] == "BEKERJA" and temp_matched_bbox is not None:
                    self.matched_bbox[zone_id] = temp_matched_bbox

            away_duration = 0.0
            if self.status[zone_id] == "TIDAK_DI_TEMPAT" and self.away_start_time[zone_id] is not None:
                away_duration = max(0.0, current_time - self.away_start_time[zone_id])

            results[zone_id] = {
                "zone_id":                 zone_id,
                "chair_bbox":              chair_bbox,
                "status":                  self.status[zone_id],
                "matched_upper_body_bbox": self.matched_bbox[zone_id],
                "away_start_time":         self.away_start_time[zone_id],
                "away_duration_seconds":   away_duration,
                "occupied_duration":       occupied_duration,
                "empty_duration":          empty_duration,
            }

        # Log diagnostik setiap 30 frame
        if self.frame_count % 30 == 0:
            log_parts = []
            for zid, res in results.items():
                log_parts.append(
                    f"{zid}: occ={res['occupied_duration']:.1f}s, "
                    f"emp={res['empty_duration']:.1f}s ({res['status']})"
                )
            print(f"[TIMER Frame {self.frame_count}] " + " | ".join(log_parts))

        return results
