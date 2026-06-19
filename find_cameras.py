import cv2

names = ["icspring camera", "icspring camera (2)", "icspring camera 2"]
for name in names:
    cap = cv2.VideoCapture(f"video={name}", cv2.CAP_DSHOW)
    if cap.isOpened():
        ret, _ = cap.read()
        status = "OK" if ret else "no frame"
        print(f"{name}: {status}")
        cap.release()
    else:
        print(f"{name}: not found")
