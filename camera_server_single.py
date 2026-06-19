"""
Run one instance per camera on Windows.

Usage:
  python camera_server_single.py --index 0 --port 8080 --name side
  python camera_server_single.py --index 1 --port 8081 --name wrist
"""

import argparse
import cv2
import time
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


latest_frame = None
frame_lock = threading.Lock()
cam_name = "camera"


def capture_loop(cam_index: int):
    for backend in (cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY):
        cap = cv2.VideoCapture(cam_index, backend)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                break
        cap.release()

    if not cap.isOpened():
        print(f"ERROR: Could not open camera index {cam_index}")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    print(f"Camera {cam_index} ({cam_name}) opened.")

    global latest_frame
    while True:
        ret, frame = cap.read()
        if ret:
            _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            with frame_lock:
                latest_frame = jpeg.tobytes()
        else:
            time.sleep(0.01)


class MJPEGHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/video":
            self._serve_mjpeg()
        elif self.path == "/snapshot":
            self._serve_snapshot()
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_snapshot(self):
        deadline = time.time() + 3.0
        data = None
        while time.time() < deadline:
            with frame_lock:
                data = latest_frame
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

    def _serve_mjpeg(self):
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace;boundary=jpgboundary")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        print(f"Client connected to {cam_name}")
        try:
            while True:
                with frame_lock:
                    data = latest_frame
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
            print(f"Client disconnected from {cam_name}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=int, required=True, help="Camera index")
    parser.add_argument("--port", type=int, required=True, help="HTTP port")
    parser.add_argument("--name", type=str, default="camera", help="Camera name")
    args = parser.parse_args()

    cam_name = args.name

    t = threading.Thread(target=capture_loop, args=(args.index,), daemon=True)
    t.start()

    print("Waiting for camera to warm up...")
    deadline = time.time() + 10
    while time.time() < deadline:
        with frame_lock:
            ready = latest_frame is not None
        if ready:
            break
        time.sleep(0.1)

    if latest_frame is None:
        print(f"ERROR: Camera {args.index} did not produce frames. Exiting.")
        exit(1)

    hostname = socket.gethostbyname(socket.gethostname())
    server = ThreadedHTTPServer(("0.0.0.0", args.port), MJPEGHandler)
    print(f"{cam_name} ready: http://{hostname}:{args.port}/video")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopped.")
