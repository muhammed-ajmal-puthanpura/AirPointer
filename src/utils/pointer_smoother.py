# ============================================================
# pointer_smoother.py
# Smoothes pointer movement using moving average
# ============================================================

from collections import deque


class PointerSmoother:
    def __init__(self, history_size=5):
        """
        Args:
            history_size: Number of frames to average over
        """
        self.history_size = history_size
        self.x_history = deque(maxlen=history_size)
        self.y_history = deque(maxlen=history_size)

    def smooth(self, x, y):
        """
        Smooth pointer coordinates.
        Returns smoothed (x, y).
        """
        self.x_history.append(x)
        self.y_history.append(y)

        if len(self.x_history) == 0:
            return x, y

        avg_x = int(sum(self.x_history) / len(self.x_history))
        avg_y = int(sum(self.y_history) / len(self.y_history))

        return avg_x, avg_y

    def set_strength(self, strength):
        """
        Set smoothing strength.
        strength: 1-10 (higher = smoother but more lag)
        """
        self.history_size = max(1, strength)
        self.x_history = deque(maxlen=self.history_size)
        self.y_history = deque(maxlen=self.history_size)