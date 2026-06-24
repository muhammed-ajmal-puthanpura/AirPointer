# ============================================================
# test_swipe.py
# Swipe-to-change-slides test (gated on OPEN PALM / NAVIGATE)
# ============================================================
import os, sys, time, traceback, cv2,inspect

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from src.core.camera import CameraFeed
from src.core.hand_tracker import HandTracker
from src.gestures.finger_state import FingerStateDetector
from src.gestures.static_gestures import GestureRecognizer
from src.gestures.swipe_detector import SwipeDetector


# Palm-center landmark IDs (wrist + 4 finger bases)
PALM_IDS = [0, 5, 9, 13, 17]

ACTION_LABELS = {
    "NEXT_SLIDE":         ("⏭️  NEXT SLIDE",      (0, 255, 0)),
    "PREV_SLIDE":         ("⏮️  PREVIOUS SLIDE",  (0, 200, 255)),
    "START_PRESENTATION": ("▶️  START SHOW",       (255, 255, 0)),
    "END_PRESENTATION":   ("⏹️  END / BLACK",      (0, 0, 255)),
    "NONE":               ("",                    (255, 255, 255)),
}


def fire_keyboard(action):
    """Lazy-import pyautogui and press the matching key."""
    import pyautogui
    pyautogui.FAILSAFE = False
    keymap = {
        "NEXT_SLIDE":         "right",
        "PREV_SLIDE":         "left",
        "START_PRESENTATION": "f5",
        "END_PRESENTATION":   "esc",
    }
    key = keymap.get(action)
    if key:
        pyautogui.press(key)


def main():
    print("=" * 60, flush=True)
    print("Air Pointer - SWIPE TEST", flush=True)
    print("=" * 60, flush=True)

    cam = CameraFeed(camera_index=0, width=1280, height=720, fps=30)
    tracker = HandTracker(max_hands=1)
    def make_detector():
        sig = inspect.signature(FingerStateDetector.__init__).parameters
        kwargs = {}
        if "angle_threshold" in sig:
            kwargs["angle_threshold"] = 160
        if "thumb_factor" in sig:
            kwargs["thumb_factor"] = 1.0
        if "thumb_inverted" in sig:
            kwargs["thumb_inverted"] = True
        return FingerStateDetector(**kwargs)

    detector = make_detector()
    recognizer = GestureRecognizer(stability_frames=4)
    swipe = SwipeDetector(window=0.40, min_displacement=0.18,
                          dominance_ratio=1.4, cooldown=0.90,
                          invert_horizontal=False)

    try:
        cam.start()
    except RuntimeError as e:
        print("Camera failed:", e, flush=True)
        return

    fw, fh = cam.get_actual_resolution()

    keyboard_on = False          # press 'k' to fire REAL arrow keys
    trail = []                   # recent palm-center pixels for the trail
    banner = ("", (255, 255, 255))
    banner_until = 0.0

    print("✋ Open palm + swipe RIGHT = next | LEFT = prev | UP = start | DOWN = end", flush=True)
    print("Controls:  k=toggle real keyboard  d=flip direction  q=quit", flush=True)
    print(f"Real keyboard: {'ON' if keyboard_on else 'OFF (preview)'}", flush=True)

    while True:
        success, frame = cam.read()
        if not success:
            break

        frame, landmarks_list = tracker.process(frame)
        command, gesture = "NONE", "NONE"

        if len(landmarks_list) > 0:
            landmarks = landmarks_list[0]
            finger_states, _, _ = detector.detect_finger_states(landmarks)
            result = recognizer.update(finger_states)
            command = result["command"]
            gesture = result["gesture"]

            # ---- Palm center (normalized) ----
            cx = sum(landmarks[i]["x"] for i in PALM_IDS) / len(PALM_IDS)
            cy = sum(landmarks[i]["y"] for i in PALM_IDS) / len(PALM_IDS)
            nx, ny = cx / fw, cy / fh

            # ---- Update swipe ONLY while in NAVIGATE (open palm) ----
            navigating = (command == "NAVIGATE")
            event = swipe.update(nx, ny, tracking_active=navigating)

            # Trail (only while navigating, keeps it clean)
            if navigating:
                trail.append((int(cx), int(cy)))
                if len(trail) > 25:
                    trail.pop(0)
            else:
                trail.clear()

            # Draw palm center
            pc_col = (0, 255, 0) if navigating else (0, 165, 255)
            cv2.circle(frame, (int(cx), int(cy)), 10, pc_col, -1)

            # Handle a detected swipe
            if event:
                action = swipe.get_action(event)
                label, col = ACTION_LABELS.get(action, (action, (255, 255, 255)))
                print(f">>> {event}  ->  {action}", flush=True)
                if keyboard_on:
                    fire_keyboard(action)
                banner = (label, col)
                banner_until = time.time() + 0.9   # show banner ~0.9s
        else:
            recognizer.reset()
            swipe.reset()
            trail.clear()

        # ---- Draw motion trail ----
        for i in range(1, len(trail)):
            thickness = max(1, int(8 * i / len(trail)))
            cv2.line(frame, trail[i - 1], trail[i], (255, 255, 0), thickness)

        # ---- Cooldown bar ----
        rem = swipe.cooldown_remaining()
        frac = 1.0 - (rem / swipe.cooldown) if swipe.cooldown > 0 else 1.0
        bar_col = (0, 255, 0) if rem <= 0 else (0, 100, 255)
        cv2.rectangle(frame, (20, 200), (320, 225), (80, 80, 80), 2)
        cv2.rectangle(frame, (20, 200), (20 + int(300 * frac), 225), bar_col, -1)
        cv2.putText(frame, "Swipe ready" if rem <= 0 else f"Cooldown {rem:.1f}s",
                    (20, 195), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # ---- HUD ----
        hcol = (0, 255, 0) if command == "NAVIGATE" else (200, 200, 200)
        cv2.putText(frame, f"Gesture: {gesture}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, hcol, 2)
        cv2.putText(frame, f"Command: {command}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, hcol, 2)
        cv2.putText(frame, "(open palm + swipe to change slides)", (20, 115),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)

        ktxt = "KEYBOARD: ON (fires real arrows!)" if keyboard_on else "KEYBOARD: OFF (preview) - press k"
        cv2.putText(frame, ktxt, (20, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (0, 0, 255) if keyboard_on else (0, 255, 255), 2)

        # ---- Big swipe banner ----
        if time.time() < banner_until and banner[0]:
            txt, col = banner
            (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, 2.0, 5)
            cv2.putText(frame, txt, ((frame.shape[1] - tw) // 2, frame.shape[0] // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 2.0, col, 5)

        cv2.imshow("Air Pointer - Swipe Test", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:
            break
        elif key == ord("k"):
            keyboard_on = not keyboard_on
            print(f"Real keyboard: {'ON' if keyboard_on else 'OFF'}", flush=True)
        elif key == ord("d"):
            swipe.invert_horizontal = not swipe.invert_horizontal
            print(f"Horizontal inverted: {swipe.invert_horizontal}", flush=True)

    cam.release()
    cv2.destroyAllWindows()
    print("Closed.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\n!!! ERROR !!!", flush=True)
        traceback.print_exc()
        input("\nPress ENTER to exit...")