import cv2
import numpy as np

class Visualizer:
    def __init__(self):
        self.color_bekerja  = (0, 220, 80)      # BGR Green
        self.color_away     = (0, 60, 220)       # BGR Red
        self.color_waiting  = (0, 180, 255)      # BGR Orange (occ naik tapi belum BEKERJA)
        self.font           = cv2.FONT_HERSHEY_SIMPLEX

    def format_duration(self, seconds: float) -> str:
        """Formats duration in seconds into 'XmYYs' format."""
        total_sec = int(max(0, seconds))
        mins  = total_sec // 60
        secs  = total_sec % 60
        return f"{mins}m{secs:02d}s"

    def _draw_label(self, img, text, pos, font_scale=0.48, color=(255,255,255), bg_color=(30,30,30), thickness=1):
        """Draw text with a dark background pill for readability."""
        (tw, th), baseline = cv2.getTextSize(text, self.font, font_scale, thickness)
        x, y = pos
        pad = 4
        cv2.rectangle(img, (x - pad, y - th - pad), (x + tw + pad, y + baseline + pad), bg_color, -1)
        cv2.putText(img, text, (x, y), self.font, font_scale, color, thickness, cv2.LINE_AA)

    def render(self, frame, presence_results: dict, fps: float = 0.0):
        """
        Renders presence monitoring visualization with labels on each box.
        
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
        total_tidak   = 0

        for zone_id, res in presence_results.items():
            status        = res["status"]
            chair_bbox    = res["chair_bbox"]
            matched_bbox  = res["matched_upper_body_bbox"]
            away_duration = res["away_duration_seconds"]
            occ_dur       = res.get("occupied_duration", 0.0)
            emp_dur       = res.get("empty_duration", 0.0)

            # Pilih warna & box berdasarkan status
            if status == "BEKERJA":
                total_bekerja += 1
                draw_box = matched_bbox if matched_bbox is not None else chair_bbox
                color    = self.color_bekerja
            elif occ_dur > 0:
                # Sedang akumulasi — belum resmi BEKERJA
                total_tidak += 1
                draw_box = matched_bbox if matched_bbox is not None else chair_bbox
                color    = self.color_waiting
            else:
                total_tidak += 1
                draw_box = chair_bbox
                color    = self.color_away

            x1, y1, x2, y2 = draw_box

            # Gambar kotak utama (2px)
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)

        # --- Top info bar ---
        bar_h = 44
        cv2.rectangle(output, (0, 0), (w, bar_h), (18, 18, 18), -1)

        cv2.putText(output, "Presence Monitoring",
                    (14, 28), self.font, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

        bekerja_text = f"BEKERJA: {total_bekerja}"
        tidak_text   = f"TIDAK DI TEMPAT: {total_tidak}"
        fps_text     = f"FPS: {fps:.1f}"

        cv2.putText(output, bekerja_text,
                    (w - 450, 28), self.font, 0.55, self.color_bekerja, 1, cv2.LINE_AA)
        cv2.putText(output, tidak_text,
                    (w - 280, 28), self.font, 0.55, self.color_away, 1, cv2.LINE_AA)
        cv2.putText(output, fps_text,
                    (w - 90, 28), self.font, 0.5, (180, 180, 180), 1, cv2.LINE_AA)

        return output
