import cv2
import time
import threading
from flask import Flask, Response

app = Flask(__name__)

latest_frame_bytes = None
lock = threading.Lock()

def set_latest_frame(frame):
    global latest_frame_bytes
    if frame is None:
        return
    ret, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    if ret:
        with lock:
            latest_frame_bytes = jpeg.tobytes()

def generate_stream():
    global latest_frame_bytes
    while True:
        with lock:
            frame = latest_frame_bytes
        
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        time.sleep(0.04)  # ~25 FPS

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

@app.route('/video_feed')
def video_feed():
    resp = Response(generate_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/status')
def status():
    return {"status": "running", "streaming": latest_frame_bytes is not None}

def start_server(host='0.0.0.0', port=5000):
    t = threading.Thread(
        target=lambda: app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True),
        daemon=True
    )
    t.start()
    print(f"[INFO] MJPEG Live Stream Server berjalan di http://localhost:{port}/video_feed")
