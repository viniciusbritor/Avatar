import cv2
import os

path = "/workspace/lana_base.avi"
print(f"Checking {path}...")
print(f"Exists: {os.path.exists(path)}")

cap = cv2.VideoCapture(path)
is_opened = cap.isOpened()
print(f"DIAGNOSTICO_OPENCV: {is_opened}")

if is_opened:
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"FPS: {fps}")
    
cap.release()
