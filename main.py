# ============================================================
# main.py — Air Pointer & Presentation Controller
# GUI + Pinned Video + Overlay + Pinch-to-Close Marking
# ============================================================

import os, sys, time, math, traceback, cv2
from PyQt5.QtWidgets import QApplication

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.core.camera import CameraFeed
from src.core.hand_tracker import HandTracker
from src.core.pointer import PointerMapper
from src.gestures.finger_state import FingerStateDetector
from src.gestures.static_gestures import GestureRecognizer
from src.gestures.swipe_detector import SwipeDetector
from src.gestures.area_marker import AreaMarker
from src.overlay.highlight_manager import HighlightManager
from src.overlay.presentation_overlay import PresentationOverlay
from src.gui.control_panel import ControlPanel, PinnedVideoFeed


# ============================================================
# CONFIGURATION
# ============================================================
CONFIG = {
    "camera_index": 0,
    "camera_width": 1280,
    "camera_height": 720,
    "stability_frames": 3,
    "pointer_margin": 0.25,
    "pointer_smoothing": 0.45,
    "swipe_window": 0.40,
    "swipe_min_displacement": 0.18,
    "swipe_cooldown": 0.90,
    "pin_radius": 0.08,
    "pinch_threshold": 40,
    "highlight_fade": 0.0,
    "highlight_dim": 0.30,
    "overlay_screen_index": 0,
    "overlay_dim_alpha": 155,
    "mouse_control": True,
    "keyboard_control": True,
    "video_feed_corner": "bottom-right",
    "video_feed_width": 320,
    "video_feed_height": 240,
}

PALM_IDS = [0, 5, 9, 13, 17]

SWIPE_LABELS = {
    "NEXT_SLIDE":         ("NEXT SLIDE >>>",     (0, 255, 0)),
    "PREV_SLIDE":         ("<<< PREV SLIDE",     (0, 200, 255)),
    "START_PRESENTATION": ("START SHOW",          (255, 255, 0)),
    "END_PRESENTATION":   ("END SHOW",            (0, 0, 255)),
}


def fire_key(action):
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0
    keymap = {
        "NEXT_SLIDE": "pagedown",
        "PREV_SLIDE": "pageup",
        "START_PRESENTATION": "f5",
        "END_PRESENTATION": "escape",
    }
    key = keymap.get(action)
    if key:
        pyautogui.press(key)
        print(f"  Key: {action} -> {key}", flush=True)


