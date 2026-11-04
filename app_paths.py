"""Portable project and PyInstaller directory paths (Windows)."""
import sys
from pathlib import Path

FROZEN = bool(getattr(sys, "frozen", False))
APP_ROOT = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent
RESOURCE_ROOT = Path(getattr(sys, "_MEIPASS", APP_ROOT)) if FROZEN else APP_ROOT
VENDOR_PYTHON = APP_ROOT / "vendor" / "python"

def prepare_local_imports():
    """Use project-managed Python dependencies when developing from source."""
    if not FROZEN and VENDOR_PYTHON.is_dir():
        vendor = str(VENDOR_PYTHON)
        if vendor not in sys.path:
            sys.path.insert(0, vendor)
        # pywin32 uses pyd/win32 alongside top-level packages.
        for folder in ("win32", "win32/lib", "Pythonwin", "pywin32_system32"):
            path = VENDOR_PYTHON / folder
            if path.is_dir() and str(path) not in sys.path:
                sys.path.insert(1, str(path))
