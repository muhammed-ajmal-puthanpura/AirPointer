# ============================================================
# area_marker.py  (v5 — pinch to start, pinch to close)
#
# Workflow:
#   1. PINCH (thumb+index)     = drop pin + start drawing
#   2. POINT (index up)        = draw boundary freely
#   3. PINCH again (thumb+index) = close + complete highlight
#   4. MIDDLE PINCH (thumb+middle) = CANCEL current marking
# ============================================================

import time
import math
from collections import deque


class AreaMarker:
    STATE_IDLE = "IDLE"
    STATE_DRAWING = "DRAWING"

    def __init__(self,
                 min_points=15,
                 min_dimension=0.02,
                 cooldown=0.8,
                 pinch_threshold=40,
                 middle_pinch_threshold=50):
        self.min_points = min_points
        self.min_dimension = min_dimension
        self.cooldown = cooldown
        self.pinch_threshold = pinch_threshold
        self.middle_pinch_threshold = middle_pinch_threshold

        self.state = self.STATE_IDLE
        self.pin = None
        self.pin_px = None
        self.trail = []
        self.trail_px = []
        self.last_mark_time = 0.0

        print(f">>> AreaMarker v5 LOADED | "
              f"pinch={pinch_threshold}px middle={middle_pinch_threshold}px", flush=True)

    def _distance_px(self, p1, p2):
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def _distance(self, p1, p2):
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def _bounding_box(self, points):
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return min(xs), min(ys), max(xs), max(ys)

    def _is_thumb_index_pinch(self, landmarks):
        """Thumb tip + Index tip touching."""
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        dist = self._distance_px(
            (thumb_tip["x"], thumb_tip["y"]),
            (index_tip["x"], index_tip["y"])
        )
        return dist < self.pinch_threshold

    def _is_thumb_middle_pinch(self, landmarks):
        """Thumb tip + Middle tip touching (cancel gesture)."""
        thumb_tip = landmarks[4]
        middle_tip = landmarks[12]
        dist = self._distance_px(
            (thumb_tip["x"], thumb_tip["y"]),
            (middle_tip["x"], middle_tip["y"])
        )
        return dist < self.middle_pinch_threshold

    def update(self, landmarks, finger_states, command, fw, fh):
        now = time.time()

        if (now - self.last_mark_time) < self.cooldown:
            return None

        tip = landmarks[8]
        tip_px = (tip["x"], tip["y"])
        tip_n = (tip["x"] / fw, tip["y"] / fh)

        # ============================================================
        # STATE: IDLE
        # ============================================================
        if self.state == self.STATE_IDLE:
            # Check for thumb+index pinch to start
            if self._is_thumb_index_pinch(landmarks):
                # Start new marking
                self.pin = tip_n
                self.pin_px = tip_px
                self.trail = [tip_n]
                self.trail_px = [tip_px]
                self.state = self.STATE_DRAWING
                print(f"  Pinch START at ({tip_px[0]}, {tip_px[1]})", flush=True)

            return None

        # ============================================================
        # STATE: DRAWING
        # ============================================================
        if self.state == self.STATE_DRAWING:
            is_thumb_index = self._is_thumb_index_pinch(landmarks)
            is_middle_pinch = self._is_thumb_middle_pinch(landmarks)

            # ---- CANCEL: middle pinch ----
            if is_middle_pinch:
                print("  Middle pinch CANCELLED marking", flush=True)
                self._cancel()
                return None

            # ---- CLOSE: thumb+index pinch while pointing ----
            if is_thumb_index and command == "POINTER":
                # Complete the marking
                result = self._complete_mark(fw, fh)
                return result

            # ---- Keep drawing: pointing ----
            if command == "POINTER" and not is_thumb_index:
                # Only add if moved enough (prevents duplicate points)
                if not self.trail or self._distance(tip_n, self.trail[-1]) > 0.004:
                    self.trail.append(tip_n)
                    self.trail_px.append(tip_px)

                    if len(self.trail) > 500:
                        self.trail.pop(0)
                        self.trail_px.pop(0)

            # ---- Re-start: pinch while already drawing ----
            # (move the pin and restart)
            if is_thumb_index and command != "POINTER":
                self.pin = tip_n
                self.pin_px = tip_px
                self.trail = [tip_n]
                self.trail_px = [tip_px]
                print(f"  Pinch RESTART at ({tip_px[0]}, {tip_px[1]})", flush=True)

            # ---- Cancel on fist ----
            if command == "IDLE" and not is_thumb_index and not is_middle_pinch:
                # Give it a moment — maybe user just relaxed briefly
                # Don't cancel immediately, let it resume if they point again
                pass

        return None

    def _complete_mark(self, fw, fh):
        if len(self.trail) < self.min_points:
            print(f"  Too few points ({len(self.trail)}), cancelled.", flush=True)
            self._cancel()
            return None

        x1, y1, x2, y2 = self._bounding_box(self.trail)
        width = x2 - x1
        height = y2 - y1

        if width < self.min_dimension and height < self.min_dimension:
            print("  Area too small, cancelled.", flush=True)
            self._cancel()
            return None

        # Close the polygon
        if self.pin:
            self.trail.append(self.pin)
            self.trail_px.append(self.pin_px)

        bx1, by1, bx2, by2 = self._bounding_box(self.trail_px)

        result = {
            "type": "freeform",
            "points_px": list(self.trail_px),
            "bbox_px": (bx1, by1, bx2, by2),
            "pin_px": self.pin_px,
        }

        print(f"  Pinch CLOSE! {len(self.trail_px)} points, "
              f"bbox=({bx1},{by1})-({bx2},{by2})", flush=True)

        self.last_mark_time = time.time()
        self._cancel()
        return result

    def _cancel(self):
        self.state = self.STATE_IDLE
        self.pin = None
        self.pin_px = None
        self.trail = []
        self.trail_px = []

    def get_state(self):
        return self.state

    def get_pin_px(self):
        return self.pin_px

    def get_trail_px(self):
        return list(self.trail_px)

    def get_progress(self):
        """
        Progress based on how many points drawn vs minimum needed.
        """
        if self.state != self.STATE_DRAWING:
            return 0.0
        return min(1.0, len(self.trail) / self.min_points)

    def reset(self):
        self._cancel()