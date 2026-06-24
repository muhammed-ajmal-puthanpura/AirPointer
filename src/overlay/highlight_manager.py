# ============================================================
# highlight_manager.py  (v2 — supports free-form polygon highlights)
# ============================================================

import cv2
import numpy as np
import time


class HighlightManager:
    def __init__(self, fade_duration=0.0, dim_factor=0.30):
        """
        fade_duration: seconds before auto-fade (0 = never)
        dim_factor: how dark outside area is (0.0=black, 1.0=no dim)
        """
        self.fade_duration = fade_duration
        self.dim_factor = dim_factor
        self.highlights = []
        print(f">>> HighlightManager v2 LOADED | fade={fade_duration}s "
              f"dim={dim_factor}")

    def add_freeform(self, points_px, color=(0, 255, 255), border_thickness=3):
        """
        Add a free-form polygon highlight.
        points_px: list of (x, y) pixel coordinates forming the shape.
        """
        if len(points_px) < 3:
            return

        pts_array = np.array(points_px, dtype=np.int32)

        self.highlights.append({
            "type": "freeform",
            "points": pts_array,
            "color": color,
            "border_thickness": border_thickness,
            "created_at": time.time(),
        })
        print(f"  Free-form highlight added ({len(points_px)} pts) "
              f"total={len(self.highlights)}")

    def add_circle(self, cx, cy, radius, color=(0, 255, 255)):
        """Add a circle highlight (backward compatible)."""
        self.highlights.append({
            "type": "circle",
            "cx": int(cx),
            "cy": int(cy),
            "radius": max(20, int(radius)),
            "color": color,
            "created_at": time.time(),
        })
        print(f"  Circle highlight added: ({int(cx)},{int(cy)}) "
              f"r={int(radius)}px total={len(self.highlights)}")

    def clear(self):
        self.highlights.clear()
        print("  All highlights cleared.")

    def _is_expired(self, h):
        if self.fade_duration <= 0:
            return False
        return (time.time() - h["created_at"]) > self.fade_duration

    def draw(self, frame):
        """Draw all highlights with spotlight effect."""
        if not self.highlights:
            return frame

        # Remove expired
        self.highlights = [h for h in self.highlights if not self._is_expired(h)]
        if not self.highlights:
            return frame

        fh, fw = frame.shape[:2]

        # Build combined mask of all highlighted regions
        mask = np.zeros((fh, fw), dtype=np.uint8)

        for hl in self.highlights:
            if hl["type"] == "freeform":
                cv2.fillPoly(mask, [hl["points"]], 255)
            elif hl["type"] == "circle":
                cv2.circle(mask, (hl["cx"], hl["cy"]), hl["radius"], 255, -1)

        # Apply spotlight: dim outside, bright inside
        dark = (frame * self.dim_factor).astype(np.uint8)
        spotlight = np.where(mask[:, :, np.newaxis] == 255, frame, dark)
        result = spotlight.copy()

        # Draw borders
        for hl in self.highlights:
            col = hl["color"]
            if hl["type"] == "freeform":
                # Smooth polygon border
                cv2.polylines(result, [hl["points"]], isClosed=True,
                              color=col, thickness=3)
                # Outer glow
                cv2.polylines(result, [hl["points"]], isClosed=True,
                              color=(col[0]//2, col[1]//2, col[2]//2),
                              thickness=6)
            elif hl["type"] == "circle":
                cv2.circle(result, (hl["cx"], hl["cy"]),
                           hl["radius"], col, 3)
                cv2.circle(result, (hl["cx"], hl["cy"]),
                           hl["radius"] + 5,
                           (col[0]//2, col[1]//2, col[2]//2), 2)

        return result

    def count(self):
        return len(self.highlights)