from ultralytics import YOLO
import numpy as np

class PersonDetector:
    def __init__(self, model_name: str = "yolov8m.pt", confidence: float = 0.1, upper_body_ratio: float = 0.5):
        """
        Pendeteksi Personel YOLOv8 dengan Pemotongan Tubuh Bagian Atas (Upper-Body) & Pelacak ByteTrack.
        
        :param model_name: File bobot model YOLO (default: 'yolov8m.pt')
        :param confidence: Ambang batas keyakinan deteksi (default: 0.1)
        :param upper_body_ratio: Rasio tinggi tubuh yang dipotong sebagai tubuh bagian atas (default: 0.5)
        """
        self.model = YOLO(model_name)
        self.confidence = float(confidence)
        self.upper_body_ratio = float(upper_body_ratio)

    def detect(self, frame):
        """
        Mendeteksi dan melacak personel dalam frame menggunakan ByteTrack, kemudian
        memotong setiap deteksi ke koordinat bounding box tubuh bagian atas.
        
        :param frame: Citra BGR (numpy array)
        :return: List berisi dictionary (upper_body_bbox, full_body_bbox, confidence, track_id)
        """
        if frame is None:
            return []

        import torch
        device = 0 if torch.cuda.is_available() else 'cpu'

        # Jalankan inferensi dengan pelacak ByteTrack ber-GPU untuk performa maksimal
        results = self.model.track(
            frame,
            verbose=False,
            conf=self.confidence,
            classes=[0],          # Khusus kelas 0 ('person')
            tracker="bytetrack.yaml",
            persist=True,         # Pertahankan status pelacakan antar frame
            device=device
        )[0]

        detections = []
        if results.boxes is None or len(results.boxes) == 0:
            return detections

        for box in results.boxes:
            conf = float(box.conf[0].cpu().numpy())
            xyxy = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])

            # Ambil ID pelacakan jika tersedia
            track_id = int(box.id[0].cpu().numpy()) if box.id is not None else None

            full_body_bbox = [int(x1), int(y1), int(x2), int(y2)]

            height = y2 - y1
            width = x2 - x1
            aspect_ratio = height / float(width) if width > 0 else 2.0

            if aspect_ratio > 1.2:
                y2_upper = y1 + (height * self.upper_body_ratio)
            else:
                y2_upper = y2

            upper_body_bbox = [int(x1), int(y1), int(x2), int(y2_upper)]

            detections.append({
                "upper_body_bbox": upper_body_bbox,
                "full_body_bbox": full_body_bbox,
                "confidence": conf,
                "track_id": track_id,
            })

        return detections
