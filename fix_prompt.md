# Context & Fix Instructions for Auto_Trash track_ball.py

## Project
GitHub: https://github.com/amharies/Auto_Trash
A self-moving trash can that uses two cameras + YOLOv8 to track thrown trash mid-air,
predict landing position, and drive a mecanum wheel robot to catch it.

## Our Setup
- OS: Windows
- Two cameras (laptop webcam + external USB webcam)
- Running track_ball.py twice (once per camera with -v 0 and -v 1)
- continue_plot.py reads target_0 and target_1 files and plots 3D trajectory
- Python + YOLOv8 + OpenCV stack

## Current Problems
1. Scattered/noisy dots in the 3D plot — no clean arc
2. FPS fluctuating between 25–50 (should be 50+)
3. Too many false detections (clothes, hangers in background)
4. Coordinate smoothing missing — raw bounding box center written directly to file
5. FPS calculation is wrong — timer.reset() called twice incorrectly
6. Writing to TWO files per camera (target_0 AND target_0.txt) — redundant

## File Structure
- track_ball.py — camera loop + YOLO detection + writes coordinates to target files
- continue_plot.py — reads target files, does 3D trigonometry, predicts landing spot
- timer.py — simple timer utility class
- color.py — color constants for OpenCV drawing
- target_0, target_1 — files written by track_ball.py, read by continue_plot.py
- yolov8_model/weights/best.pt — trained YOLOv8 model (47 epochs, 14256 images)
- robot_control.ino — Teensy 4.0 Arduino code for stepper motors

## Exact Fixes Needed in track_ball.py

### Fix 1: Add confidence threshold to model.predict()
Currently:
```python
results = model.predict(frame, device=0, verbose=False, augment=False, imgsz=320)
```
Change to:
```python
results = model.predict(frame, device=0, verbose=False, augment=False, imgsz=320, conf=0.5)
```
Why: Without conf threshold, it detects anything including background clutter.
Tune: If ball is missed too often, lower to 0.4. If too many false detections, raise to 0.6.

### Fix 2: Change buffer size from 2 to 1
Currently:
```python
vid.set(cv2.CAP_PROP_BUFFERSIZE, 2)
```
Change to:
```python
vid.set(cv2.CAP_PROP_BUFFERSIZE, 1)
```
Why: Smaller buffer = less lag = more consistent FPS on Windows.

### Fix 3: Fix FPS calculation (timer reset called twice)
Currently in track():
```python
self.timer.reset()          # reset at start
data = self.find_ball(...)
...
elapsed = self.timer.elapsed()
fps = 1/np.round(elapsed, 3)
self.timer.reset()          # reset again immediately after — wrong!
```
Fix — remove the first reset, only reset after elapsed:
```python
# Do NOT reset at start of track()
data = self.find_ball(...)
...
elapsed = self.timer.elapsed()
fps = 1/np.round(elapsed, 3)
self.timer.reset()          # only reset here
```

### Fix 4: Add coordinate smoothing using deque
Add at top of file (after imports):
```python
from collections import deque
SMOOTH_N = 4
smooth_x = deque(maxlen=SMOOTH_N)
smooth_y = deque(maxlen=SMOOTH_N)
```

Add as instance variables in __init__ (after self.last_target = None):
```python
self.smooth_x = deque(maxlen=SMOOTH_N)
self.smooth_y = deque(maxlen=SMOOTH_N)
```

In track(), where ball is detected, replace raw center write with smoothed:
```python
center_x, center_y = int((target[0]+target[2])/2), int((target[1]+target[3])/2)

# Add to smoothing buffer
self.smooth_x.append(center_x)
self.smooth_y.append(center_y)

# Use smoothed average
smooth_cx = int(np.mean(self.smooth_x))
smooth_cy = int(np.mean(self.smooth_y))

# Write smoothed coords to file (only .txt version)
with open(f"target_{args['video']}.txt", "w") as f:
    f.write(f"{smooth_cx} {smooth_cy}")
```

### Fix 5: Remove duplicate file write in draw_target()
Currently draw_target() also writes to target_{video} (no extension).
This is a duplicate. Either:
- Remove the write from draw_target() entirely (track() already handles it)
- OR keep draw_target() write-free and just use it for drawing

### Fix 6: Pick ONE filename format and stick to it
The repo uses target_0 and target_1 (no extension).
But the code also writes target_0.txt and target_1.txt.
Check what continue_plot.py reads — match that exact filename.
If continue_plot.py reads "target_0" (no extension), write to that.
If it reads "target_0.txt", write to that. Remove the other.

## What NOT to change
- Do not change imgsz=320 (lower = faster inference, good for real-time)
- Do not change device=0 (GPU acceleration)
- Do not change frame dimensions (640x360 is fine)
- Do not touch timer.py, color.py, continue_plot.py, or robot_control.ino
- The file ends with Tracker() under if __name__ == "__main__": — keep that

## Priority Order
1. Fix confidence threshold (biggest impact on scatter)
2. Fix buffer size (FPS stability)
3. Fix FPS calculation (accuracy)
4. Add smoothing (cleaner arc)
5. Clean up duplicate file writes
