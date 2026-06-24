# ============================================================
# presentation_overlay.py
# Transparent always-on-top overlay for presentation slides
# Draws pointer, pin, trails, and free-form highlights on screen
# ============================================================

import sys
import os
import time
import ctypes

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QPolygonF


class PresentationOverlay(QWidget):
    def __init__(self, screen_index=0, dim_alpha=155):
        """
        screen_index:
            Which monitor to draw overlay on.

        dim_alpha:
            Darkness outside highlighted region.
            0   = no dimming
            255 = fully black
        """

        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)

        super().__init__()

        self.dim_alpha = dim_alpha

        self.highlights = []      # list of free-form polygons in screen coords
        self.pointer = None       # {"x": ..., "y": ...}
        self.marker_pin = None    # (x, y)
        self.marker_trail = []    # [(x, y), ...]
        self.marker_state = "IDLE"

        # ---------------- Window flags ----------------
        flags = (
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )

        # Makes overlay ignore mouse/keyboard input if supported
        try:
            flags |= Qt.WindowTransparentForInput
        except Exception:
            pass

        self.setWindowFlags(flags)

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        # ---------------- Screen geometry ----------------
        screens = self.app.screens()
        if screen_index < len(screens):
            screen = screens[screen_index]
        else:
            screen = self.app.primaryScreen()

        geo = screen.geometry()
        self.offset_x = geo.x()
        self.offset_y = geo.y()
        self.setGeometry(geo)

        self.show()
        self.raise_()

        self._enable_click_through_windows()

        print(
            f">>> PresentationOverlay LOADED | "
            f"screen={screen_index} geometry={geo.width()}x{geo.height()} "
            f"offset=({self.offset_x},{self.offset_y})",
            flush=True
        )

    # ========================================================
    # Windows click-through support
    # ========================================================
    def _enable_click_through_windows(self):
        if os.name != "nt":
            return

        try:
            hwnd = int(self.winId())

            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_TOOLWINDOW = 0x00000080

            user32 = ctypes.windll.user32
            ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

            user32.SetWindowLongW(
                hwnd,
                GWL_EXSTYLE,
                ex_style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW
            )
        except Exception as e:
            print("Overlay click-through warning:", e, flush=True)

    # ========================================================
    # Coordinate helpers
    # ========================================================
    def _local_point(self, x, y):
        """
        Convert global screen coordinate to overlay-local coordinate.
        """
        return QPointF(float(x) - self.offset_x, float(y) - self.offset_y)

    def _qcolor(self, color, alpha=255):
        return QColor(int(color[0]), int(color[1]), int(color[2]), int(alpha))

    # ========================================================
    # Public update methods
    # ========================================================
    def set_pointer(self, x=None, y=None, visible=True):
        if not visible or x is None or y is None:
            self.pointer = None
        else:
            self.pointer = {"x": float(x), "y": float(y)}

        self.update()

    def set_marker(self, pin=None, trail=None, state="IDLE"):
        self.marker_pin = pin
        self.marker_trail = trail or []
        self.marker_state = state
        self.update()

    def add_freeform_highlight(self, points, color=(0, 255, 255), ttl=None):
        """
        Add free-form highlight.

        points:
            List of screen coordinates [(x, y), ...]
        """
        if not points or len(points) < 3:
            return

        self.highlights.append({
            "points": [(float(x), float(y)) for x, y in points],
            "color": color,
            "created_at": time.time(),
            "ttl": ttl,
        })

        print(f"Overlay highlight added: {len(points)} points", flush=True)
        self.update()

    def clear_highlights(self):
        self.highlights.clear()
        self.update()
        print("Overlay highlights cleared.", flush=True)

    def process_events(self):
        """
        Call this every frame from OpenCV loop.
        """
        self.update()
        self.app.processEvents()

    def close_overlay(self):
        self.close()
        self.app.processEvents()

    # ========================================================
    # Paint overlay
    # ========================================================
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        now = time.time()

        # Remove expired highlights
        self.highlights = [
            h for h in self.highlights
            if h["ttl"] is None or (now - h["created_at"]) < h["ttl"]
        ]

        # ====================================================
        # Draw spotlight highlights
        # ====================================================
        if self.highlights:
            # Dim full screen
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, self.dim_alpha))
            painter.drawRect(self.rect())

            # Cut transparent holes for highlight regions
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            for h in self.highlights:
                poly = QPolygonF([
                    self._local_point(x, y)
                    for x, y in h["points"]
                ])
                painter.drawPolygon(poly)

            # Draw highlight borders
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setBrush(Qt.NoBrush)

            for h in self.highlights:
                color = h["color"]
                poly = QPolygonF([
                    self._local_point(x, y)
                    for x, y in h["points"]
                ])

                # Glow border
                painter.setPen(QPen(self._qcolor(color, 110), 9))
                painter.drawPolygon(poly)

                # Sharp border
                painter.setPen(QPen(self._qcolor(color, 255), 3))
                painter.drawPolygon(poly)

        # ====================================================
        # Draw marker trail
        # ====================================================
        if len(self.marker_trail) > 1:
            for i in range(1, len(self.marker_trail)):
                alpha = i / len(self.marker_trail)

                p1 = self._local_point(
                    self.marker_trail[i - 1][0],
                    self.marker_trail[i - 1][1]
                )
                p2 = self._local_point(
                    self.marker_trail[i][0],
                    self.marker_trail[i][1]
                )

                pen = QPen(QColor(0, int(255 * alpha), 255, 220), max(2, int(6 * alpha)))
                painter.setPen(pen)
                painter.drawLine(p1, p2)

        # ====================================================
        # Draw pin
        # ====================================================
        if self.marker_pin is not None:
            x, y = self.marker_pin
            p = self._local_point(x, y)

            pulse = int(5 * abs(__import__("math").sin(time.time() * 4)))

            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(255, 0, 0, 240), 3))
            painter.drawEllipse(p, 18 + pulse, 18 + pulse)

            painter.setBrush(QColor(255, 0, 0, 240))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(p, 5, 5)

        # ====================================================
        # Draw pointer
        # ====================================================
        if self.pointer is not None:
            p = self._local_point(self.pointer["x"], self.pointer["y"])

            # Glow
            painter.setBrush(QColor(0, 255, 0, 70))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(p, 22, 22)

            # Main dot
            painter.setBrush(QColor(0, 255, 0, 230))
            painter.drawEllipse(p, 8, 8)

            # Border
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(255, 255, 255, 230), 2))
            painter.drawEllipse(p, 10, 10)

        painter.end()