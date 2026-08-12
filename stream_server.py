import cv2
import time
import threading
from flask import Flask, Response

app = Flask(__name__)

latest_frame_bytes = None
lock = threading.Lock()

import numpy as np

def get_placeholder_frame():
    img = np.zeros((480, 854, 3), dtype=np.uint8)
    cv2.putText(img, "YOLOv8 AI Stream Initializing...", (180, 240),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (56, 189, 248), 2)
    ret, jpeg = cv2.imencode('.jpg', img)
    return jpeg.tobytes() if ret else b''

def set_latest_frame(frame):
    global latest_frame_bytes
    if frame is None:
        return
    # Fast resize stream payload for zero-lag remote tunneling
    h, w = frame.shape[:2]
    if w > 720:
        new_w = 720
        new_h = int(h * (720 / w))
        stream_frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
    else:
        stream_frame = frame

    ret, jpeg = cv2.imencode('.jpg', stream_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 65])
    if ret:
        with lock:
            latest_frame_bytes = jpeg.tobytes()

def generate_stream():
    global latest_frame_bytes
    while True:
        with lock:
            frame = latest_frame_bytes
        
        if frame is None:
            frame = get_placeholder_frame()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        time.sleep(0.015)  # Fast push

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
    return {"status": "running", "streaming": True}

import sys
import subprocess
import re

def auto_start_tunnel(port=5000):
    try:
        import google.colab
        is_colab = True
    except ImportError:
        is_colab = False

    if is_colab or sys.platform.startswith("linux"):
        try:
            subprocess.run(["cloudflared", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            try:
                subprocess.run("wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb && dpkg -i cloudflared-linux-amd64.deb", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

        try:
            proc = subprocess.Popen(
                ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            public_url = None
            for _ in range(25):
                line = proc.stderr.readline()
                if "trycloudflare.com" in line:
                    match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                    if match:
                        public_url = match.group(0)
                        break
                time.sleep(0.3)
            
            if public_url:
                print("\n" + "="*70)
                print(" CLOUDFLARE PUBLIC LIVE STREAM URL (100% AKTIF):")
                print(f"    {public_url}/video_feed")
                print("="*70 + "\n")
        except Exception:
            pass

def start_server(host='0.0.0.0', port=5000):
    t = threading.Thread(
        target=lambda: app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True),
        daemon=True
    )
    t.start()
    print(f"[INFO] MJPEG Live Stream Server berjalan di http://localhost:{port}/video_feed")
    auto_start_tunnel(port=port)
