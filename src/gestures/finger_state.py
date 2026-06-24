# ============================================================
# finger_state.py  (v4 — tip vs PIP method, much more accurate)
# Uses Y-position comparison instead of angles
# ============================================================

import math


class FingerStateDetector:
    def __init__(self):
        # Landmark IDs for each finger
        # (MCP = base, PIP = middle joint, TIP = fingertip)
        #
        # MediaPipe Hand Landmarks:
        #   Thumb:  1(CMC) 2(MCP) 3(IP)  4(TIP)
        #   Index:  5(MCP) 6(PIP) 7(DIP) 8(TIP)
        #   Middle: 9(MCP) 10(PIP) 11(DIP) 12(TIP)
        #   Ring:   13(MCP) 14(PIP) 15(DIP) 16(TIP)
        #   Pinky:  17(MCP) 18(PIP) 19(DIP) 20(TIP)

        # For UP/DOWN detection: compare TIP.y vs PIP.y
        self.finger_tip_ids = {
            "index":  8,
            "middle": 12,
            "ring":   16,
            "pinky":  20,
        }
        self.finger_pip_ids = {
            "index":  6,
            "middle": 10,
            "ring":   14,
            "pinky":  18,
        }

        # Thumb uses X-distance method (unchanged)
        self.THUMB_TIP = 4
        self.THUMB_IP = 3
        self.INDEX_MCP = 5

        print(">>> FingerStateDetector v4 LOADED (tip-vs-pip method)")

    def _distance(self, p1, p2):
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def _detect_thumb(self, points):
        """
        Thumb detection using distance method (mirror-immune).
        Thumb is UP if tip is farther from index base than thumb IP joint.
        """
        if (self.THUMB_TIP not in points or
            self.THUMB_IP not in points or
            self.INDEX_MCP not in points):
            return False

        thumb_tip = points[self.THUMB_TIP]
        thumb_ip = points[self.THUMB_IP]
        index_mcp = points[self.INDEX_MCP]

        tip_dist = self._distance(thumb_tip, index_mcp)
        ip_dist = self._distance(thumb_ip, index_mcp)

        return tip_dist > ip_dist

    def detect_finger_states(self, landmarks):
        """
        Detect which fingers are up/down using tip-vs-pip Y comparison.

        Args:
            landmarks: list of landmark dicts [{id, x, y, z}, ...]

        Returns:
            finger_states: {"thumb": bool, "index": bool, ...}
            finger_count: int (number of fingers up)
            details: dict with extra info per finger
        """
        # Convert to lookup dict
        points = {}
        for lm in landmarks:
            points[lm["id"]] = (lm["x"], lm["y"])

        finger_states = {}
        details = {}

        # ---- Thumb (distance method) ----
        finger_states["thumb"] = self._detect_thumb(points)
        details["thumb"] = {"method": "distance"}

        # ---- Index, Middle, Ring, Pinky (tip vs pip Y comparison) ----
        for finger_name in ["index", "middle", "ring", "pinky"]:
            tip_id = self.finger_tip_ids[finger_name]
            pip_id = self.finger_pip_ids[finger_name]

            if tip_id in points and pip_id in points:
                tip_y = points[tip_id][1]
                pip_y = points[pip_id][1]

                # Tip ABOVE pip = finger UP (smaller Y = higher on screen)
                # Add a small margin (8 pixels) to prevent flickering
                margin = 8
                is_up = tip_y < (pip_y - margin)

                finger_states[finger_name] = is_up
                details[finger_name] = {
                    "tip_y": tip_y,
                    "pip_y": pip_y,
                    "diff": pip_y - tip_y,
                    "method": "tip_vs_pip"
                }
            else:
                finger_states[finger_name] = False
                details[finger_name] = {"method": "missing"}

        finger_count = sum(1 for s in finger_states.values() if s)
        return finger_states, finger_count, details

    def detect_pose(self, finger_states):
        """Detect common hand poses."""
        thumb  = finger_states.get("thumb", False)
        index  = finger_states.get("index", False)
        middle = finger_states.get("middle", False)
        ring   = finger_states.get("ring", False)
        pinky  = finger_states.get("pinky", False)

        if not index and not middle and not ring and not pinky:
            return "FIST"
        if index and middle and ring and pinky:
            return "OPEN_PALM"
        if index and not middle and not ring and not pinky:
            return "POINTING"
        if index and middle and not ring and not pinky:
            return "PEACE"
        if thumb and not index and not middle and not ring and not pinky:
            return "THUMB_UP"
        return "UNKNOWN"