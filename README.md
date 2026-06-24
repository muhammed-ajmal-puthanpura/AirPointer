# 🖐️ Air Pointer — Gesture-Based Presentation Controller

Air Pointer is a computer-vision-powered presentation controller that allows users to control presentations using natural hand gestures captured through a webcam.

It enables seamless slide navigation, air pointer control, and free-form area highlighting without requiring any physical clicker or presentation remote.

Designed for educators, presenters, trainers, and public speakers, Air Pointer works with PowerPoint, Google Slides, PDF viewers, and most keyboard-controlled presentation software.

---

## ✨ Features

### 🎯 Air Pointer Control

Move a virtual pointer on the screen using your index finger.

### ⏭️ Slide Navigation

Navigate between slides using intuitive swipe gestures.

### 🖍️ Free-Form Highlighting

Draw around any region of the slide and highlight it in real time.

### 🪟 Transparent Presentation Overlay

Displays pointer, drawing trails, and highlighted regions above presentations without interfering with slide interaction.

### 📷 Pinned Camera Feed

Always-on-top webcam preview that can be resized, repositioned, and adjusted for transparency.

### ⚙️ Control Panel

Manage gesture settings, tracking controls, sensitivity, overlay options, and camera feed preferences.

---

## 🎬 Demo Features

| Feature            | Gesture                   | Action                     |
| ------------------ | ------------------------- | -------------------------- |
| Air Pointer        | Index Finger Up           | Move pointer on screen     |
| Next Slide         | Open Palm Swipe Right     | Move to next slide         |
| Previous Slide     | Open Palm Swipe Left      | Move to previous slide     |
| Start Highlight    | Thumb + Index Pinch       | Begin marking area         |
| Draw Highlight     | Move Index Finger         | Draw free-form boundary    |
| Complete Highlight | Thumb + Index Pinch Again | Create highlighted region  |
| Cancel Marking     | Thumb + Middle Pinch      | Cancel current marking     |
| Clear Highlights   | Peace Sign Hold           | Remove all highlights      |
| Idle Mode          | Fist                      | Disable accidental actions |

---

## 🖥️ Application Components

Air Pointer consists of three main windows:

### 1. Control Panel

Used to:

* Start/stop gesture tracking
* Enable or disable mouse control
* Enable or disable keyboard slide control
* Adjust gesture sensitivity
* Manage camera feed settings
* Clear highlights

### 2. Pinned Camera Feed

Features:

* Always-on-top webcam preview
* Adjustable opacity
* Resizable window
* Corner positioning
* Show/Hide support

### 3. Presentation Overlay

A transparent click-through overlay displayed above presentations.

Shows:

* Air pointer
* Drawing trail
* Pin markers
* Highlighted regions

---

## 📂 Project Structure

```text
AirPointer/
│
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
├── air_pointer.spec
├── installer.nsi
│
├── src/
│   ├── core/
│   │   ├── camera.py
│   │   ├── hand_tracker.py
│   │   └── pointer.py
│   │
│   ├── gestures/
│   │   ├── finger_state.py
│   │   ├── static_gestures.py
│   │   ├── swipe_detector.py
│   │   └── area_marker.py
│   │
│   ├── overlay/
│   │   ├── highlight_manager.py
│   │   └── presentation_overlay.py
│   │
│   └── gui/
│       └── control_panel.py
│
├── assets/
│   └── icon.ico
│
├── hooks/
│   ├── hook-mediapipe.py
│   └── runtime_hook.py
│
└── tests/
    ├── test_camera_feed.py
    ├── test_hand_detection.py
    ├── test_finger_state.py
    ├── test_swipe.py
    └── test_circle_highlight.py
```

---

## 🛠️ Technologies Used

| Category             | Technology               |
| -------------------- | ------------------------ |
| Programming Language | Python                   |
| Computer Vision      | OpenCV                   |
| Hand Tracking        | MediaPipe                |
| GUI Framework        | PyQt5                    |
| Screen Overlay       | PyQt5 Transparent Window |
| Input Automation     | PyAutoGUI                |
| Packaging            | PyInstaller              |
| Installer Creation   | NSIS                     |

---

## 📋 Requirements

### Recommended Environment

