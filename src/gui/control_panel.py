# ============================================================
# control_panel.py
# PyQt5 GUI: Control Panel + Pinned Camera Feed
# With camera visibility, size, corner, opacity, drag
# ============================================================

import sys
import os
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QSlider, QGroupBox, QFrame,
    QSizePolicy, QComboBox, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QImage, QPixmap, QFont, QIcon


class Signals(QObject):
    """Signals for communication between GUI and main loop."""
    start_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    quit_clicked = pyqtSignal()
    clear_highlights = pyqtSignal()
    flip_swipe = pyqtSignal()

    mouse_toggled = pyqtSignal(bool)
    keyboard_toggled = pyqtSignal(bool)
    region_toggled = pyqtSignal(bool)

    smoothing_changed = pyqtSignal(float)
    sensitivity_changed = pyqtSignal(float)
    pinch_changed = pyqtSignal(int)

    camera_visibility_changed = pyqtSignal(bool)
    camera_size_changed = pyqtSignal(int, int)
    camera_corner_changed = pyqtSignal(str)
    camera_opacity_changed = pyqtSignal(float)


class PinnedVideoFeed(QWidget):
    """
    Small always-on-top camera feed window pinned to screen corner.
    Supports show/hide, resize, corner change, opacity, and drag.
    """
    def __init__(self, width=320, height=240, corner="bottom-right", opacity=1.0):
        super().__init__()

        self.feed_width = width
        self.feed_height = height
        self.corner = corner
        self._dragging = False
        self._drag_pos = None
        self._custom_position = False

        self.setWindowTitle("Camera Feed")
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFixedSize(width, height)
        self.setWindowOpacity(opacity)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.image_label = QLabel()
        self.image_label.setFixedSize(width, height)
        self.image_label.setStyleSheet("background-color: black;")
        self.image_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.image_label)

        self.status_label = QLabel("IDLE", self)
        self.status_label.setStyleSheet(
            "color: white; background-color: rgba(0,0,0,150); "
            "padding: 4px 8px; border-radius: 4px; font-size: 11px;"
        )
        self.status_label.move(5, 5)

        self.close_btn = QPushButton("✕", self)
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setStyleSheet(
            "QPushButton { background-color: rgba(255,0,0,150); color: white; "
            "border: none; border-radius: 12px; font-size: 14px; font-weight: bold; }"
            "QPushButton:hover { background-color: rgba(255,0,0,220); }"
        )
        self.close_btn.move(width - 30, 5)
        self.close_btn.clicked.connect(self.hide)
        self.close_btn.setCursor(Qt.PointingHandCursor)

        self._position_corner()
        self.show()

    def _position_corner(self):
        if self._custom_position:
            return
        app = QApplication.instance()
        if app is None:
            return
        screen = app.primaryScreen()
        geo = screen.availableGeometry()
        margin = 10
        positions = {
            "bottom-right": (
                geo.x() + geo.width() - self.feed_width - margin,
                geo.y() + geo.height() - self.feed_height - margin
            ),
            "bottom-left": (
                geo.x() + margin,
                geo.y() + geo.height() - self.feed_height - margin
            ),
            "top-right": (
                geo.x() + geo.width() - self.feed_width - margin,
                geo.y() + margin
            ),
            "top-left": (
                geo.x() + margin,
                geo.y() + margin
            ),
        }
        x, y = positions.get(self.corner, positions["bottom-right"])
        self.move(x, y)

    def resize_feed(self, width, height):
        self.feed_width = width
        self.feed_height = height
        self.setFixedSize(width, height)
        self.image_label.setFixedSize(width, height)
        self.close_btn.move(width - 30, 5)
        self._custom_position = False
        self._position_corner()

    def set_corner(self, corner):
        self.corner = corner
        self._custom_position = False
        self._position_corner()

    def set_opacity(self, opacity):
        self.setWindowOpacity(max(0.1, min(1.0, opacity)))

    def show_feed(self):
        self.show()
        self.raise_()

    def hide_feed(self):
        self.hide()

    def update_frame(self, frame):
        if frame is None or not self.isVisible():
            return
        small = cv2.resize(frame, (self.feed_width, self.feed_height))
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(q_img))

    def update_status(self, text, color="white"):
        if not self.isVisible():
            return
        self.status_label.setText(text)
        self.status_label.setStyleSheet(
            f"color: {color}; background-color: rgba(0,0,0,150); "
            f"padding: 4px 8px; border-radius: 4px; font-size: 11px;"
        )
        self.status_label.adjustSize()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            self._custom_position = True
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self._drag_pos = None


