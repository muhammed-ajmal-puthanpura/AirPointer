# ============================================================
# hook-mediapipe.py
# Ensures MediaPipe + all its dependencies are included
# ============================================================

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all mediapipe data files (models, configs)
datas = collect_data_files("mediapipe", include_py_files=True)

# Collect all mediapipe submodules
hiddenimports = collect_submodules("mediapipe")

# Add matplotlib which mediapipe drawing_utils needs
hiddenimports += [
    "matplotlib",
    "matplotlib.pyplot",
    "matplotlib.backends",
    "matplotlib.backends.backend_agg",
]