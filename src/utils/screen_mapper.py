# ============================================================
# screen_mapper.py
# Maps hand coordinates to screen coordinates
# ============================================================

import numpy as np


class ScreenMapper:
    def __init__(self, camera_width=1280, camera_height=720):
        self.camera_width = camera_width
        self.camera_height = camera_height
        self.screen_width = 1920
        self.screen_height = 1080

        # Edge margin (dead zone) to prevent cursor at extreme edges
        self.margin_x = 80
        self.margin_y = 80

        # Calibration offsets
        self.offset_x = 0
        self.offset_y = 0

        # Sensitivity multiplier
        self.sensitivity = 1.5

    def get_screen_size(self):
        """Auto-detect screen size."""
        try:
            from screeninfo import get_monitors
            monitor = get_monitors()[0]
            self.screen_width = monitor.width
            self.screen_height = monitor.height
        except:
            # Fallback to 1920x1080
            pass

        return self.screen_width, self.screen_height

    def map_to_screen(self, hand_x, hand_y):
        """
        Map camera coordinates to screen coordinates.

        Args:
            hand_x, hand_y: Hand position in camera frame

        Returns:
            screen_x, screen_y: Mapped screen coordinates
        """
        # Apply margin
        cam_x_min = self.margin_x
        cam_x_max = self.camera_width - self.margin_x
        cam_y_min = self.margin_y
        cam_y_max = self.camera_height - self.margin_y

        # Clamp hand position to valid range
        hand_x = max(cam_x_min, min(hand_x, cam_x_max))
        hand_y = max(cam_y_min, min(hand_y, cam_y_max))

        # Map to 0-1 range
        norm_x = (hand_x - cam_x_min) / (cam_x_max - cam_x_min)
        norm_y = (hand_y - cam_y_min) / (cam_y_max - cam_y_min)

        # Apply sensitivity
        norm_x = 0.5 + (norm_x - 0.5) * self.sensitivity
        norm_y = 0.5 + (norm_y - 0.5) * self.sensitivity

        # Clamp to 0-1
        norm_x = max(0.0, min(1.0, norm_x))
        norm_y = max(0.0, min(1.0, norm_y))

        # Map to screen
        screen_x = int(norm_x * self.screen_width)
        screen_y = int(norm_y * self.screen_height)

        return screen_x, screen_y