class ControlPanel(QMainWindow):
    """
    Main control panel window with settings, status, and camera controls.
    """
    def __init__(self, config):
        super().__init__()

        self.config = config
        self.signals = Signals()
        self.is_running = False

        self.setWindowTitle("Air Pointer — Controller")
        self.setFixedWidth(380)
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.WindowCloseButtonHint |
            Qt.WindowMinimizeButtonHint
        )

        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2e; }
            QLabel { color: #cdd6f4; font-size: 13px; }
            QPushButton {
                background-color: #45475a; color: #cdd6f4;
                border: 1px solid #585b70; border-radius: 6px;
                padding: 8px 16px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #585b70; }
            QPushButton:pressed { background-color: #6c7086; }
            QPushButton#startBtn { background-color: #a6e3a1; color: #1e1e2e; }
            QPushButton#stopBtn { background-color: #f38ba8; color: #1e1e2e; }
            QPushButton#quitBtn { background-color: #f38ba8; color: #1e1e2e; }
            QPushButton#clearBtn { background-color: #89b4fa; color: #1e1e2e; }
            QCheckBox { color: #cdd6f4; font-size: 13px; spacing: 8px; }
            QCheckBox::indicator { width: 18px; height: 18px; }
            QGroupBox {
                color: #89b4fa; border: 1px solid #45475a;
                border-radius: 8px; margin-top: 12px;
                padding-top: 16px; font-size: 13px; font-weight: bold;
            }
            QSlider::groove:horizontal {
                height: 6px; background: #45475a; border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #89b4fa; width: 16px; height: 16px;
                margin: -5px 0; border-radius: 8px;
            }
            QSlider::sub-page:horizontal { background: #89b4fa; border-radius: 3px; }
            QComboBox {
                background-color: #45475a; color: #cdd6f4;
                border: 1px solid #585b70; border-radius: 4px;
                padding: 4px 8px; font-size: 12px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #313244; color: #cdd6f4;
                selection-background-color: #585b70;
            }
            QSpinBox {
                background-color: #45475a; color: #cdd6f4;
                border: 1px solid #585b70; border-radius: 4px;
                padding: 4px; font-size: 12px;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(6)
        layout.setContentsMargins(12, 12, 12, 12)

        # ---- Title ----
        title = QLabel("AIR POINTER")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #89b4fa; margin-bottom: 2px;")
        layout.addWidget(title)

        subtitle = QLabel("Presentation Controller")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #6c7086; font-size: 11px; margin-bottom: 6px;")
        layout.addWidget(subtitle)

        # ---- Start / Stop ----
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶  Start")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self._on_start)
        btn_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹  Stop")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # ---- Controls Group ----
        controls_group = QGroupBox("Controls")
        controls_layout = QVBoxLayout()

        self.mouse_cb = QCheckBox("Mouse Control")
        self.mouse_cb.setChecked(config["mouse_control"])
        self.mouse_cb.toggled.connect(lambda v: self.signals.mouse_toggled.emit(v))
        controls_layout.addWidget(self.mouse_cb)

        self.keyboard_cb = QCheckBox("Keyboard Control (Slides)")
        self.keyboard_cb.setChecked(config["keyboard_control"])
        self.keyboard_cb.toggled.connect(lambda v: self.signals.keyboard_toggled.emit(v))
        controls_layout.addWidget(self.keyboard_cb)

        self.region_cb = QCheckBox("Show Pointer Region")
        self.region_cb.setChecked(True)
        self.region_cb.toggled.connect(lambda v: self.signals.region_toggled.emit(v))
        controls_layout.addWidget(self.region_cb)

        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # ---- Camera Feed Group ----
        camera_group = QGroupBox("Camera Feed")
        camera_layout = QVBoxLayout()

        self.camera_visible_cb = QCheckBox("Show Camera Feed")
        self.camera_visible_cb.setChecked(True)
        self.camera_visible_cb.toggled.connect(self._on_camera_visibility)
        camera_layout.addWidget(self.camera_visible_cb)

        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Size:"))
        self.size_combo = QComboBox()
        self.size_combo.addItems([
            "Tiny (200x150)", "Small (280x210)", "Medium (320x240)",
            "Large (400x300)", "XL (480x360)", "Custom"
        ])
        self.size_combo.setCurrentIndex(2)
        self.size_combo.currentIndexChanged.connect(self._on_size_preset)
        size_row.addWidget(self.size_combo)
        camera_layout.addLayout(size_row)

        self.custom_size_widget = QWidget()
        custom_layout = QHBoxLayout(self.custom_size_widget)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.addWidget(QLabel("W:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(120, 800)
        self.width_spin.setValue(config.get("video_feed_width", 320))
        self.width_spin.setSingleStep(20)
        custom_layout.addWidget(self.width_spin)
        custom_layout.addWidget(QLabel("H:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(90, 600)
        self.height_spin.setValue(config.get("video_feed_height", 240))
        self.height_spin.setSingleStep(15)
        custom_layout.addWidget(self.height_spin)
        self.apply_size_btn = QPushButton("Apply")
        self.apply_size_btn.setFixedWidth(60)
        self.apply_size_btn.clicked.connect(self._on_custom_size)
        custom_layout.addWidget(self.apply_size_btn)
        self.custom_size_widget.setVisible(False)
        camera_layout.addWidget(self.custom_size_widget)

        corner_row = QHBoxLayout()
        corner_row.addWidget(QLabel("Position:"))
        self.corner_combo = QComboBox()
        self.corner_combo.addItems([
            "Bottom Right", "Bottom Left", "Top Right", "Top Left"
        ])
        self.corner_combo.setCurrentIndex(0)
        self.corner_combo.currentIndexChanged.connect(self._on_corner_change)
        corner_row.addWidget(self.corner_combo)
        camera_layout.addLayout(corner_row)

        opacity_row = QHBoxLayout()
        opacity_row.addWidget(QLabel("Opacity:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self._on_opacity)
        opacity_row.addWidget(self.opacity_slider)
        self.opacity_label = QLabel("100%")
        self.opacity_label.setFixedWidth(40)
        opacity_row.addWidget(self.opacity_label)
        camera_layout.addLayout(opacity_row)

        drag_hint = QLabel("Drag the camera feed to reposition freely")
        drag_hint.setStyleSheet("color: #6c7086; font-size: 10px; font-style: italic;")
        camera_layout.addWidget(drag_hint)

        camera_group.setLayout(camera_layout)
        layout.addWidget(camera_group)

        # ---- Sensitivity Group ----
        sens_group = QGroupBox("Sensitivity")
        sens_layout = QVBoxLayout()

        sens_layout.addWidget(QLabel("Pointer Smoothing"))
        sh = QHBoxLayout()
        self.smooth_slider = QSlider(Qt.Horizontal)
        self.smooth_slider.setRange(5, 95)
        self.smooth_slider.setValue(int(config["pointer_smoothing"] * 100))
        self.smooth_label = QLabel(f"{config['pointer_smoothing']:.2f}")
        self.smooth_label.setFixedWidth(35)
        self.smooth_slider.valueChanged.connect(self._on_smoothing)
        sh.addWidget(self.smooth_slider)
        sh.addWidget(self.smooth_label)
        sens_layout.addLayout(sh)

        sens_layout.addWidget(QLabel("Swipe Sensitivity"))
        ssh = QHBoxLayout()
        self.swipe_slider = QSlider(Qt.Horizontal)
        self.swipe_slider.setRange(8, 35)
        self.swipe_slider.setValue(int(config["swipe_min_displacement"] * 100))
        self.swipe_label = QLabel(f"{config['swipe_min_displacement']:.2f}")
        self.swipe_label.setFixedWidth(35)
        self.swipe_slider.valueChanged.connect(self._on_sensitivity)
        ssh.addWidget(self.swipe_slider)
        ssh.addWidget(self.swipe_label)
        sens_layout.addLayout(ssh)

        sens_layout.addWidget(QLabel("Pinch Distance"))
        ph = QHBoxLayout()
        self.pinch_slider = QSlider(Qt.Horizontal)
        self.pinch_slider.setRange(20, 80)
        self.pinch_slider.setValue(config["pinch_threshold"])
        self.pinch_label = QLabel(f"{config['pinch_threshold']}px")
        self.pinch_label.setFixedWidth(40)
        self.pinch_slider.valueChanged.connect(self._on_pinch)
        ph.addWidget(self.pinch_slider)
        ph.addWidget(self.pinch_label)
        sens_layout.addLayout(ph)

        sens_group.setLayout(sens_layout)
        layout.addWidget(sens_group)

        # ---- Status Group ----
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()

        self.gesture_label = QLabel("Gesture: —")
        self.gesture_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        status_layout.addWidget(self.gesture_label)

        self.command_label = QLabel("Command: —")
        status_layout.addWidget(self.command_label)

        self.highlight_label = QLabel("Highlights: 0")
        status_layout.addWidget(self.highlight_label)

        self.marker_label = QLabel("Marker: IDLE")
        status_layout.addWidget(self.marker_label)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # ---- Action Buttons ----
        self.clear_btn = QPushButton("Clear All Highlights")
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.clicked.connect(lambda: self.signals.clear_highlights.emit())
        layout.addWidget(self.clear_btn)

        self.flip_btn = QPushButton("Flip Swipe Direction")
        self.flip_btn.clicked.connect(lambda: self.signals.flip_swipe.emit())
        layout.addWidget(self.flip_btn)

        layout.addStretch()

        self.quit_btn = QPushButton("✕  Quit")
        self.quit_btn.setObjectName("quitBtn")
        self.quit_btn.clicked.connect(lambda: self.signals.quit_clicked.emit())
        layout.addWidget(self.quit_btn)

        self.adjustSize()
        self.show()

    # ---- Camera callbacks ----
    def _on_camera_visibility(self, visible):
        self.signals.camera_visibility_changed.emit(visible)

    def _on_size_preset(self, index):
        presets = {0: (200, 150), 1: (280, 210), 2: (320, 240), 3: (400, 300), 4: (480, 360)}
        if index == 5:
            self.custom_size_widget.setVisible(True)
            return
        self.custom_size_widget.setVisible(False)
        w, h = presets.get(index, (320, 240))
        self.width_spin.setValue(w)
        self.height_spin.setValue(h)
        self.signals.camera_size_changed.emit(w, h)

    def _on_custom_size(self):
        self.signals.camera_size_changed.emit(self.width_spin.value(), self.height_spin.value())

    def _on_corner_change(self, index):
        corners = ["bottom-right", "bottom-left", "top-right", "top-left"]
        self.signals.camera_corner_changed.emit(corners[index] if index < len(corners) else "bottom-right")

    def _on_opacity(self, value):
        self.opacity_label.setText(f"{value}%")
        self.signals.camera_opacity_changed.emit(value / 100.0)

    # ---- Other callbacks ----
    def _on_start(self):
        self.is_running = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.signals.start_clicked.emit()

    def _on_stop(self):
        self.is_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.signals.stop_clicked.emit()

    def _on_smoothing(self, value):
        v = value / 100.0
        self.smooth_label.setText(f"{v:.2f}")
        self.signals.smoothing_changed.emit(v)

    def _on_sensitivity(self, value):
        v = value / 100.0
        self.swipe_label.setText(f"{v:.2f}")
        self.signals.sensitivity_changed.emit(v)

    def _on_pinch(self, value):
        self.pinch_label.setText(f"{value}px")
        self.signals.pinch_changed.emit(value)

    # ---- Public update ----
    def update_status(self, gesture="—", command="—", highlights=0, marker_state="IDLE"):
        color_map = {
            "POINTER": "#a6e3a1", "NAVIGATE": "#fab387",
            "IDLE": "#6c7086", "CLEAR_HIGHLIGHT": "#f9e2af", "NONE": "#6c7086",
        }
        color = color_map.get(command, "#cdd6f4")
        self.gesture_label.setText(f"Gesture: {gesture}")
        self.gesture_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
        self.command_label.setText(f"Command: {command}")
        self.command_label.setStyleSheet(f"color: {color};")
        self.highlight_label.setText(f"Highlights: {highlights}")
        self.marker_label.setText(f"Marker: {marker_state}")

    def closeEvent(self, event):
        self.signals.quit_clicked.emit()
        event.accept()