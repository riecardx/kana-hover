"""Per-user Windows startup registration (no admin required)."""
import sys
import winreg
from pathlib import Path
from app_paths import APP_ROOT, FROZEN

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE = "KanaHover"

def command_line():
    if FROZEN:
        return '"' + str(Path(sys.executable).resolve()) + '"'
    executable = Path(sys.executable).resolve()
    pythonw = executable.with_name("pythonw.exe")
    if pythonw.is_file():
        executable = pythonw
    return '"' + str(executable) + '" "' + str(APP_ROOT / "main.py") + '"'

def startup_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
            value = winreg.QueryValueEx(key, RUN_VALUE)[0]
            return value == command_line()
    except FileNotFoundError:
        return False

def set_startup(enabled):
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, RUN_VALUE, 0, winreg.REG_SZ, command_line())
        else:
            try:
                winreg.DeleteValue(key, RUN_VALUE)
            except FileNotFoundError:
                pass

def toggle_startup():
    set_startup(not startup_enabled())
