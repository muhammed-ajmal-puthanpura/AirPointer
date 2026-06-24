# ============================================================
# static_gestures.py  (v3 - bug-free, string-guaranteed)
# Pose -> command mapping with stability + one-shot triggers
# ============================================================

from collections import deque
import time


class GestureRecognizer:
    # Pose rules: which fingers must be UP / DOWN
    GESTURES = {
        "FIST":      {"up": [], "down": ["thumb", "index", "middle", "ring", "pinky"]},
        "OPEN_PALM": {"up": ["thumb", "index", "middle", "ring", "pinky"], "down": []},
        "POINTING":  {"up": ["index"], "down": ["middle", "ring", "pinky"]},
        "PEACE":     {"up": ["index", "middle"], "down": ["ring", "pinky"]},
        "THREE":     {"up": ["index", "middle", "ring"], "down": ["pinky"]},
        "FOUR":      {"up": ["index", "middle", "ring", "pinky"], "down": ["thumb"]},
        "THUMB_UP":  {"up": ["thumb"], "down": ["index", "middle", "ring", "pinky"]},
    }

    def __init__(self, stability_frames=5):
        self.stability_frames = stability_frames
        self.history = deque(maxlen=stability_frames)

        # Always-strings:
        self.current_gesture = "UNKNOWN"
        self.previous_gesture = "UNKNOWN"
        self.gesture_active = False
        self.gesture_start_time = time.time()

        # gesture name -> command
        self.gesture_map = {
            "FIST":      "IDLE",
            "OPEN_PALM": "NAVIGATE",
            "POINTING":  "POINTER",
            "PEACE":     "CLEAR_HIGHLIGHT",
            "THREE":     "NONE",
            "FOUR":      "NONE",
            "THUMB_UP":  "SELECT",
            "UNKNOWN":   "NONE",
        }
        print(">>> GestureRecognizer v3 LOADED | stability_frames =", stability_frames)

    def _classify(self, finger_states):
        """Return a gesture NAME (string). Most-specific match wins."""
        best = "UNKNOWN"
        best_score = -1
        for name, rule in self.GESTURES.items():
            score = 0
            ok = True
            for f in rule["up"]:
                score += 1
                if not finger_states.get(f, False):
                    ok = False
                    break
            if not ok:
                continue
            for f in rule["down"]:
                score += 1
                if finger_states.get(f, False):
                    ok = False
                    break
            if not ok:
                continue
            if score > best_score:
                best_score = score
                best = name
        return best   # <-- ALWAYS a string

    def update(self, finger_states):
        raw = self._classify(finger_states)   # string
        self.history.append(raw)

        # Confirm only if all recent frames agree (stability filter)
        if len(self.history) == self.stability_frames and all(g == raw for g in self.history):
            confirmed = raw
        else:
            confirmed = self.current_gesture  # hold previous stable gesture

        triggered = False
        changed = False

        if confirmed != self.current_gesture:
            self.previous_gesture = self.current_gesture
            self.current_gesture = confirmed          # guaranteed string
            self.gesture_start_time = time.time()
            changed = True
            if confirmed != "UNKNOWN":
                triggered = True                      # fires ONCE on lock-in

        self.gesture_active = (self.current_gesture != "UNKNOWN")

        # SAFE lookup (current_gesture is always a str)
        command = self.gesture_map.get(self.current_gesture, "NONE")

        return {
            "gesture":   self.current_gesture,
            "command":   command,
            "active":    self.gesture_active,
            "triggered": triggered,
            "changed":   changed,
            "previous":  self.previous_gesture,
        }

    def get_active_command(self):
        return self.gesture_map.get(self.current_gesture, "NONE")

    def get_held_duration(self):
        return time.time() - self.gesture_start_time

    def reset(self):
        self.history.clear()
        self.current_gesture = "UNKNOWN"
        self.previous_gesture = "UNKNOWN"
        self.gesture_active = False