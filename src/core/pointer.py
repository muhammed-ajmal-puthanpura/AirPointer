# ============================================================
# pointer.py
# Air Pointer screen mapper + smoother + optional mouse control
# ============================================================

import os
import ctypes


def _get_screen_size():
    """
    Get screen size without importing pyautogui at startup.
    This avoids pyautogui hanging on Windows.
    """
    try:
        if os.name == "nt":
            user32 = ctypes.windll.user32
            return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    except Exception:
        pass

    # fallback
    import pyautogui
    return pyautogui.size()


class PointerMapper:
    def __init__(
        self,
        frame_width,
        frame_height,
        screen_width=None,
        screen_height=None,
        margin=0.25,
        smoothing=0.45
    ):
        """
        frame_width/frame_height:
            camera frame size

        screen_width/screen_height:
            monitor size. If None, auto detected.

        margin:
            camera dead-zone border.
            Example 0.25 means inner 50% camera area maps to full screen.

        smoothing:
            0.05 = very smooth but laggy
            1.0  = instant but jittery
        """

        self.frame_width = frame_width
        self.frame_height = frame_height
        self.margin = max(0.0, min(0.45, margin))
        self.smoothing = max(0.01, min(1.0, smoothing))

        if screen_width is None or screen_height is None:
            sw, sh = _get_screen_size()
            self.screen_width = screen_width or sw
            self.screen_height = screen_height or sh
        else:
            self.screen_width = screen_width
            self.screen_height = screen_height

        self._sx = self.screen_width / 2
        self._sy = self.screen_height / 2
        self._initialized = False

        self._pyautogui = None

        print(
            f">>> PointerMapper LOADED | "
            f"frame={self.frame_width}x{self.frame_height} "
            f"screen={self.screen_width}x{self.screen_height} "
            f"margin={self.margin} smoothing={self.smoothing}",
            flush=True
        )

    def _lazy_pyautogui(self):
        """
        Import pyautogui only when mouse movement is actually enabled.
        """
        if self._pyautogui is None:
            import pyautogui
            pyautogui.FAILSAFE = False
            pyautogui.PAUSE = 0
            self._pyautogui = pyautogui

        return self._pyautogui

    def get_region(self):
        """
        Return active camera region:
        x1, y1, x2, y2
        """
        x1 = int(self.margin * self.frame_width)
        y1 = int(self.margin * self.frame_height)
        x2 = int((1 - self.margin) * self.frame_width)
        y2 = int((1 - self.margin) * self.frame_height)

        return x1, y1, x2, y2

    def map(self, tip_x, tip_y):
        """
        Convert fingertip camera coordinates to screen coordinates.
        Returns:
            sx, sy
        """

        x1, y1, x2, y2 = self.get_region()

        region_w = max(1, x2 - x1)
        region_h = max(1, y2 - y1)

        # normalize fingertip inside active region
        nx = (tip_x - x1) / region_w
        ny = (tip_y - y1) / region_h

        # clamp
        nx = max(0.0, min(1.0, nx))
        ny = max(0.0, min(1.0, ny))

        target_sx = nx * self.screen_width
        target_sy = ny * self.screen_height

        # first frame snaps directly
        if not self._initialized:
            self._sx = target_sx
            self._sy = target_sy
            self._initialized = True

        # smoothing
        self._sx = self.smoothing * target_sx + (1 - self.smoothing) * self._sx
        self._sy = self.smoothing * target_sy + (1 - self.smoothing) * self._sy

        return self._sx, self._sy

    def move_mouse(self, sx=None, sy=None):
        """
        Move actual system mouse cursor.
        """
        pg = self._lazy_pyautogui()

        if sx is None:
            sx = self._sx
        if sy is None:
            sy = self._sy

        sx = max(0, min(self.screen_width - 1, int(sx)))
        sy = max(0, min(self.screen_height - 1, int(sy)))

        pg.moveTo(sx, sy)

    def reset(self):
        """
        Reset smoothing state.
        """
        self._initialized = False

    def map_raw(self, tip_x, tip_y):
    

        x1, y1, x2, y2 = self.get_region()

        region_w = max(1, x2 - x1)
        region_h = max(1, y2 - y1)

        nx = (tip_x - x1) / region_w
        ny = (tip_y - y1) / region_h

        nx = max(0.0, min(1.0, nx))
        ny = max(0.0, min(1.0, ny))

        sx = nx * self.screen_width
        sy = ny * self.screen_height

        return sx, sy