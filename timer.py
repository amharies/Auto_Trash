from time import time

# Helper class to time code execution speed
# Useful for calculating FPS or performance metrics


class Timer():
    def __init__(self):
        # Record the current time when instantiated
        self.start_time = time()

    def reset(self):
        # Reset the timer to the current time
        self.start_time = time()

    def elapsed(self):
        # Calculate the time elapsed since the start or last reset
        return time() - self.start_time
