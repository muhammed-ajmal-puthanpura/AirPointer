# ============================================================
# pointer_overlay.py
# Transparent overlay window showing pointer dot
# ============================================================

import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush


class PointerOverlay(QWidget):
    def __init__(self):
        super().__init__()

        # Get screen size
        screen = QApplication.primaryScreen().geometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()

        # Window settings
        self.setGeometry(0, 0, self.screen_width, self.screen_height)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # Click-through!

        # Pointer position
        self.pointer_x = self.screen_width // 2
        self.pointer_y = self.screen_height // 2
        self.pointer_visible = False

        # Pointer settings
        self.pointer_radius = 12
        self.pointer_color = QColor(255, 50, 50, 220)  # Red with alpha
        self.outer_radius = 24
        self.outer_color = QColor(255, 50, 50, 80)     # Lighter outer ring

        # Update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # ~60 FPS

    def set_pointer_position(self, x, y):
        """Update pointer position."""
        self.pointer_x = x
        self.pointer_y = y

    def show_pointer(self):
        """Show the pointer."""
        self.pointer_visible = True
        self.show()

    def hide_pointer(self):
        """Hide the pointer."""
        self.pointer_visible = False
        self.hide()

    def paintEvent(self, event):
        """Draw the pointer dot."""
        if not self.pointer_visible:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw outer glow ring
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.outer_color))
        painter.drawEllipse(
            self.pointer_x - self.outer_radius,
            self.pointer_y - self.outer_radius,
            self.outer_radius * 2,
            self.outer_radius * 2
        )

        # Draw inner dot
        painter.setBrush(QBrush(self.pointer_color))
        painter.drawEllipse(
            self.pointer_x - self.pointer_radius,
            self.pointer_y - self.pointer_radius,
            self.pointer_radius * 2,
            self.pointer_radius * 2
        )

        painter.end()