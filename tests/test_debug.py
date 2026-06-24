# ============================================================
# test_debug.py  - Minimal isolated test
# ============================================================
import os, sys, traceback
import cv2

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

print("Step 1: Importing modules...")
try:
    from src.core.camera import CameraFeed
    from src.core.hand_tracker import HandTracker
    from src.gestures.finger_state import FingerStateDetector
    print("  ✅ Imports OK")
except Exception:
    print("  ❌ IMPORT FAILED:")
    traceback.print_exc()
    sys.exit()

print("Step 2: Starting camera...")
try:
    cam = CameraFeed(camera_index=0, width=1280, height=720, fps=30)
    cam.start()
    print("  ✅ Camera OK")
except Exception:
    print("  ❌ CAMERA FAILED:")
    traceback.print_exc()
    sys.exit()

print("Step 3: Creating tracker + detector...")
tracker = HandTracker(max_hands=1)
detector = FingerStateDetector(angle_threshold=160)
print("  ✅ Objects created")

print("Step 4: Entering main loop (press Q to quit)...")
frame_count = 0

while True:
    success, frame = cam.read()
    if not success:
        print("  ⚠️ Failed to read frame")
        break

    frame_count += 1

    try:
        frame, landmarks_list = tracker.process(frame)

        if len(landmarks_list) > 0:
            landmarks = landmarks_list[0]
            finger_states, finger_count, angles = detector.detect_finger_states(landmarks)
            pose = detector.detect_pose(finger_states)

            # Print to terminal every 30 frames (once per second)
            if frame_count % 30 == 0:
                print(f"  Fingers up: {finger_count} | Pose: {pose} | States: {finger_states}")

            cv2.putText(frame, f"Fingers: {finger_count}", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Pose: {pose}", (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        else:
            if frame_count % 30 == 0:
                print("  No hand detected")

    except Exception:
        print("  ❌ ERROR IN PROCESSING LOOP:")
        traceback.print_exc()
        break

    cv2.imshow("DEBUG TEST", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cam.release()
cv2.destroyAllWindows()
print("Step 5: Closed cleanly.")