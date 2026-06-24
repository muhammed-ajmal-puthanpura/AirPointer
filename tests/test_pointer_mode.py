# ============================================================
# test_pointer_mode.py
# Tests pointer mode — index finger moves cursor on screen
# Uses YOUR GestureRecogonizer API
# ============================================================

import os
import sys
import cv2

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from src.core.camera import CameraFeed
from src.core.hand_tracker import HandTracker
from src.gestures.finger_state import FingerStateDetector
from src.gestures.static_gestures import GestureRecognizer
from src.utils.screen_mapper import ScreenMapper
from src.utils.pointer_smoother import PointerSmoother


def main():
    print("=" * 60)
    print("Air Pointer - Pointer Mode Test")
    print("=" * 60)

    # Camera
    cam = CameraFeed(camera_index=0, width=640, height=480, fps=30)
    tracker = HandTracker(max_hands=1)
    finger_detector = FingerStateDetector(angle_threshold=160)
    gesture_recognizer = GestureRecognizer()

    # Screen mapping & smoothing
    mapper = ScreenMapper(camera_width=640, camera_height=480)
    mapper.get_screen_size()
    smoother = PointerSmoother(history_size=4)

    try:
        cam.start()
    except Exception as e:
        print(f"Camera error: {e}")
        return

    print(f"Screen size: {mapper.screen_width} x {mapper.screen_height}")
    print("Point your index finger to activate pointer.")
    print("Press Q to quit.")
    print("=" * 60)

    while True:
        success, frame = cam.read()
        if not success:
            print("Failed to read frame")
            break

        frame, landmarks_list = tracker.process(frame)

        if len(landmarks_list) > 0:
            landmarks = landmarks_list[0]

            # Finger states
            finger_states, finger_count, _ = finger_detector.detect_finger_states(landmarks)

            # YOUR GestureRecogonizer API
            result = gesture_recognizer.update(finger_states)
            gesture = result["gesture"]
            command = result["command"]
            triggered = result["triggered"]

            # Index fingertip is landmark #8
            index_tip = landmarks[8]
            hand_x, hand_y = index_tip["x"], index_tip["y"]

            # Draw index tip highlight
            cv2.circle(frame, (hand_x, hand_y), 15, (0, 255, 255), 3)
            cv2.circle(frame, (hand_x, hand_y), 6, (0, 200, 255), -1)

            # Activate pointer in POINTING mode
            if gesture == "POINTING":
                screen_x, screen_y = mapper.map_to_screen(hand_x, hand_y)
                smooth_x, smooth_y = smoother.smooth(screen_x, screen_y)

                cv2.putText(frame, f"POINTER ACTIVE -> ({smooth_x}, {smooth_y})",
                           (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(frame, f"Gesture: {gesture} | Command: {command}",
                           (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            if triggered:
                cv2.putText(frame, "TRIGGERED!", (20, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            # Show finger states
            y = 100
            for name in ["thumb", "index", "middle", "ring", "pinky"]:
                state = "UP" if finger_states[name] else "DOWN"
                color = (0, 255, 0) if finger_states[name] else (0, 0, 255)
                cv2.putText(frame, f"{name}: {state}", (20, y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                y += 25

        else:
            gesture_recognizer.reset()
            cv2.putText(frame, "No hand detected", (20, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.imshow("Air Pointer - Pointer Mode Test", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:
            break

    cam.release()
    cv2.destroyAllWindows()
    print("Done.")


if __name__ == "__main__":
    main()