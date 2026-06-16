"""
Run this on WINDOWS (not WSL2) to stream USB cameras over HTTP.
Usage: python camera_server.py

Endpoints:
  http://172.31.192.1:8080/video0    -> Camera 0 (follower robot camera)
  http://172.31.192.1:8080/video1    -> Camera 1 (standalone camera)
  http://172.31.192.1:8080/snapshot0 -> Single frame from camera 0
  http://172.31.192.1:8080/snapshot1 -> Single frame from camera 1
"""

import cv2
import time
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

# DEBUG
# for i in range(10):
#     cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
#     if cap.isOpened():
#         ret, frame = cap.read()
#         print(f"Camera index {i}: opened, frame={ret}")
#     else:
#         print(f"Camera index {i}: not available")
#     cap.release()

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handles each request in a separate thread."""
    daemon_threads = True


CAMERAS = {
    1: {"index": 0, "name": "standalone"},
}
PORT = 8080

# Shared state per camera
latest_frames = {k: None for k in CAMERAS}
frame_locks = {k: threading.Lock() for k in CAMERAS}


def camera_capture_loop(cam_id: int, cam_index: int):
    cap = cv2.VideoCapture(cam_index, cv2.CAP_MSMF)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print(f"ERROR: Could not open camera index {cam_index}")
        return

    print(f"Camera {cam_index} ({CAMERAS[cam_id]['name']}) opened.")
    while True:
        ret, frame = cap.read()
        if ret:
            _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            with frame_locks[cam_id]:
                latest_frames[cam_id] = jpeg.tobytes()
        else:
            time.sleep(0.01)


class MJPEGHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/video0":
            self._serve_mjpeg(0)
        elif self.path == "/video1":
            self._serve_mjpeg(1)
        elif self.path == "/snapshot0":
            self._serve_snapshot(0)
        elif self.path == "/snapshot1":
            self._serve_snapshot(1)
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_snapshot(self, cam_id: int):
        deadline = time.time() + 3.0
        data = None
        while time.time() < deadline:
            with frame_locks[cam_id]:
                data = latest_frames[cam_id]
            if data:
                break
            time.sleep(0.05)

        if not data:
            self.send_response(503)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _serve_mjpeg(self, cam_id: int):
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace;boundary=jpgboundary")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Pragma", "no-cache")
        self.end_headers()

        print(f"Client connected — streaming camera {cam_id} ({CAMERAS[cam_id]['name']})")
        try:
            while True:
                with frame_locks[cam_id]:
                    data = latest_frames[cam_id]

                if data is None:
                    time.sleep(0.01)
                    continue

                self.wfile.write(b"--jpgboundary\r\n")
                self.wfile.write(b"Content-Type: image/jpeg\r\n")
                self.wfile.write(f"Content-Length: {len(data)}\r\n\r\n".encode())
                self.wfile.write(data)
                self.wfile.write(b"\r\n")
                self.wfile.flush()
                time.sleep(1 / 30)

        except (BrokenPipeError, ConnectionResetError, OSError):
            print(f"Client disconnected from camera {cam_id}.")


if __name__ == "__main__":
    # Start capture threads for all cameras
    for cam_id, info in CAMERAS.items():
        t = threading.Thread(
        target=camera_capture_loop,
        args=(cam_id, info["index"]),
        daemon=True
    )
    t.start()
    time.sleep(1.5)  # IMPORTANT: let Windows initialize one camera before opening the next

    # Wait for all cameras to produce first frame
    print("Waiting for cameras to warm up...")
    deadline = time.time() + 10
    while time.time() < deadline:
        if all(latest_frames[i] is not None for i in CAMERAS):
            break
        time.sleep(0.1)

    ready = [i for i in CAMERAS if latest_frames[i] is not None]
    not_ready = [i for i in CAMERAS if latest_frames[i] is None]
    if not_ready:
        print(f"WARNING: Camera(s) {not_ready} did not produce frames.")
    if not ready:
        print("ERROR: No cameras ready. Exiting.")
        exit(1)

    hostname = socket.gethostbyname(socket.gethostname())
    server = ThreadedHTTPServer(("0.0.0.0", PORT), MJPEGHandler)
    print(f"Camera server ready!")
    for cam_id in ready:
        print(f"  Camera {cam_id} ({CAMERAS[cam_id]['name']}): http://{hostname}:{PORT}/video{cam_id}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopped.")
