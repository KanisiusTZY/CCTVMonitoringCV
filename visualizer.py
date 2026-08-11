import cv2
import numpy as np

class Visualizer:
    def __init__(self):
        self.color_bekerja = (0, 255, 0)      # BGR Green
        self.color_away = (0, 0, 255)         # BGR Red
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.55
        self.thickness = 2

    def format_duration(self, seconds: float) -> str:
        """Formats duration in seconds into 'XmYYs' format."""
        total_sec = int(max(0, seconds))
        mins = total_sec // 60
        secs = total_sec % 60
        return f"{mins}m{secs:02d}s"

    def render(self, frame, presence_results: dict, fps: float = 0.0):
        """
        Renders presence monitoring visualization using clean static workstation boxes.
        Guaranteeing zero double-boxes or overlapping detection rectangles.
        
        :param frame: Input BGR image frame
        :param presence_results: Dict output from RuleZonePresence
        :param fps: Current FPS
        :return: Annotated BGR frame
        """
        if frame is None:
            return frame

        output = frame.copy()
        h, w = output.shape[:2]

        total_bekerja = 0
        total_tidak_di_tempat = 0

        # Draw static locked chair zone box for each workstation (GREEN = BEKERJA, RED = TIDAK DI TEMPAT)
        for zone_id, res in presence_results.items():
            status = res["status"]
            chair_bbox = res["chair_bbox"]

            if status == "BEKERJA":
                total_bekerja += 1
                color = self.color_bekerja
            else:
                total_tidak_di_tempat += 1
                color = self.color_away

            x1, y1, x2, y2 = chair_bbox
            # Draw single clean 2px outline box per workstation
            cv2.rectangle(output, (x1, y1), (x2, y2), color, self.thickness)

        # Render top info bar showing summary counts and FPS
        bar_height = 42
        cv2.rectangle(output, (0, 0), (w, bar_height), (20, 20, 20), -1)

        info_bekerja = f"BEKERJA: {total_bekerja}"
        info_away = f"TIDAK DI TEMPAT: {total_tidak_di_tempat}"
        info_fps = f"FPS: {fps:.1f}"

        cv2.putText(output, "SKYNET Simple Presence Monitoring", (15, 26),
                    self.font, 0.6, (255, 255, 255), 2, cv2.LINE_AA)

        cv2.putText(output, info_bekerja, (max(15, w - 450), 26),
                    self.font, 0.55, self.color_bekerja, 2, cv2.LINE_AA)

        cv2.putText(output, info_away, (max(15, w - 280), 26),
                    self.font, 0.55, self.color_away, 2, cv2.LINE_AA)

        cv2.putText(output, info_fps, (max(15, w - 90), 26),
                    self.font, 0.55, (200, 200, 200), 1, cv2.LINE_AA)

        return output