def main():
    print("=" * 60, flush=True)
    print("  AIR POINTER — Presentation Controller", flush=True)
    print("=" * 60, flush=True)

    # ---- PyQt5 App ----
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # ---- GUI ----
    print("[1/9] Control Panel...", flush=True)
    panel = ControlPanel(CONFIG)

    print("[2/9] Pinned Video Feed...", flush=True)
    video_feed = PinnedVideoFeed(
        width=CONFIG["video_feed_width"],
        height=CONFIG["video_feed_height"],
        corner=CONFIG["video_feed_corner"]
    )

    # ---- Modules ----
    print("[3/9] Camera...", flush=True)
    cam = CameraFeed(
        camera_index=CONFIG["camera_index"],
        width=CONFIG["camera_width"],
        height=CONFIG["camera_height"],
        fps=30
    )

    print("[4/9] Hand tracker...", flush=True)
    tracker = HandTracker(max_hands=1)

    print("[5/9] Finger detector...", flush=True)
    detector = FingerStateDetector()

    print("[6/9] Gesture recognizer...", flush=True)
    recognizer = GestureRecognizer(stability_frames=CONFIG["stability_frames"])

    print("[7/9] Starting camera...", flush=True)
    try:
        cam.start()
    except RuntimeError as e:
        print(f"  Camera failed: {e}", flush=True)
        return
    fw, fh = cam.get_actual_resolution()
    print(f"  Camera: {fw}x{fh}", flush=True)

    print("[8/9] Pointer + Swipe + Marker...", flush=True)
    pointer = PointerMapper(
        frame_width=fw, frame_height=fh,
        margin=CONFIG["pointer_margin"],
        smoothing=CONFIG["pointer_smoothing"]
    )
    swipe = SwipeDetector(
        window=CONFIG["swipe_window"],
        min_displacement=CONFIG["swipe_min_displacement"],
        cooldown=CONFIG["swipe_cooldown"]
    )
    marker = AreaMarker(
        pinch_threshold=CONFIG["pinch_threshold"]
    )
    highlighter = HighlightManager(
        fade_duration=CONFIG["highlight_fade"],
        dim_factor=CONFIG["highlight_dim"]
    )

    print("[9/9] Presentation overlay...", flush=True)
    overlay = PresentationOverlay(
        screen_index=CONFIG["overlay_screen_index"],
        dim_alpha=CONFIG["overlay_dim_alpha"]
    )

    # ---- Runtime state ----
    mouse_on = CONFIG["mouse_control"]
    keyboard_on = CONFIG["keyboard_control"]
    show_region = True
    running = True
    tracking_active = True
    swipe_trail = []
    banner = ""
    banner_color = (255, 255, 255)
    banner_until = 0.0

    # ---- Connect GUI signals ----
    def on_start():
        nonlocal tracking_active
        tracking_active = True
        print("  Tracking started.", flush=True)

    def on_stop():
        nonlocal tracking_active
        tracking_active = False
        overlay.set_pointer(visible=False)
        overlay.set_marker(pin=None, trail=[], state="IDLE")
        overlay.clear_highlights()
        highlighter.clear()
        marker.reset()
        print("  Tracking stopped.", flush=True)

    def on_quit():
        nonlocal running
        running = False

    def on_mouse(v):
        nonlocal mouse_on
        mouse_on = v

    def on_keyboard(v):
        nonlocal keyboard_on
        keyboard_on = v

    def on_region(v):
        nonlocal show_region
        show_region = v

    def on_smoothing(v):
        pointer.smoothing = v

    def on_sensitivity(v):
        swipe.min_displacement = v

    def on_pinch(v):
        marker.pinch_threshold = v

    def on_clear():
        highlighter.clear()
        overlay.clear_highlights()

    def on_flip():
        swipe.invert_horizontal = not swipe.invert_horizontal
        print(f"  Swipe inverted: {swipe.invert_horizontal}", flush=True)

    def on_camera_visibility(visible):
        if visible:
            video_feed.show_feed()
        else:
            video_feed.hide_feed()

    def on_camera_size(w, h):
        video_feed.resize_feed(w, h)

    def on_camera_corner(corner):
        video_feed.set_corner(corner)

    def on_camera_opacity(opacity):
        video_feed.set_opacity(opacity)

    panel.signals.start_clicked.connect(on_start)
    panel.signals.stop_clicked.connect(on_stop)
    panel.signals.quit_clicked.connect(on_quit)
    panel.signals.mouse_toggled.connect(on_mouse)
    panel.signals.keyboard_toggled.connect(on_keyboard)
    panel.signals.region_toggled.connect(on_region)
    panel.signals.smoothing_changed.connect(on_smoothing)
    panel.signals.sensitivity_changed.connect(on_sensitivity)
    panel.signals.pinch_changed.connect(on_pinch)
    panel.signals.clear_highlights.connect(on_clear)
    panel.signals.flip_swipe.connect(on_flip)
    panel.signals.camera_visibility_changed.connect(on_camera_visibility)
    panel.signals.camera_size_changed.connect(on_camera_size)
    panel.signals.camera_corner_changed.connect(on_camera_corner)
    panel.signals.camera_opacity_changed.connect(on_camera_opacity)

    panel._on_start()

    print("=" * 60, flush=True)
    print("  GESTURES:", flush=True)
    print("    Point       = Air pointer", flush=True)
    print("    Open palm   = Swipe L/R for slides", flush=True)
    print("    Pinch       = Start marking area", flush=True)
    print("    Draw + Pinch = Complete highlight", flush=True)
    print("    Middle pinch = Cancel marking", flush=True)
    print("    Peace (1s)  = Clear highlights", flush=True)
    print("    Fist        = Idle", flush=True)
    print("  KEYS: m=mouse k=keys c=clear d=flip q=quit", flush=True)
    print("=" * 60, flush=True)

    # ============================================================
    # MAIN LOOP
    # ============================================================
    while running:
        success, frame = cam.read()
        if not success:
            break

        command, gesture = "NONE", "NONE"
        screen_pos = None
        marker_state = "IDLE"

        if tracking_active:
            frame, landmarks_list = tracker.process(frame)
            hand_detected = len(landmarks_list) > 0

            if hand_detected:
                landmarks = landmarks_list[0]
                finger_states, _, _ = detector.detect_finger_states(landmarks)
                result = recognizer.update(finger_states)
                command = result["command"]
                gesture = result["gesture"]

                tip = landmarks[8]
                tip_x, tip_y = tip["x"], tip["y"]

                # ========================================
                # ACTION 1: AIR POINTER
                # ========================================
                if command == "POINTER":
                    sx, sy = pointer.map(tip_x, tip_y)
                    screen_pos = (int(sx), int(sy))
                    overlay.set_pointer(sx, sy, visible=True)
                    if mouse_on:
                        pointer.move_mouse(sx, sy)
                    cv2.circle(frame, (tip_x, tip_y), 12, (0, 255, 0), -1)
                    cv2.circle(frame, (tip_x, tip_y), 18, (0, 255, 0), 2)
                    swipe_trail.clear()

                # ========================================
                # ACTION 2: SWIPE
                # ========================================
                elif command == "NAVIGATE":
                    cx = sum(landmarks[i]["x"] for i in PALM_IDS) / len(PALM_IDS)
                    cy = sum(landmarks[i]["y"] for i in PALM_IDS) / len(PALM_IDS)
                    nx, ny = cx / fw, cy / fh
                    event = swipe.update(nx, ny, tracking_active=True)
                    swipe_trail.append((int(cx), int(cy)))
                    if len(swipe_trail) > 25:
                        swipe_trail.pop(0)
                    cv2.circle(frame, (int(cx), int(cy)), 10, (255, 165, 0), -1)
                    if event:
                        action = swipe.get_action(event)
                        label, col = SWIPE_LABELS.get(action, (action, (255, 255, 255)))
                        banner = label
                        banner_color = col
                        banner_until = time.time() + 0.9
                        if keyboard_on:
                            fire_key(action)
                    pointer.reset()

                # Hide pointer when not pointing
                if command != "POINTER":
                    overlay.set_pointer(visible=False)

                # Disable swipe when not navigating
                if command != "NAVIGATE":
                    swipe.update(0, 0, tracking_active=False)

                # ========================================
                # ACTION 3: AREA HIGHLIGHT (pinch workflow)
                # ========================================
                mark_result = marker.update(landmarks, finger_states, command, fw, fh)

                if mark_result:
                    pts_px = mark_result["points_px"]
                    highlighter.add_freeform(pts_px, color=(0, 255, 255))
                    pts_screen = [pointer.map_raw(x, y) for x, y in pts_px]
                    overlay.add_freeform_highlight(pts_screen, color=(0, 255, 255))
                    banner = "AREA HIGHLIGHTED!"
                    banner_color = (0, 255, 255)
                    banner_until = time.time() + 1.2

                # ========================================
                # CLEAR HIGHLIGHTS (peace hold)
                # ========================================
                if command == "CLEAR_HIGHLIGHT" and result["active"]:
                    if recognizer.get_held_duration() > 1.0:
                        highlighter.clear()
                        overlay.clear_highlights()
                        banner = "CLEARED"
                        banner_color = (200, 200, 200)
                        banner_until = time.time() + 0.8

            else:
                # No hand
                recognizer.reset()
                marker.reset()
                swipe.update(0, 0, tracking_active=False)
                swipe_trail.clear()
                pointer.reset()
                overlay.set_pointer(visible=False)
                overlay.set_marker(pin=None, trail=[], state="IDLE")

        # ============================================
        # DRAW CAMERA PREVIEW OVERLAYS
        # ============================================

        # Pointer region
        if show_region and command == "POINTER":
            x1, y1, x2, y2 = pointer.get_region()
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 1)

        # Swipe trail
        for i in range(1, len(swipe_trail)):
            thick = max(1, int(8 * i / len(swipe_trail)))
            cv2.line(frame, swipe_trail[i-1], swipe_trail[i], (255, 165, 0), thick)

        # Marker state + pin + trail
        marker_state = marker.get_state()
        pin = marker.get_pin_px()
        draw_trail = marker.get_trail_px()

        pin_screen = None
        trail_screen = []

        # Draw pin on camera preview
        if pin:
            pin_screen = pointer.map_raw(pin[0], pin[1])
            pulse = int(4 * abs(math.sin(time.time() * 4)))
            cv2.circle(frame, (int(pin[0]), int(pin[1])), 16 + pulse, (0, 0, 255), 3)
            cv2.circle(frame, (int(pin[0]), int(pin[1])), 4, (0, 0, 255), -1)
            cv2.putText(frame, "PIN", (int(pin[0]) + 20, int(pin[1]) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # Draw trail on camera preview
        if draw_trail:
            trail_screen = [pointer.map_raw(p[0], p[1]) for p in draw_trail]
            for i in range(1, len(draw_trail)):
                alpha = i / len(draw_trail)
                col = (0, int(255 * alpha), int(255 * (1 - alpha)))
                thick = max(2, int(6 * alpha))
                p1 = (int(draw_trail[i-1][0]), int(draw_trail[i-1][1]))
                p2 = (int(draw_trail[i][0]), int(draw_trail[i][1]))
                cv2.line(frame, p1, p2, col, thick)

        # Guide line (trail end -> pin)
        if pin and draw_trail and marker_state == "DRAWING":
            last = (int(draw_trail[-1][0]), int(draw_trail[-1][1]))
            pin_pt = (int(pin[0]), int(pin[1]))
            cv2.line(frame, last, pin_pt, (100, 100, 255), 1, cv2.LINE_AA)

        # Send marker to overlay
        overlay.set_marker(pin=pin_screen, trail=trail_screen, state=marker_state)

        # Apply spotlight on camera preview
        frame = highlighter.draw(frame)

        # Swipe cooldown bar
        swipe_rem = swipe.cooldown_remaining()
        if command == "NAVIGATE":
            frac = 1.0 - (swipe_rem / swipe.cooldown) if swipe.cooldown > 0 else 1.0
            bc = (0, 255, 0) if swipe_rem <= 0 else (0, 100, 255)
            cv2.rectangle(frame, (20, 240), (170, 258), (60, 60, 60), 2)
            cv2.rectangle(frame, (20, 240), (20 + int(150 * frac), 258), bc, -1)

        # ============================================
        # HUD on camera preview
        # ============================================
        mc_map = {
            "POINTER": (0, 255, 0), "NAVIGATE": (255, 165, 0),
            "IDLE": (128, 128, 128), "CLEAR_HIGHLIGHT": (200, 200, 0),
        }
        mc = mc_map.get(command, (200, 200, 200))
        cv2.putText(frame, f"{gesture} | {command}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, mc, 2)

        if screen_pos:
            cv2.putText(frame, f"Cursor: {screen_pos}", (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        # Marker status hint
        if marker_state == "DRAWING":
            progress = marker.get_progress()
            hint = f"Drawing... ({int(progress * 100)}%) — pinch to close"
            cv2.putText(frame, hint, (20, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
        elif marker_state == "IDLE" and highlighter.count() > 0:
            cv2.putText(frame, f"Highlights: {highlighter.count()}", (20, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # Banner
        if time.time() < banner_until and banner:
            (tw, th), _ = cv2.getTextSize(banner, cv2.FONT_HERSHEY_SIMPLEX, 2.0, 5)
            bx = (frame.shape[1] - tw) // 2
            by = frame.shape[0] // 2
            cv2.putText(frame, banner, (bx, by),
                        cv2.FONT_HERSHEY_SIMPLEX, 2.0, banner_color, 5)

        # ============================================
        # UPDATE GUI + OVERLAY
        # ============================================
        video_feed.update_frame(frame)
        video_feed.update_status(
            f"{gesture} | {command}",
            "lime" if command == "POINTER" else
            "orange" if command == "NAVIGATE" else "gray"
        )
        panel.update_status(
            gesture=gesture,
            command=command,
            highlights=highlighter.count(),
            marker_state=marker_state
        )

        overlay.process_events()
        app.processEvents()
        cv2.waitKey(1)

    # ============================================
    # CLEANUP
    # ============================================
    overlay.close_overlay()
    video_feed.close()
    panel.close()
    cam.release()
    cv2.destroyAllWindows()
    print("\nAir Pointer closed. Goodbye!", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\n!!! ERROR !!!", flush=True)
        traceback.print_exc()
        input("\nPress ENTER to exit...")