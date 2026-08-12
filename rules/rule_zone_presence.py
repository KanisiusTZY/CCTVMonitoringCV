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
        Rule for checking presence in static chair zones using time-based thresholds.
        
        :param config: Dictionary containing iou_threshold, enter_seconds, exit_seconds,
                       miss_tolerance_seconds, chair_zones, etc.
        """
        self.update_config(config)

        self.occupied_since  = {}   # timestamp when continuous detection streak started
        self.empty_since     = {}   # timestamp when continuous absence streak started
        self.last_seen       = {}   # timestamp of last detection (for miss tolerance)

        self.status          = {}
        self.away_start_time = {}
        self.matched_bbox    = {}
        self.frame_count     = 0

    def update_config(self, config: dict):
        self.iou_threshold   = float(config.get("iou_threshold", 0.15))

        # Time-based thresholds (seconds)
        # Fallback: if old frame-based keys still present, convert assuming 25fps
        _fallback_fps = 25.0
        self.enter_seconds = float(config.get(
            "enter_seconds",
            config.get("enter_frames", config.get("persistence_frames", 12)) / _fallback_fps
        ))
        self.exit_seconds = float(config.get(
            "exit_seconds",
            config.get("exit_frames", config.get("persistence_frames", 12)) / _fallback_fps
        ))
        # How long a missed detection is tolerated before resetting the occupied timer
        self.miss_tolerance_seconds = float(config.get("miss_tolerance_seconds", 0.5))

        self.chair_zones = config.get("chair_zones", [])

    def reset(self):
        """Resets all zone timers and statuses."""
        self.occupied_since.clear()
        self.empty_since.clear()
        self.last_seen.clear()
        self.status.clear()
        self.away_start_time.clear()
        self.matched_bbox.clear()
        self.frame_count = 0

    def process(self, frame, detections: list, current_time: float = None):
        """
        Evaluates presence for each registered chair zone using time-based thresholds.
        
        :param frame: Current BGR image frame
        :param detections: List of detection dicts containing 'upper_body_bbox'
        :param current_time: Current timestamp in seconds (default: time.time())
        :return: Dict mapping zone_id to presence status details
        """
        if current_time is None:
            current_time = time.time()

        self.frame_count += 1
        results = {}

        # 1. Build all valid candidate pairs (score, det_idx, zone_id, upper_body_bbox)
        candidate_pairs = []

        for det_idx, det in enumerate(detections):
            upper_body = det["upper_body_bbox"]
            for zone in self.chair_zones:
                zone_id    = zone["id"]
                chair_bbox = zone["bbox"]

                # Expand search tolerance slightly (15px) for occluded chair zones
                expanded_chair_bbox = [
                    max(0, chair_bbox[0] - 15), max(0, chair_bbox[1] - 15),
                    chair_bbox[2] + 15,          chair_bbox[3] + 15
                ]

                iou, containment, center_inside = compute_box_metrics(upper_body, expanded_chair_bbox)
                is_match = (iou >= self.iou_threshold) or (containment >= 0.12) or (center_inside and containment >= 0.06)

                if is_match:
                    score = max(iou, containment)
                    candidate_pairs.append((score, det_idx, zone_id, upper_body))

        # 2. Greedy 1-to-1 matching: sort by highest score first
        candidate_pairs.sort(key=lambda x: x[0], reverse=True)

        assigned_detections = set()
        assigned_zones      = {}

        for score, det_idx, zone_id, upper_body in candidate_pairs:
            if det_idx not in assigned_detections and zone_id not in assigned_zones:
                assigned_detections.add(det_idx)
                assigned_zones[zone_id] = upper_body

        # 3. Update time-based presence trackers for each chair zone
        for zone in self.chair_zones:
            zone_id    = zone["id"]
            chair_bbox = zone["bbox"]

            # Initialize tracking structures for new zones
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

                # Start occupied timer if this is a fresh detection streak
                if self.occupied_since[zone_id] is None:
                    self.occupied_since[zone_id] = current_time

                # Reset empty timer
                self.empty_since[zone_id] = None

            else:
                temp_matched_bbox = None

                # Check if miss duration exceeds tolerance
                last = self.last_seen[zone_id]
                miss_duration = (current_time - last) if last is not None else float("inf")

                if miss_duration > self.miss_tolerance_seconds:
                    # Toleration window exceeded — reset occupied streak
                    self.occupied_since[zone_id] = None

                # Start empty timer if not already running
                if self.empty_since[zone_id] is None:
                    self.empty_since[zone_id] = current_time

            # Compute durations for state transitions
            occupied_duration = (
                current_time - self.occupied_since[zone_id]
                if self.occupied_since[zone_id] is not None else 0.0
            )
            empty_duration = (
                current_time - self.empty_since[zone_id]
                if self.empty_since[zone_id] is not None else 0.0
            )

            # State transitions (time-based)
            if occupied_duration >= self.enter_seconds:
                self.status[zone_id]          = "BEKERJA"
                self.away_start_time[zone_id] = None
                if temp_matched_bbox is not None:
                    self.matched_bbox[zone_id] = temp_matched_bbox

            elif empty_duration >= self.exit_seconds:
                self.status[zone_id] = "TIDAK_DI_TEMPAT"
                if self.away_start_time[zone_id] is None:
                    self.away_start_time[zone_id] = current_time
                self.matched_bbox[zone_id] = None

            else:
                # In transition — keep last known bbox if still working
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

        # Diagnostic log every 30 frames
        if self.frame_count % 30 == 0:
            log_parts = []
            for zid, res in results.items():
                log_parts.append(
                    f"{zid}: occ={res['occupied_duration']:.1f}s, "
                    f"emp={res['empty_duration']:.1f}s ({res['status']})"
                )
            print(f"[TIMERS Frame {self.frame_count}] " + " | ".join(log_parts))

        return results
