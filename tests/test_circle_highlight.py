# ============================================================
# test_circle_highlight.py  (v4 — pin-based area marking)
# ============================================================
import os, sys, time, traceback, cv2

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from src.core.camera import CameraFeed
from src.core.hand_tracker import HandTracker
from src.gestures.finger_state import FingerStateDetector
from src.gestures.static_gestures import GestureRecognizer
from src.gestures.area_marker import AreaMarker
from src.overlay.highlight_manager import HighlightManager


def main():
    print("=" * 60, flush=True)
    print("Air Pointer - Pin-Based Highlight (v4)", flush=True)
    print("=" * 60, flush=True)

    cam = CameraFeed(camera_index=0, width=1280, height=720, fps=30)
    tracker = HandTracker(max_hands=1)
    detector = FingerStateDetector()
    recognizer = GestureRecognizer(stability_frames=3)
    marker = AreaMarker(
        pin_radius=0.08,
        min_points=10,
        min_dimension=0.02,
        cooldown=1.0,
        pinch_threshold=40
    )
    highlighter = HighlightManager(fade_duration=0.0, dim_factor=0.30)

    try:
        cam.start()
    except RuntimeError as e:
        print("Camera failed:", e, flush=True)
        return

    fw, fh = cam.get_actual_resolution()
    banner = ""
    banner_until = 0.0

    print("HOW TO USE:", flush=True)
    print("  1. 🤏 PINCH (thumb+index touch) = drop a pin 📍", flush=True)
    print("  2. 👆 POINT (index up) = draw around the area", flush=True)
    print("  3. Bring finger BACK to the pin = HIGHLIGHTED! 🔦", flush=True)
    print("  ✌️  PEACE (hold 1s) = clear highlights", flush=True)
    print("  c = clear | q = quit", flush=True)
    print("=" * 60, flush=True)

    while True:
        success, frame = cam.read()
        if not success:
            break

        frame, landmarks_list = tracker.process(frame)
        command, gesture = "NONE", "NONE"
        hand_detected = len(landmarks_list) > 0

        if hand_detected:
            landmarks = landmarks_list[0]
            finger_states, _, _ = detector.detect_finger_states(landmarks)
            result = recognizer.update(finger_states)
            command = result["command"]
            gesture = result["gesture"]

            # Update marker with all needed info
            mark_result = marker.update(landmarks, finger_states, command, fw, fh)

            if mark_result:
                pts_px = mark_result["points_px"]
                highlighter.add_freeform(pts_px, color=(0, 255, 255))
                banner = "AREA HIGHLIGHTED!"
                banner_until = time.time() + 1.5

            # Clear on PEACE hold
            if command == "CLEAR_HIGHLIGHT" and result["active"]:
                if recognizer.get_held_duration() > 1.0 and highlighter.count() > 0:
                    highlighter.clear()
                    banner = "CLEARED"
                    banner_until = time.time() + 0.8

            # Draw fingertip
            tip = landmarks[8]
            tip_col = (0, 255, 0) if command == "POINTER" else (0, 165, 255)
            cv2.circle(frame, (tip["x"], tip["y"]), 10, tip_col, -1)
        else:
            recognizer.reset()
            marker.reset()

        # ---- Draw pin marker ----
        state = marker.get_state()
        pin = marker.get_pin_px()
        trail = marker.get_trail_px()

        if pin:
            # Draw pin as a pulsing target
            pulse = int(5 * abs(math.sin(time.time() * 4)))  # ← need math import
            cv2.circle(frame, (int(pin[0]), int(pin[1])), 18 + pulse, (0, 0, 255), 3)
            cv2.circle(frame, (int(pin[0]), int(pin[1])), 5, (0, 0, 255), -1)
            cv2.putText(frame, "PIN", (int(pin[0]) + 22, int(pin[1]) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # ---- Draw trail ----
        if len(trail) > 1:
            for i in range(1, len(trail)):
                alpha = i / len(trail)
                col = (0, int(255 * alpha), int(255 * (1 - alpha)))
                thick = max(2, int(6 * alpha))
                p1 = (int(trail[i-1][0]), int(trail[i-1][1]))
                p2 = (int(trail[i][0]), int(trail[i][1]))
                cv2.line(frame, p1, p2, col, thick)

        # ---- Draw line from current tip to pin (closing guide) ----
        if pin and trail and state == "DRAWING":
            last_pt = (int(trail[-1][0]), int(trail[-1][1]))
            pin_pt = (int(pin[0]), int(pin[1]))
            # Dashed guide line
            cv2.line(frame, last_pt, pin_pt, (100, 100, 255), 1, cv2.LINE_AA)

        # Apply spotlight
        frame = highlighter.draw(frame)

        # ---- Progress bar ----
        progress = marker.get_progress()
        bar_w = 300
        bar_x, bar_y = 20, 200
        cv2.rectangle(frame, (bar_x, bar_y),
                      (bar_x + bar_w, bar_y + 25), (80, 80, 80), 2)
        fill = int(bar_w * progress)
        bar_col = (0, int(255 * progress), int(255 * (1 - progress)))
        cv2.rectangle(frame, (bar_x, bar_y),
                      (bar_x + fill, bar_y + 25), bar_col, -1)

        # State-based label
        if state == "IDLE":
            label = "Pinch to drop a pin"
        elif state == "PIN_SET":
            label = "Pin set! Point to start drawing"
        elif state == "DRAWING":
            if progress > 0.7:
                label = "Almost there! Return to pin!"
            else:
                label = f"Drawing... return to pin ({int(progress*100)}%)"
        else:
            label = ""
        cv2.putText(frame, label, (bar_x, bar_y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # ---- HUD ----
        hcol = (0, 255, 0) if command == "POINTER" else (200, 200, 200)
        cv2.putText(frame, f"Gesture: {gesture}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, hcol, 2)
        cv2.putText(frame, f"Command: {command}", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, hcol, 2)
        cv2.putText(frame, f"State: {state}", (20, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 200, 0), 2)
        cv2.putText(frame, f"Highlights: {highlighter.count()}", (20, 155),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

        cv2.putText(frame, "pinch=pin | point+draw+return=highlight | peace=clear",
                    (20, frame.shape[0] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 180, 180), 1)

        # ---- Banner ----
        if time.time() < banner_until and banner:
            (tw, th), _ = cv2.getTextSize(banner,
                                          cv2.FONT_HERSHEY_SIMPLEX, 2.0, 5)
            bx = (frame.shape[1] - tw) // 2
            by = frame.shape[0] // 2
            cv2.putText(frame, banner, (bx, by),
                        cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 255, 255), 5)

        cv2.imshow("Air Pointer - Pin Based Highlight", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:
            break
        elif key == ord("c"):
            highlighter.clear()

    cam.release()
    cv2.destroyAllWindows()
    print("Closed.", flush=True)


if __name__ == "__main__":
    try:
        import math   # needed for pin pulse animation
        main()
    except Exception:
        print("\n!!! ERROR !!!", flush=True)
        traceback.print_exc()
        input("\nPress ENTER to exit...")