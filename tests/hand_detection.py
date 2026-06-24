# ============================================================
# test_hand_detection.py
# Tests MediaPipe hand tracking
# ============================================================

import os
import sys
import cv2

# Add project root to Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from src.core.camera import CameraFeed
from src.core.hand_tracker import HandTracker


def main():
    print("=" * 60)
    print("Air Pointer - Hand Detection Test")
    print("=" * 60)

    cam = CameraFeed(camera_index=0, width=1280, height=720, fps=30)
    tracker = HandTracker(max_hands=1)

    try:
        cam.start()
    except RuntimeError as e:
        print("ERROR:", e)
        return

    print("Show your hand to the camera.")
    print("Press Q or ESC to quit.")
    print("=" * 60)

    while True:
        success, frame = cam.read()
        if not success:
            break

        frame, landmarks = tracker.process(frame)

        # Display number of detected hands
        cv2.putText(
            frame,
            f"Hands detected: {len(landmarks)}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        # Display example: index fingertip coordinates (ID 8)
        if len(landmarks) > 0:
            index_tip = landmarks[0][8]
            text = f"Index Tip: ({index_tip['x']}, {index_tip['y']})"

            cv2.putText(
                frame,
                text,
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

        cv2.imshow("Air Pointer - Hand Detection", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:
            break

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()