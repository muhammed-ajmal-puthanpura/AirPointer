# ============================================================
# hand_tracker.py  (v3 — very low confidence for fast motion)
# ============================================================

import cv2
import mediapipe as mp


class HandTracker:
    def __init__(self,
                 static_mode=False,
                 max_hands=1,
                 detection_confidence=0.4,    # very low for fast motion
                 tracking_confidence=0.35):   # very low to maintain tracking
        self.static_mode = static_mode
        self.max_hands = max_hands
        self.detection_confidence = detection_confidence
        self.tracking_confidence = tracking_confidence

        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils

        self.hands = self.mp_hands.Hands(
            static_image_mode=self.static_mode,
            max_num_hands=self.max_hands,
            min_detection_confidence=self.detection_confidence,
            min_tracking_confidence=self.tracking_confidence
        )

        # Store last known landmarks for gap-bridging
        self.last_landmarks = None
        self.frames_since_last = 0
        self.max_gap_frames = 8    # bridge up to 8 lost frames (~0.27s at 30fps)

    def process(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        landmarks_list = []

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                single_hand_landmarks = []
                for id, lm in enumerate(hand_landmarks.landmark):
                    h, w, c = frame.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    single_hand_landmarks.append({
                        "id": id,
                        "x": cx,
                        "y": cy,
                        "z": lm.z
                    })
                landmarks_list.append(single_hand_landmarks)
                self.mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS
                )

            # Save last known good landmarks
            self.last_landmarks = landmarks_list
            self.frames_since_last = 0
        else:
            # Hand lost — use last known position for a few frames
            self.frames_since_last += 1
            if (self.last_landmarks is not None and
                    self.frames_since_last <= self.max_gap_frames):
                landmarks_list = self.last_landmarks
            else:
                self.last_landmarks = None

        return frame, landmarks_list