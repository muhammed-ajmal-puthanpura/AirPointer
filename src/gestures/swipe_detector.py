# ============================================================
# swipe_detector.py
# Motion-based swipe detection (left/right/up/down)
# Works on NORMALIZED (0-1) palm-center coordinates
# ============================================================

import time
from collections import deque


class SwipeDetector:
    # Map swipe events to logical slide actions
    ACTION_MAP = {
        "SWIPE_RIGHT": "NEXT_SLIDE",
        "SWIPE_LEFT":  "PREV_SLIDE",
        "SWIPE_UP":    "START_PRESENTATION",
        "SWIPE_DOWN":  "END_PRESENTATION",
    }

    def __init__(self,
                 window=0.40,           # seconds of history to measure over
                 min_displacement=0.18, # min travel as fraction of frame (0-1)
                 dominance_ratio=1.4,   # primary axis must beat other by this ratio
                 cooldown=0.90,         # seconds to block after a swipe fires
                 invert_horizontal=False,
                 invert_vertical=False):
        self.window = window
        self.min_displacement = min_displacement
        self.dominance_ratio = dominance_ratio
        self.cooldown = cooldown
        self.invert_horizontal = invert_horizontal
        self.invert_vertical = invert_vertical

        self.history = deque()          # (timestamp, nx, ny)
        self.last_swipe_time = 0.0
        self.last_event = None

        print(f">>> SwipeDetector LOADED | window={window}s "
              f"min_disp={min_displacement} cooldown={cooldown}s "
              f"invertH={invert_horizontal}")

    def _apply_inversion(self, event):
        if event in ("SWIPE_LEFT", "SWIPE_RIGHT") and self.invert_horizontal:
            return "SWIPE_LEFT" if event == "SWIPE_RIGHT" else "SWIPE_RIGHT"
        if event in ("SWIPE_UP", "SWIPE_DOWN") and self.invert_vertical:
            return "SWIPE_UP" if event == "SWIPE_DOWN" else "SWIPE_DOWN"
        return event

    def update(self, nx, ny, tracking_active=True):
        """
        Feed the latest NORMALIZED palm-center position (0-1).
        Returns a swipe EVENT string ("SWIPE_LEFT", ...) or None.
        """
        now = time.time()

        # If we left the tracking gesture, wipe history (clean start next time)
        if not tracking_active:
            self.history.clear()
            return None

        # Add current point
        self.history.append((now, float(nx), float(ny)))

        # Drop points older than the measurement window
        cutoff = now - self.window
        while self.history and self.history[0][0] < cutoff:
            self.history.popleft()

        # Cooldown: don't fire again too soon
        if (now - self.last_swipe_time) < self.cooldown:
            return None

        # Need enough data spanning at least half the window
        if len(self.history) < 3:
            return None
        t0, x0, y0 = self.history[0]
        t1, x1, y1 = self.history[-1]
        if (t1 - t0) < self.window * 0.5:
            return None

        dx = x1 - x0
        dy = y1 - y0
        abs_dx, abs_dy = abs(dx), abs(dy)

        event = None
        # Horizontal swipe: big dx that dominates dy
        if abs_dx >= self.min_displacement and abs_dx > abs_dy * self.dominance_ratio:
            event = "SWIPE_RIGHT" if dx > 0 else "SWIPE_LEFT"
        # Vertical swipe: big dy that dominates dx
        elif abs_dy >= self.min_displacement and abs_dy > abs_dx * self.dominance_ratio:
            event = "SWIPE_DOWN" if dy > 0 else "SWIPE_UP"

        if event:
            event = self._apply_inversion(event)
            self.last_swipe_time = now
            self.last_event = event
            self.history.clear()   # reset so the same motion can't fire twice
            return event

        return None

    def get_action(self, event):
        """Map an event to a logical action name."""
        return self.ACTION_MAP.get(event, "NONE")

    def cooldown_remaining(self):
        """Seconds of cooldown left (0.0 when ready)."""
        rem = self.cooldown - (time.time() - self.last_swipe_time)
        return max(0.0, rem)

    def reset(self):
        self.history.clear()
        self.last_event = None