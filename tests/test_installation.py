# ============================================================
# TEST INSTALLATION — Air Pointer Project
# Run this to verify all dependencies are installed correctly
# ============================================================

import sys

def test_imports():
    print("=" * 50)
    print("  Air Pointer — Installation Test")
    print("=" * 50)
    
    libraries = {
        "OpenCV"     : "cv2",
        "MediaPipe"  : "mediapipe",
        "PyAutoGUI"  : "pyautogui",
        "Pynput"     : "pynput",
        "NumPy"      : "numpy",
        "Pillow"     : "PIL",
        "PyQt5"      : "PyQt5",
        "Screeninfo" : "screeninfo",
        "Keyboard"   : "keyboard",
    }
    
    all_passed = True
    
    for name, module in libraries.items():
        try:
            __import__(module)
            print(f"  ✅  {name:<15} installed successfully")
        except ImportError as e:
            print(f"  ❌  {name:<15} FAILED — {e}")
            all_passed = False
    
    print("=" * 50)
    
    # Check Python version
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"  ✅  Python {version.major}.{version.minor}.{version.micro} — Compatible")
    else:
        print(f"  ❌  Python {version.major}.{version.minor} — Too old! Upgrade to 3.8+")
        all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("  🎉  ALL CHECKS PASSED! Ready to build!")
    else:
        print("  ⚠️   SOME CHECKS FAILED! Fix errors above.")
    
    print("=" * 50)


def test_versions():
    print("\n  📦  Library Versions:")
    print("-" * 50)
    
    import cv2
    import mediapipe
    import numpy
    import PIL
    import PyQt5.QtCore
    
    print(f"  OpenCV    : {cv2.__version__}")
    print(f"  MediaPipe : {mediapipe.__version__}")
    print(f"  NumPy     : {numpy.__version__}")
    print(f"  Pillow    : {PIL.__version__}")
    print(f"  PyQt5     : {PyQt5.QtCore.PYQT_VERSION_STR}")
    print("-" * 50)


def test_camera():
    print("\n  📷  Camera Test:")
    print("-" * 50)
    
    import cv2
    cap = cv2.VideoCapture(0)
    
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            h, w, c = frame.shape
            print(f"  ✅  Camera detected!")
            print(f"  ✅  Resolution : {w} x {h}")
            print(f"  ✅  Channels   : {c}")
        else:
            print("  ❌  Camera found but cannot read frames")
    else:
        print("  ❌  No camera detected! Connect a webcam.")
    
    cap.release()
    print("-" * 50)


if __name__ == "__main__":
    test_imports()
    test_versions()
    test_camera()
    print("\n  ✅  Step 1 Complete! Ready for Step 2.\n")