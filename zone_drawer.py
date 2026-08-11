import cv2
import json
import os
import sys

CONFIG_PATH = "config.json"

drawing = False
ix, iy = -1, -1
cx, cy = -1, -1
chair_zones = []

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to read {CONFIG_PATH}: {e}")
    return {
        "source": "video.mp4",
        "confidence": 0.5,
        "upper_body_ratio": 0.5,
        "iou_threshold": 0.15,
        "persistence_frames": 15,
        "chair_zones": []
    }

def save_config(config_data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config_data, f, indent=2)
    print(f"[INFO] Configuration saved to {CONFIG_PATH}")

def mouse_callback(event, x, y, flags, param):
    global ix, iy, cx, cy, drawing, chair_zones

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
        cx, cy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            cx, cy = x, y

    elif event == cv2.EVENT_LBUTTONUP:
        if drawing:
            drawing = False
            x1, y1 = min(ix, x), min(iy, y)
            x2, y2 = max(ix, x), max(iy, y)
            # Only add if box has valid width and height
            if (x2 - x1) > 10 and (y2 - y1) > 10:
                zone_id = f"chair_{len(chair_zones) + 1}"
                chair_zones.append({
                    "id": zone_id,
                    "bbox": [int(x1), int(y1), int(x2), int(y2)]
                })
                print(f"[ADDED] {zone_id}: [{x1}, {y1}, {x2}, {y2}]")
            ix, iy, cx, cy = -1, -1, -1, -1

def main():
    global chair_zones, ix, iy, cx, cy, drawing

    config = load_config()
    
    # Allow overriding video source via CLI arg
    source = sys.argv[1] if len(sys.argv) > 1 else config.get("source", "video.mp4")
    config["source"] = source

    # Try integer for webcam index, else string path
    cap_source = int(source) if str(source).isdigit() else source
    cap = cv2.VideoCapture(cap_source)

    if not cap.isOpened():
        print(f"[ERROR] Could not open video source: {source}")
        return

    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        print(f"[ERROR] Failed to read first frame from: {source}")
        return

    # Load existing chair zones if any
    chair_zones = config.get("chair_zones", [])

    window_name = "SKYNET Zone Drawer - Set Manual Chair Zones"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, mouse_callback)

    print("\n" + "="*50)
    print(" SKYNET ZONE DRAWER INSTRUCTIONS")
    print("="*50)
    print(" - Click & drag mouse to draw a chair zone box")
    print(" - Press 's' : Save chair zones to config.json & exit")
    print(" - Press 'z' : Undo last box")
    print(" - Press 'r' : Reset all boxes")
    print(" - Press 'q' / ESC : Quit without saving")
    print("="*50 + "\n")

    while True:
        display = frame.copy()

        # Draw already saved chair zones
        for zone in chair_zones:
            x1, y1, x2, y2 = zone["bbox"]
            cv2.rectangle(display, (x1, y1), (x2, y2), (255, 191, 0), 2)
            cv2.putText(display, zone["id"], (x1, max(y1 - 8, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 191, 0), 2)

        # Draw box currently being dragged
        if drawing and ix != -1 and iy != -1:
            x1, y1 = min(ix, cx), min(iy, cy)
            x2, y2 = max(ix, cx), max(iy, cy)
            cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 255), 2)
            temp_id = f"chair_{len(chair_zones) + 1}"
            cv2.putText(display, temp_id, (x1, max(y1 - 8, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # Instructions overlay bar at bottom
        h, w = display.shape[:2]
        info_text = f"Zones: {len(chair_zones)} | 's': Save & Exit | 'z': Undo | 'r': Reset | 'q': Quit"
        cv2.rectangle(display, (0, h - 35), (w, h), (30, 30, 30), -1)
        cv2.putText(display, info_text, (15, h - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

        cv2.imshow(window_name, display)
        key = cv2.waitKey(20) & 0xFF

        if key == ord('s'):
            config["chair_zones"] = chair_zones
            save_config(config)
            print(f"[SUCCESS] {len(chair_zones)} chair zones saved to {CONFIG_PATH}.")
            break
        elif key == ord('z'):
            if chair_zones:
                removed = chair_zones.pop()
                print(f"[UNDO] Removed {removed['id']}")
        elif key == ord('r'):
            chair_zones.clear()
            print("[RESET] All chair zones cleared.")
        elif key == ord('q') or key == 27:
            print("[QUIT] Exited without saving.")
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
