# ============================================================
# test_finger_state.py
# Tests finger state detection
# ============================================================

import os
import sys
import cv2

# Add project root to Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from src.core.camera import CameraFeed
from src.core.hand_tracker import HandTracker
from src.gestures.finger_state import FingerStateDetector


def main():
    print("=" * 60)
    print("Air Pointer - Finger State Test")
    print("=" * 60)

    cam = CameraFeed(camera_index=0, width=1280, height=720, fps=30)
    tracker = HandTracker(max_hands=1)
    detector = FingerStateDetector(angle_threshold=160)

    try:
        cam.start()
    except RuntimeError as e:
        print("ERROR:", e)
        return

    print("Show your hand to the camera.")
    print("Try: open palm, fist, point, peace sign.")
    print("Press Q or ESC to quit.")
    print("=" * 60)

    while True:
        success, frame = cam.read()
        if not success:
            break

        frame, landmarks_list = tracker.process(frame)

        if len(landmarks_list) > 0:
            landmarks = landmarks_list[0]

            finger_states, finger_count, angles = detector.detect_finger_states(landmarks)
            pose = detector.detect_pose(finger_states)

            cv2.putText(frame, f"Fingers Up: {finger_count}", (20, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.putText(frame, f"Pose: {pose}", (20, 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            y = 130
            for finger_name in ["thumb", "index", "middle", "ring", "pinky"]:
                state = "UP" if finger_states[finger_name] else "DOWN"
                angle = int(angles[finger_name])
                color = (0, 255, 0) if finger_states[finger_name] else (0, 0, 255)

                cv2.putText(frame, f"{finger_name.capitalize():<6}: {state}  Angle: {angle}",
                           (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                y += 35

        else:
            cv2.putText(frame, "No hand detected", (20, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imshow("Air Pointer - Finger State Test", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:
            break

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()