| Setting              | Recommendation             |
| -------------------- | -------------------------- |
| Operating System     | Windows 10 / Windows 11    |
| Python Version       | Python 3.8+                |
| Camera               | 720p Webcam or Better      |
| Lighting             | Bright and Even            |
| Distance from Camera | 50–100 cm                  |
| Background           | Plain Background Preferred |

### Supported Presentation Software

* Microsoft PowerPoint
* Google Slides
* PDF Presentation Viewers
* Any keyboard-controlled presentation software

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/air-pointer.git
cd air-pointer
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python main.py
```

---

## 🎮 Usage

### Recommended Workflow

1. Open your presentation.
2. Launch Air Pointer.

```bash
python main.py
```

3. Start slideshow mode.
4. Enable desired controls from the control panel.
5. Use gestures to interact with your presentation.

---

## ✋ Gesture Guide

### Air Pointer Mode

Raise only your index finger.

```text
Index Finger Up
```

Result:

```text
Pointer becomes active
```

---

### Slide Navigation

Perform an open-palm swipe.

```text
Swipe Right  → Next Slide
Swipe Left   → Previous Slide
```

> Keyboard Control must be enabled.

---

### Free-Form Highlighting

#### Start Marking

```text
Thumb + Index Pinch
```

#### Draw Region

```text
Move Index Finger
```

#### Complete Highlight

```text
Thumb + Index Pinch Again
```

#### Cancel Marking

```text
Thumb + Middle Pinch
```

#### Clear All Highlights

```text
Peace Sign Hold
```

---

## ⚙️ GUI Features

### Controls

* Start / Stop Tracking
* Mouse Control Toggle
* Keyboard Control Toggle
* Camera Feed Toggle
* Overlay Toggle
* Clear Highlights

### Camera Feed Options

* Show / Hide
* Resize
* Reposition
* Opacity Adjustment

### Adjustable Parameters

* Pointer Smoothing
* Swipe Sensitivity
* Pinch Threshold
* Pointer Region
* Swipe Direction

---

## 📦 Building the Executable

### Using PyInstaller

```bash
pyinstaller air_pointer.spec --clean --noconfirm
```

Output:

```text
dist/AirPointer/AirPointer.exe
```

### Single File Build

```bash
pyinstaller air_pointer.spec --clean --noconfirm
```

Output:

```text
dist/AirPointer.exe
```

---

## 🖥️ Creating a Windows Installer

Install NSIS:

https://nsis.sourceforge.io/Download

Build installer:

```bash
"C:\Program Files (x86)\NSIS\makensis.exe" installer.nsi
```

Output:

```text
AirPointerSetup.exe
```

---

## 📝 Overlay Notes

The presentation overlay is implemented as a transparent always-on-top PyQt5 window.

If the overlay does not appear:

* Verify the correct monitor is selected.
* Adjust `overlay_screen_index` in `main.py`.
* Run Python with administrator privileges if PowerPoint is running as Administrator.
* Use windowed slideshow mode if fullscreen blocks overlays.

---

## ⚠️ Known Limitations

* Gesture accuracy depends on lighting conditions.
* Fast hand movement may reduce tracking stability.
* Some fullscreen applications may block overlays.
* Antivirus software may flag unsigned executables.
* One-file builds may have slower startup times.

---

## 🛣️ Roadmap

Future improvements include:

* Multi-monitor overlay selection
* Gesture calibration wizard
* User profile save/load support
* Voice command integration
* Annotation tools with multiple colors
* Presentation analytics
* OBS Studio integration
* Zoom / Teams integration

---

## 📄 License

This project is currently released for educational and personal use.

You may choose a license such as:

* MIT License
* Apache License 2.0
* GPLv3
* Proprietary License

---

## 🙌 Acknowledgements

Special thanks to the open-source tools that power this project:

* MediaPipe
* OpenCV
* PyQt5
* PyInstaller
* NSIS

---

## 👨‍💻 Author

**Muhammed Ajmal P P**

Computer Science Engineering Student
College of Engineering Thalassery

GitHub: https://github.com/muhammed-ajmal-puthanpura

---

⭐ If you found this project useful, consider giving it a star on GitHub.
