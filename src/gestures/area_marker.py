# ============================================================
# area_marker.py  (v6 — Rectangle Selection Mode)
#
# Workflow:
#   1. Thumb + Index pinch      -> set rectangle start point
#   2. Move index finger        -> resize rectangle like crop box
#   3. Thumb + Index pinch again -> confirm rectangle highlight
#   4. Thumb + Middle pinch     -> cancel rectangle
#
# Output is still compatible with the existing main.py:
#   mark_result["points_px"] = rectangle polygon points
# ============================================================

import time
import math


class AreaMarker:
    STATE_IDLE = "IDLE"
    STATE_DRAWING = "DRAWING"

    def __init__(
        self,
        min_points=4,
        min_dimension=0.03,
        cooldown=0.8,
        pinch_threshold=40,
        middle_pinch_threshold=50,
        grid_size=10
    ):
        """
        min_dimension:
            Minimum rectangle width/height as normalized screen fraction.

        pinch_threshold:
            Pixel distance between thumb tip and index tip for start/close.

        middle_pinch_threshold:
            Pixel distance between thumb tip and middle tip for cancel.

        grid_size:
            Rectangle coordinates snap to this pixel grid.
            Use 1 to disable grid snapping.
        """

        self.min_points = min_points
        self.min_dimension = min_dimension
        self.cooldown = cooldown
        self.pinch_threshold = pinch_threshold
        self.middle_pinch_threshold = middle_pinch_threshold
        self.grid_size = max(1, int(grid_size))

        self.state = self.STATE_IDLE

        # Normalized points
        self.start = None          # (nx, ny)
        self.current = None        # (nx, ny)

        # Pixel points
        self.start_px = None       # (x, y)
        self.current_px = None     # (x, y)

        self.last_mark_time = 0.0

        # Pinch edge detection
        self.index_pinch_down = False
        self.middle_pinch_down = False

        print(
            f">>> AreaMarker v6 RECTANGLE MODE LOADED | "
            f"pinch={pinch_threshold}px middle={middle_pinch_threshold}px "
            f"grid={self.grid_size}px",
            flush=True
        )

    # ============================================================
    # Utility methods
    # ============================================================
    def _distance_px(self, p1, p2):
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def _is_thumb_index_pinch(self, landmarks):
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]

        dist = self._distance_px(
            (thumb_tip["x"], thumb_tip["y"]),
            (index_tip["x"], index_tip["y"])
        )

        return dist < self.pinch_threshold

    def _is_thumb_middle_pinch(self, landmarks):
        thumb_tip = landmarks[4]
        middle_tip = landmarks[12]

        dist = self._distance_px(
            (thumb_tip["x"], thumb_tip["y"]),
            (middle_tip["x"], middle_tip["y"])
        )

        return dist < self.middle_pinch_threshold

    def _snap_px(self, x, y):
        """
        Snap pixel coordinates to a uniform grid.
        This gives crop-tool-like rectangle movement.
        """
        if self.grid_size <= 1:
            return int(x), int(y)

        sx = round(x / self.grid_size) * self.grid_size
        sy = round(y / self.grid_size) * self.grid_size

        return int(sx), int(sy)

    def _px_to_norm(self, x, y, fw, fh):
        return x / fw, y / fh

    def _make_rectangle_points_px(self):
        """
        Return rectangle polygon points in clockwise order.
        """
        if self.start_px is None or self.current_px is None:
            return []

        x1, y1 = self.start_px
        x2, y2 = self.current_px

        left = min(x1, x2)
        right = max(x1, x2)
        top = min(y1, y2)
        bottom = max(y1, y2)

        return [
            (left, top),
            (right, top),
            (right, bottom),
            (left, bottom),
            (left, top),      # close polygon visually
        ]

    def _make_rectangle_points_norm(self, fw, fh):
        pts_px = self._make_rectangle_points_px()
        return [(x / fw, y / fh) for x, y in pts_px]

    def _rectangle_dimensions_norm(self, fw, fh):
        if self.start_px is None or self.current_px is None:
            return 0.0, 0.0

        x1, y1 = self.start_px
        x2, y2 = self.current_px

        width = abs(x2 - x1) / fw
        height = abs(y2 - y1) / fh

        return width, height

    # ============================================================
    # Main update method
    # ============================================================
    def update(self, landmarks, finger_states, command, fw, fh):
        """
        Call every frame.

        Returns:
            None if rectangle is not completed.

            dict if rectangle is confirmed:
            {
                "type": "rectangle",
                "points_px": [(x,y), ...],
                "bbox_px": (x1, y1, x2, y2),
                "pin_px": (start_x, start_y),
            }
        """

        now = time.time()

        if (now - self.last_mark_time) < self.cooldown:
            return None

        tip = landmarks[8]
        tip_x, tip_y = self._snap_px(tip["x"], tip["y"])
        tip_px = (tip_x, tip_y)
        tip_n = self._px_to_norm(tip_x, tip_y, fw, fh)

        is_index_pinch = self._is_thumb_index_pinch(landmarks)
        is_middle_pinch = self._is_thumb_middle_pinch(landmarks)

        # Rising-edge detection
        index_pinch_started = is_index_pinch and not self.index_pinch_down
        middle_pinch_started = is_middle_pinch and not self.middle_pinch_down

        self.index_pinch_down = is_index_pinch
        self.middle_pinch_down = is_middle_pinch

        # ========================================================
        # STATE: IDLE
        # Waiting for first thumb+index pinch
        # ========================================================
        if self.state == self.STATE_IDLE:
            if index_pinch_started:
                self.start_px = tip_px
                self.current_px = tip_px

                self.start = tip_n
                self.current = tip_n

                self.state = self.STATE_DRAWING

                print(
                    f"  Rectangle START at ({tip_px[0]}, {tip_px[1]})",
                    flush=True
                )

            return None

        # ========================================================
        # STATE: DRAWING
        # Rectangle expands from start point to current index position
        # ========================================================
        if self.state == self.STATE_DRAWING:

            # Cancel with thumb + middle pinch
            if middle_pinch_started:
                print("  Rectangle CANCELLED by middle pinch", flush=True)
                self._cancel()
                return None

            # Update rectangle endpoint whenever not closing
            if not is_index_pinch:
                self.current_px = tip_px
                self.current = tip_n

            # Confirm rectangle with second thumb+index pinch
            if index_pinch_started:
                result = self._complete_rectangle(fw, fh)
                return result

        return None

    # ============================================================
    # Complete rectangle
    # ============================================================
    def _complete_rectangle(self, fw, fh):
        width, height = self._rectangle_dimensions_norm(fw, fh)

        if width < self.min_dimension or height < self.min_dimension:
            print(
                f"  Rectangle too small "
                f"(w={width:.3f}, h={height:.3f}), cancelled.",
                flush=True
            )
            self._cancel()
            return None

        points_px = self._make_rectangle_points_px()

        xs = [p[0] for p in points_px]
        ys = [p[1] for p in points_px]

        bbox_px = (
            min(xs),
            min(ys),
            max(xs),
            max(ys)
        )

        result = {
            "type": "rectangle",
            "points_px": points_px,
            "bbox_px": bbox_px,
            "pin_px": self.start_px,
        }

        print(
            f"  Rectangle COMPLETE! bbox={bbox_px}",
            flush=True
        )

        self.last_mark_time = time.time()
        self._cancel()

        return result

    # ============================================================
    # Public getters used by main.py
    # ============================================================
    def get_state(self):
        return self.state

    def get_pin_px(self):
        return self.start_px

    def get_trail_px(self):
        """
        Existing main.py expects a trail/polygon list.
        For rectangle mode, return rectangle preview points.
        """
        if self.state != self.STATE_DRAWING:
            return []

        return self._make_rectangle_points_px()

    def get_progress(self):
        """
        Progress based on rectangle size.
        """
        if self.state != self.STATE_DRAWING:
            return 0.0

        if self.start_px is None or self.current_px is None:
            return 0.0

        x1, y1 = self.start_px
        x2, y2 = self.current_px

        dist = self._distance_px((x1, y1), (x2, y2))

        # Rough progress estimate
        progress = min(1.0, dist / 250.0)
        return progress

    def reset(self):
        self._cancel()

    def _cancel(self):
        self.state = self.STATE_IDLE
        self.start = None
        self.current = None
        self.start_px = None
        self.current_px = None