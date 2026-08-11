import time
import cv2
import numpy as np

def compute_box_metrics(boxA, boxB):
    """
    Computes Intersection over Union (IoU), Containment ratio of boxA in boxB,
    and checks if center of boxA is inside boxB.
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
    """Backward compatibility helper for IoU."""
    iou, _, _ = compute_box_metrics(boxA, boxB)
    return iou

class RuleZonePresence:
    def __init__(self, config: dict):
        """
        Rule for checking presence in static chair zones based on upper-body detections.
        
        :param config: Dictionary containing iou_threshold, persistence_frames, chair_zones, etc.
        """
        self.update_config(config)

        self.occupied_counter = {}
        self.empty_counter = {}
        self.status = {}
        self.away_start_time = {}
        self.matched_bbox = {}
        self.frame_count = 0

    def update_config(self, config: dict):
        self.iou_threshold = float(config.get("iou_threshold", 0.15))
        self.persistence_frames = int(config.get("persistence_frames", 12))
        self.chair_zones = config.get("chair_zones", [])

    def reset(self):
        """Resets all zone counters, statuses, and away timers."""
        self.occupied_counter.clear()
        self.empty_counter.clear()
        self.status.clear()
        self.away_start_time.clear()
        self.matched_bbox.clear()
        self.frame_count = 0

    def process(self, frame, detections: list, current_time: float = None):
        """
        Evaluates presence for each registered chair zone using 1-to-1 greedy matching.
        
        :param frame: Current BGR image frame
        :param detections: List of detection dicts containing 'upper_body_bbox'
        :param current_time: Current timestamp in seconds (default: time.time())
        :return: Dict mapping zone_id to presence status details
        """
        if current_time is None:
            current_time = time.time()

        self.frame_count += 1
        results = {}

        # 1. Build all valid candidate pairs (match_score, det_idx, zone_id, upper_body_bbox)
        candidate_pairs = []

        for det_idx, det in enumerate(detections):
            upper_body = det["upper_body_bbox"]
            for zone in self.chair_zones:
                zone_id = zone["id"]
                chair_bbox = zone["bbox"]
                
                # Expand search tolerance slightly (15px) for occluded chair zones
                expanded_chair_bbox = [max(0, chair_bbox[0] - 15), max(0, chair_bbox[1] - 15), chair_bbox[2] + 15, chair_bbox[3] + 15]

                iou, containment, center_inside = compute_box_metrics(upper_body, expanded_chair_bbox)
                is_match = (iou >= self.iou_threshold) or (containment >= 0.12) or (center_inside and containment >= 0.06)

                if is_match:
                    score = max(iou, containment)
                    candidate_pairs.append((score, det_idx, zone_id, upper_body))

        # 2. Greedy 1-to-1 matching: sort candidate pairs by highest score first
        candidate_pairs.sort(key=lambda x: x[0], reverse=True)

        assigned_detections = set()
        assigned_zones = {}

        for score, det_idx, zone_id, upper_body in candidate_pairs:
            if det_idx not in assigned_detections and zone_id not in assigned_zones:
                assigned_detections.add(det_idx)
                assigned_zones[zone_id] = upper_body

        # 3. Update presence statuses for each chair zone
        for zone in self.chair_zones:
            zone_id = zone["id"]
            chair_bbox = zone["bbox"]

            # Initialize tracking structures for new zones
            if zone_id not in self.occupied_counter:
                self.occupied_counter[zone_id] = 0
                self.empty_counter[zone_id] = 0
                self.status[zone_id] = "TIDAK_DI_TEMPAT"
                self.away_start_time[zone_id] = current_time
                self.matched_bbox[zone_id] = None

            if zone_id in assigned_zones:
                self.occupied_counter[zone_id] += 1
                self.empty_counter[zone_id] = 0
                temp_matched_bbox = assigned_zones[zone_id]
            else:
                self.empty_counter[zone_id] += 1
                # Reset occupied_counter only after 10 consecutive missed frames
                if self.empty_counter[zone_id] >= 10:
                    self.occupied_counter[zone_id] = 0
                temp_matched_bbox = None

            # State transitions
            if self.occupied_counter[zone_id] >= self.persistence_frames:
                self.status[zone_id] = "BEKERJA"
                self.away_start_time[zone_id] = None
                self.matched_bbox[zone_id] = temp_matched_bbox
            elif self.empty_counter[zone_id] >= self.persistence_frames:
                self.status[zone_id] = "TIDAK_DI_TEMPAT"
                if self.away_start_time[zone_id] is None:
                    self.away_start_time[zone_id] = current_time
                self.matched_bbox[zone_id] = None
            else:
                if self.status[zone_id] == "BEKERJA" and temp_matched_bbox is not None:
                    self.matched_bbox[zone_id] = temp_matched_bbox

            away_duration = 0.0
            if self.status[zone_id] == "TIDAK_DI_TEMPAT" and self.away_start_time[zone_id] is not None:
                away_duration = max(0.0, current_time - self.away_start_time[zone_id])

            results[zone_id] = {
                "zone_id": zone_id,
                "chair_bbox": chair_bbox,
                "status": self.status[zone_id],
                "matched_upper_body_bbox": self.matched_bbox[zone_id],
                "away_start_time": self.away_start_time[zone_id],
                "away_duration_seconds": away_duration,
                "occupied_counter": self.occupied_counter[zone_id],
                "empty_counter": self.empty_counter[zone_id]
            }

        # Print counter diagnostic log every 30 frames
        if self.frame_count % 30 == 0:
            log_parts = []
            for zid, res in results.items():
                log_parts.append(f"{zid}: occ={res['occupied_counter']}, emp={res['empty_counter']} ({res['status']})")
            print(f"[COUNTERS Frame {self.frame_count}] " + " | ".join(log_parts))

        return results
