# ============================================================
# test_camera_feed.py
# Tests live webcam feed
# ============================================================

import os
import sys
import time
import cv2

# Add project root to Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from src.core.camera import CameraFeed


def main():
    print("=" * 60)
    print("Air Pointer - Camera Feed Test")
    print("=" * 60)

    # If camera does not open, change camera_index to 1
    camera_index = 0

    cam = CameraFeed(
        camera_index=camera_index,
        width=1280,
        height=720,
        fps=30,
        mirror=True
    )

    try:
        cam.start()
    except RuntimeError as e:
        print("ERROR:", e)
        print("\nTry these fixes:")
        print("1. Close Zoom/Teams/Camera app if open.")
        print("2. Change camera_index from 0 to 1.")
        print("3. Check Windows camera permission.")
        return

    actual_width, actual_height = cam.get_actual_resolution()
    print(f"Actual camera resolution: {actual_width} x {actual_height}")

    previous_time = time.time()
    fps_display = 0

    print("\nCamera window opened.")
    print("Press 'q' or ESC to quit.")
    print("=" * 60)

    while True:
        success, frame = cam.read()

        if not success:
            print("Failed to read frame from camera.")
            break

        # FPS calculation
        current_time = time.time()
        elapsed_time = current_time - previous_time

        if elapsed_time > 0:
            fps_display = int(1 / elapsed_time)

        previous_time = current_time

        # Draw info on camera frame
        cv2.putText(
            frame,
            f"FPS: {fps_display}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            "Press Q or ESC to quit",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        cv2.imshow("Air Pointer - Camera Feed Test", frame)

        key = cv2.waitKey(1) & 0xFF

        # q key or ESC key
        if key == ord("q") or key == 27:
            break

    cam.release()
    cv2.destroyAllWindows()

    print("Camera feed test closed successfully.")


if __name__ == "__main__":
    main()