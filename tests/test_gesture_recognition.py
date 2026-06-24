# ============================================================
# test_gesture_recognition.py
# Tests static gesture recognition with hold duration
# ============================================================

import os
import sys
import cv2
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from src.core.camera import CameraFeed
from src.core.hand_tracker import HandTracker
from src.gestures.finger_state import FingerStateDetector
from src.gestures.static_gestures import GestureRecognizer


def draw_progress_bar(frame, x, y, width, height, progress, color=(0, 255, 0)):
    """Draw a horizontal progress bar."""
    # Background
    cv2.rectangle(frame, (x, y), (x + width, y + height), (60, 60, 60), -1)
    # Progress
    filled_width = int(width * progress)
    if filled_width > 0:
        cv2.rectangle(frame, (x, y), (x + filled_width, y + height), color, -1)
    # Border
    cv2.rectangle(frame, (x, y), (x + width, y + height), (255, 255, 255), 1)


def main():
    print("=" * 60)
    print("Air Pointer - Gesture Recognition Test")
    print("=" * 60)

    cam = CameraFeed(camera_index=0, width=1280, height=720, fps=30)
    tracker = HandTracker(max_hands=1)
    detector = FingerStateDetector(angle_threshold=160)
    recognizer = GestureRecognizer(hold_duration=0.8)

    try:
        cam.start()
    except RuntimeError as e:
        print("ERROR:", e)
        return

    print("\n🎯 Gesture Guide:")
    print("  ✊ FIST        → PAUSE tracking")
    print("  ✋ OPEN PALM   → STOP pointer")
    print("  👆 POINTING    → MOVE cursor")
    print("  ✌️ PEACE       → ANNOTATE mode")
    print("  👍 THUMB UP    → CONFIRM/Click")
    print("\nHold gesture for 0.8 seconds to activate.")
    print("Press Q or ESC to quit.")
    print("=" * 60)

    while True:
        success, frame = cam.read()
        if not success:
            break

        frame, landmarks_list = tracker.process(frame)

        # Semi-transparent overlay for info panel
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (400, 250), (30, 30, 30), -1)
        frame = cv2.addWeighted(frame, 0.85, overlay, 0.15, 0)

        if len(landmarks_list) > 0:
            landmarks = landmarks_list[0]
            finger_states, finger_count, angles = detector.detect_finger_states(landmarks)
            pose = detector.detect_pose(finger_states)
            result = recognizer.update(pose)

            # Display info
            y = 40

            # Gesture name
            gesture_color = (0, 255, 0) if result["active"] else (255, 255, 255)
            cv2.putText(frame, f"Gesture: {result['gesture']}", (20, y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, gesture_color, 2)
            y += 30

            # Command
            cmd_color = (0, 255, 255) if result["active"] else (200, 200, 200)
            cv2.putText(frame, f"Command: {result['command']}", (20, y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, cmd_color, 2)
            y += 30

            # Status
            if result["active"]:
                status_text = "● ACTIVE"
                status_color = (0, 255, 0)
            else:
                status_text = "○ Waiting..."
                status_color = (255, 165, 0)
            cv2.putText(frame, status_text, (20, y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
            y += 35

            # Hold progress bar
            if recognizer.current_gesture and not recognizer.gesture_active:
                elapsed = time.time() - recognizer.gesture_start_time
                progress = min(elapsed / recognizer.hold_duration, 1.0)
                draw_progress_bar(frame, 20, y, 200, 15, progress, (255, 165, 0))

            # Show triggered effect
            if result["triggered"]:
                cv2.putText(frame, "ACTIVATED!", (250, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

        else:
            recognizer.reset()
            cv2.putText(frame, "No hand detected", (20, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.imshow("Air Pointer - Gesture Recognition", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:
            break

    cam.release()
    cv2.destroyAllWindows()
    print("✅ Gesture recognition test complete.")


if __name__ == "__main__":
    main()