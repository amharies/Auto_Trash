import argparse
import cv2
import numpy as np
from collections import deque
from dotenv import load_dotenv
from timer import Timer
from ultralytics import YOLO
from color import Color

# Load environment variables from .env file if it exists
load_dotenv()

# Initialize the YOLO model with the specified weights
# This model will be used for object detection
model = YOLO("yolov8_model/weights/best.pt")

# Set up argument parsing to accept command line arguments
arg_parser = argparse.ArgumentParser()
# Add a 'video' argument which can be an integer (for webcam) or string
arg_parser.add_argument("-v", "--video", required=True,
                        help="{int} for webcam")
# Parse the arguments into a dictionary
args = vars(arg_parser.parse_args())

# Number of frames to average for coordinate smoothing
SMOOTH_N = 4


class Tracker():
    # Tracker class responsible for handling video input,
    # detecting the ball, and tracking its position.
    def find_ball(self, frame):
    # Detects the ball in the given frame using the YOLO model.
    # Returns the bounding boxes of detected objects.
        # conf=0.5 filters out background clutter — lower to 0.4 if ball is missed too often
        results = model.predict(frame, device=0,
                                verbose=False, augment=False, imgsz=320, conf=0.5)
        # Return the boxes from the first result (assuming single image/frame)
        return results[0].boxes

    def setup_camera(self, num):
    # Initializes the video capture object with specific settings.
    # Sets buffer size and frame dimensions.
        vid = cv2.VideoCapture(num)
        vid.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # buffer=1 reduces lag on Windows
        vid.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
        return vid

    def draw_target(self, target, smooth_cx, smooth_cy):
    # Draws the bounding box and smoothed center point of the detected target.
    # File writing is handled in track() — this method is draw-only.
        (x, y, x2, y2) = target
        draw_on = self.frame

        # Draw a rectangle around the target
        cv2.rectangle(draw_on, (x, y), (x2, y2), Color.GREEN, 2)
        # Draw a red circle at the smoothed center of the target
        cv2.circle(draw_on, (smooth_cx, smooth_cy), 5, Color.RED, -1)

        # If a previous target exists, draw a line between the last and current position
        if self.last_target is not None:
            (last_x, last_y, last_x2, last_y2) = self.last_target
            last_center_x, last_center_y = int(
                (last_x+last_x2)/2), int((last_y+last_y2)/2)
            # Draw the path
            cv2.circle(draw_on, (smooth_cx, smooth_cy), 5, Color.BLUE, -1)
            cv2.line(draw_on, (last_center_x, last_center_y),
                     (smooth_cx, smooth_cy), Color.BLUE, 2)

    def track(self):
    # Main tracking loop for a single frame.
    # Detects ball, updates files, and calculates FPS.
        # Find the ball in the current frame
        data = self.find_ball(self.frame)
        # Convert bounding boxes to integer list
        bboxes = np.array(data.xyxy.cpu(), dtype="int").tolist()

        # If a ball is detected
        if len(bboxes) > 0:
            target = bboxes[0]
            self.last_target = target

            # Raw center of bounding box
            center_x, center_y = int(
                (target[0]+target[2])/2), int((target[1]+target[3])/2)

            # Add to smoothing buffer and compute smoothed average
            self.smooth_x.append(center_x)
            self.smooth_y.append(center_y)
            smooth_cx = int(np.mean(self.smooth_x))
            smooth_cy = int(np.mean(self.smooth_y))

            print(f"({smooth_cx}, {smooth_cy})")

            # Draw visual indicators using smoothed coords
            self.draw_target(target, smooth_cx, smooth_cy)

            # Write smoothed coordinates to file (read by continue_plot.py)
            with open(f"target_{args['video']}", "w") as f:
                f.write(f"{smooth_cx} {smooth_cy}")
        else:
            # If no ball is found, write that status to the file
            with open(f"target_{args['video']}", "w") as f:
                f.write("no ball found")

        # Calculate frames per second (FPS)
        # NOTE: timer is reset AFTER elapsed() — only one reset per cycle
        elapsed = self.timer.elapsed()
        fps = 1 / np.round(elapsed, 3)
        self.timer.reset()

        # Display FPS on the frame
        cv2.putText(self.frame, f"FPS: {fps}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, Color.RED, 2)

    def __init__(self):
    # Initialize the Tracker instance.
    # Sets up the camera and starts the main loop.
        self.timer = Timer()

        # Coordinate smoothing buffers
        self.smooth_x = deque(maxlen=SMOOTH_N)
        self.smooth_y = deque(maxlen=SMOOTH_N)

        # Determine if input is a camera index (int) or video path (str)
        url = None
        try:
            url = int(args["video"])
        except:
            url = args["video"]

        # Setup the camera
        self.vid = self.setup_camera(url)

        self.last_target = None

        print("Started!!")

        # Read the first frame
        self.ret, self.frame = self.vid.read()

        # Start the timer before the loop — only reset inside track() after elapsed()
        self.timer.reset()

        # specific loop to keep reading frames
        while self.ret:
            self.track()
            # Quit if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            # Show the frame in a window
            cv2.imshow('Frame', self.frame)
            # Read the next frame
            self.ret, self.frame = self.vid.read()

        # Cleanup resources
        self.vid.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    # Create an instance of the Tracker class to start the program
    Tracker()
