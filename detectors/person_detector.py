from ultralytics import YOLO
import numpy as np

class PersonDetector:
    def __init__(self, model_name: str = "yolov8n.pt", confidence: float = 0.03, upper_body_ratio: float = 0.5):
        """
        YOLOv8 Person Detector with Smart Upper-Body Cropping.
        
        :param model_name: YOLO model file (default: 'yolov8n.pt')
        :param confidence: Detection confidence threshold (default: 0.03)
        :param upper_body_ratio: Ratio of full height to crop as upper body (default: 0.5)
        """
        self.model = YOLO(model_name)
        self.confidence = float(confidence)
        self.upper_body_ratio = float(upper_body_ratio)

    def detect(self, frame):
        """
        Detects persons in the frame and crops each detection to upper-body bbox.
        
        :param frame: BGR image (numpy array)
        :return: List of dicts containing upper_body_bbox, full_body_bbox, and confidence
        """
        if frame is None:
            return []

        # Run inference filtering specifically for class 0 ('person')
        results = self.model(frame, verbose=False, conf=self.confidence, classes=[0])[0]

        detections = []
        if results.boxes is None or len(results.boxes) == 0:
            return detections

        for box in results.boxes:
            conf = float(box.conf[0].cpu().numpy())
            xyxy = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])

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
                "confidence": conf
            })

        return detections
