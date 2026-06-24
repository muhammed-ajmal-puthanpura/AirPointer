# ============================================================
# camera.py
# Air Pointer Project
# Handles webcam capture using OpenCV
# ============================================================

import cv2
import os


class CameraFeed:
    def __init__(self, camera_index=0, width=1280, height=720, fps=30, mirror=True):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps
        self.mirror = mirror
        self.cap = None

    def start(self):
        """
        Start the camera feed.
        """

        # CAP_DSHOW helps reduce camera startup delay on Windows
        if os.name == "nt":
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            raise RuntimeError(
                f"Could not open camera with index {self.camera_index}. "
                "Try changing camera_index to 1 or 2."
            )

        # Set camera resolution and FPS
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        print("Camera started successfully.")
        print(f"Camera index: {self.camera_index}")
        print(f"Requested resolution: {self.width} x {self.height}")
        print(f"Requested FPS: {self.fps}")

        return self

    def read(self):
        """
        Read one frame from camera.
        Returns:
            success: True/False
            frame: image frame
        """

        if self.cap is None:
            raise RuntimeError("Camera has not been started. Call start() first.")

        success, frame = self.cap.read()

        if not success:
            return False, None

        # Mirror camera feed for natural hand movement
        if self.mirror:
            frame = cv2.flip(frame, 1)

        return True, frame

    def release(self):
        """
        Release camera resources.
        """

        if self.cap is not None:
            self.cap.release()
            self.cap = None
            print("Camera released.")

    def get_actual_resolution(self):
        """
        Get actual camera resolution.
        """

        if self.cap is None:
            return None, None

        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        return width, height