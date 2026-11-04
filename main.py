"""KanaHover v0.7.1 - offline Windows Japanese reading helper."""
import ctypes
import json
import logging
import os
import queue
import re
import sys
import threading
import time
import tkinter as tk
from ctypes import wintypes
from pathlib import Path

from app_paths import APP_ROOT, prepare_local_imports
prepare_local_imports()

import pystray
from PIL import Image, ImageDraw
from sudachipy import dictionary, tokenizer
import uiautomation as auto
from ocr_feature import OCRFeature
from speech_feature import OpenJTalkSpeaker
from startup_feature import startup_enabled, toggle_startup

ROOT = APP_ROOT
LOGFILE = ROOT / "kana-hover.log"
logging.basicConfig(filename=LOGFILE, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("kana-hover")
JAPANESE = re.compile(r"[\u3400-\u9fff\u3040-\u30ff]")
KANJI = re.compile(r"[\u3400-\u9fff]")
KATA = re.compile(r"[\u30a1-\u30f6]")
VALID = {"chrome.exe", "msedge.exe", "notepad.exe", "emeditor.exe", "excel.exe", "wps.exe", "et.exe", "wpp.exe"}
DIC = dictionary.Dictionary().create()
MODE = tokenizer.Tokenizer.SplitMode.C
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

def pointer():
    p = POINT()
    user32.GetCursorPos(ctypes.byref(p))
    return p.x, p.y

def process_name(control):
    try:
        pid = control.ProcessId
        if not pid:
            return ""
        import win32api, win32con, win32process
        handle = win32api.OpenProcess(win32con.PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        try:
            return win32process.GetModuleFileNameEx(handle, 0).split("\\")[-1].lower()
        finally:
            win32api.CloseHandle(handle)
    except Exception:
        try:
            import psutil
            return psutil.Process(control.ProcessId).name().lower()
        except Exception:
            return ""

def hiragana(text):
    return KATA.sub(lambda m: chr(ord(m.group()) - 0x60), text)

def tokenize_japanese(text):
    """Prefer dictionary readings; text is limited to the focused word or short line."""
    if not text or len(text) > 220 or not JAPANESE.search(text):
        return None
    try:
        words = DIC.tokenize(text, MODE)
        candidates = []
        for m in words:
            surface = m.surface()
            if not KANJI.search(surface):
                continue
            reading = m.reading_form()
            if reading and reading != surface and reading != "*":
                candidates.append((surface, hiragana(reading)))
        return candidates
    except Exception:
        logger.exception("dictionary error")
        return None

def word_reading(text):
    if not text:
        return None
    text = str(text).strip().replace("\\r", " ").replace("\\n", " ")
    if len(text) > 140 or not JAPANESE.search(text):
        return None
    if KANJI.search(text):
        parts = tokenize_japanese(text)
        if not parts:
            return None
        if len(parts) == 1 and text == parts[0][0]:
            return parts[0]
        # For explicitly selected phrases, render each word reading in order.
        try:
            readings = []
            for m in DIC.tokenize(text, MODE):
                reading = m.reading_form()
                readings.append(hiragana(reading) if reading and reading != "*" else m.surface())
            return text, "".join(readings)
        except Exception:
            return None
    if KATA.search(text):
        return text, hiragana(text)
    return None

def app_name(control):
    cur = control
    for _ in range(12):
        if not cur:
            break
        app = process_name(cur)
        if app in VALID:
            return app
        try:
            cur = cur.GetParentControl()
        except Exception:
            break
    return ""

def selection_from_uia():
    try:
        ctrl = auto.GetFocusedControl()
        if not ctrl or app_name(ctrl) not in VALID:
            return None
        current = ctrl
        for _ in range(10):
            if not current:
                break
            try:
                pat = current.GetPattern(auto.PatternId.TextPattern)
                if pat:
                    chunks = [r.GetText(200) for r in pat.GetSelection()]
                    selected = "".join(chunks).strip()
                    if selected and len(selected) <= 140:
                        return selected
            except Exception:
                pass
            try:
                current = current.GetParentControl()
            except Exception:
                break
    except Exception:
        logger.exception("UIA selection read")
    return None


def foreground_app():
    try:
        import win32gui, win32process, psutil
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return ""
        pid = win32process.GetWindowThreadProcessId(hwnd)[1]
        return psutil.Process(pid).name().lower()
    except Exception:
        return ""

def selected_reading():
    # Only actual selected text from the focused text control.
    if foreground_app() not in VALID:
        return None
    selected = selection_from_uia()
    return word_reading(selected)

def clipboard_selected_reading():
    # Triggered only after drag-select or double-click, never from an idle poll.
    # Restore the original clipboard IDataObject rather than flattening formats.
    import pythoncom, win32clipboard, win32api, win32con
    if foreground_app() not in VALID:
        return None
    old_clipboard = None
    try:
        old_clipboard = pythoncom.OleGetClipboard()
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
        finally:
            win32clipboard.CloseClipboard()
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        win32api.keybd_event(ord("C"), 0, 0, 0)
        win32api.keybd_event(ord("C"), 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.09)
        win32clipboard.OpenClipboard()
        try:
            # Excel whole-cell copy advertises Excel clipboard formats. Reject it.
            names = []
            fmt = 0
            while True:
                fmt = win32clipboard.EnumClipboardFormats(fmt)
                if not fmt:
                    break
                if fmt >= 0xC000:
                    try:
                        names.append(win32clipboard.GetClipboardFormatName(fmt).lower())
                    except Exception:
                        pass
            if foreground_app() == "excel.exe" and any(
                "biff" in x or "xml spreadsheet" in x or "excel" in x
                for x in names
            ):
                return None
            # WPS Sheets: a copied cell is NOT a text selection.
            # Reject spreadsheet clipboard signatures, while retaining WPS Writer text selections.
            if foreground_app() in {"wps.exe", "et.exe", "wpp.exe"} and any(
                "biff" in x or "spreadsheet" in x or "worksheet" in x
                or "et.sheet" in x or "et_sheet" in x
                for x in names
            ):
                return None
            text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT) if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT) else None
        finally:
            win32clipboard.CloseClipboard()
        return word_reading(text)
    except Exception:
        logger.exception("clipboard selection fallback failed")
        return None
    finally:
        if old_clipboard is not None:
            try:
                pythoncom.OleSetClipboard(old_clipboard)
            except Exception:
                logger.exception("clipboard restore failed")

def tray_image():
    img = Image.new("RGBA", (64, 64), (33, 91, 132, 255))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((4, 4, 59, 59), radius=13, fill=(39, 119, 163))
    draw.ellipse((13, 11, 51, 49), fill="white")
    draw.line((22, 51, 42, 51), fill="white", width=5)
    return img

class HoverApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        # Popup must accept mouse/keyboard input for text selection and Ctrl+C.
        self.root.configure(bg="#1678c2")
        self.label = tk.Text(self.root, bg="#fcfcf7", fg="#1c3550",
                             padx=16, pady=9, font=("Yu Gothic UI", 18, "bold"),
                             width=24, height=2, wrap="word", undo=False,
                             borderwidth=0, highlightthickness=0,
                             selectbackground="#8dbbf1", selectforeground="#111111",
                             cursor="xterm", exportselection=False)
        self.label.pack(side="left", padx=(3, 0), pady=3)
        self.speaker_button = tk.Button(self.root, text="🔊", command=self.toggle_speech,
                                        font=("Segoe UI Emoji", 15), cursor="hand2",
                                        padx=4, pady=1, relief="flat", bg="#fcfcf7",
                                        activebackground="#dbedff", takefocus=False)
        self.speaker_button.pack(side="right", padx=(0, 3), pady=3, fill="y")
        self.label.bind("<Control-c>", self.copy_popup_selection)
        self.label.bind("<Control-C>", self.copy_popup_selection)
        # Explicitly clicking popup text may focus it for Ctrl+C; showing it must not.
        self.label.bind("<ButtonPress-1>", self.allow_popup_focus, add="+")
        self.root.withdraw()
        self.running = threading.Event()
        self.running.set()
        self.paused = False
        self.capture_active = False
        self.messages = queue.Queue()
        self.last_position = None
        self.last_value = None
        self.popup_bounds = None
        self.popup_opened_at = 0.0
        self._popup_mouse_down = False
        self.root.after(35, self.watch_popup_click)
        self.tray = pystray.Icon("KanaHover", tray_image(), "KanaHover v0.7.1", menu=pystray.Menu(
            pystray.MenuItem(self.pause_menu_text, self.toggle),
            pystray.MenuItem("Start with Windows", self.toggle_windows_startup,
                             checked=lambda item: startup_enabled()),
            pystray.MenuItem("Test Popup", self.test_popup),
            pystray.MenuItem("OCR Shortcut...", self.configure_ocr_shortcut),
            pystray.MenuItem("Voice Speed", pystray.Menu(
                pystray.MenuItem("0.8x", lambda icon, item: self.speech.set_speed(0.8),
                                 checked=lambda item: self.speech.speed == 0.8, radio=True),
                pystray.MenuItem("1.0x", lambda icon, item: self.speech.set_speed(1.0),
                                 checked=lambda item: self.speech.speed == 1.0, radio=True),
                pystray.MenuItem("1.2x", lambda icon, item: self.speech.set_speed(1.2),
                                 checked=lambda item: self.speech.speed == 1.2, radio=True))),
            pystray.MenuItem("Restart", self.restart),
            pystray.MenuItem("Exit", self.exit)))
        self.ocr = OCRFeature(self, word_reading, pointer)
        self.speech = OpenJTalkSpeaker(self)
        self.root.after(80, self.consume)
        threading.Thread(target=self.scan, daemon=True).start()
        threading.Thread(target=self.tray.run, daemon=True).start()

    def test_popup(self, *_):
        x, y = pointer()
        self.messages.put((x, y, ("KanaHover", "TEST OK")))

    def test_popup(self, *_):
        x, y = pointer()
        self.messages.put((x, y, ("KanaHover", "TEST OK")))

    def toggle_speech(self):
        if self.last_value:
            self.speech.toggle(self.last_value[0])

    def set_speaker_playing(self, playing):
        self.speaker_button.configure(text="■" if playing else "🔊")

    def popup_hwnd(self):
        import win32gui
        import win32con
        return win32gui.GetAncestor(self.root.winfo_id(), win32con.GA_ROOT)

    def prevent_popup_activation(self):
        import win32gui
        import win32con
        hwnd = self.popup_hwnd()
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                               style | win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TOOLWINDOW)
        return hwnd

    def allow_popup_focus(self, event=None):
        # Only an intentional click on the text switches focus to KanaHover.
        import win32gui
        import win32con
        try:
            hwnd = self.popup_hwnd()
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                                   style & ~win32con.WS_EX_NOACTIVATE)
            win32gui.SetForegroundWindow(hwnd)
            self.label.focus_set()
        except Exception:
            logger.exception("popup explicit focus")

    def copy_popup_selection(self, event=None):
        try:
            selected = self.label.get("sel.first", "sel.last")
        except tk.TclError:
            return "break"
        self.root.clipboard_clear()
        self.root.clipboard_append(selected)
        self.root.update()
        return "break"

    def hide_popup(self):
        if hasattr(self, "speech"):
            self.speech.stop()
        self.root.withdraw()
        self.popup_bounds = None
        self.last_value = None

    def point_in_popup(self, x, y):
        bounds = self.popup_bounds
        if not bounds:
            return False
        left, top, width, height = bounds
        return left <= x < left + width and top <= y < top + height

    def watch_popup_click(self):
        import win32api
        import win32con
        is_down = bool(win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000)
        if is_down and not self._popup_mouse_down:
            if (self.popup_bounds and self.root.winfo_viewable()
                    and not self.capture_active
                    and time.monotonic() - self.popup_opened_at > 0.18):
                x, y = pointer()
                if not self.point_in_popup(x, y):
                    self.hide_popup()
        self._popup_mouse_down = is_down
        if self.running.is_set():
            self.root.after(35, self.watch_popup_click)

    def configure_ocr_shortcut(self, *_):
        self.ocr.request_settings()

    def toggle_windows_startup(self, *_):
        try:
            toggle_startup()
            self.tray.update_menu()
        except Exception:
            logger.exception("Windows startup registration failed")

    def pause_menu_text(self, _item):
        # Called by pystray when rendering the first menu row.
        return "开始取词（当前：已暂停）" if self.paused else "暂停取词（当前：运行中）"

    def toggle(self, *_):
        self.paused = not self.paused
        self.messages.put(None)
        try:
            self.tray.update_menu()
        except Exception:
            logger.exception("tray pause menu refresh failed")

    def restart(self, *_):
        self.speech.stop()
        self.ocr.stop()
        self.running.clear()
        try:
            self.tray.stop()
        except Exception:
            pass
        import subprocess
        exe = sys.executable
        cmd = [exe, str(ROOT / "main.py")]
        subprocess.Popen(cmd, cwd=str(ROOT), creationflags=0x00000008)
        self.root.after(0, self.root.destroy)

    def exit(self, *_):
        self.speech.stop()
        self.ocr.stop()
        self.running.clear()
        try:
            self.tray.stop()
        except Exception:
            pass
        self.root.after(0, self.root.destroy)

    def consume(self):
        try:
            while True:
                data = self.messages.get_nowait()
                if data is None or self.paused:
                    self.hide_popup()
                    continue
                x, y, value = data
                if value != self.last_value or not self.root.winfo_viewable():
                    if value != self.last_value:
                        self.speech.stop()
                    content = value[0] + chr(10) + value[1]
                    self.label.delete("1.0", "end")
                    self.label.insert("1.0", content)
                    self.label.tag_remove("sel", "1.0", "end")
                    # Tk Text width is in font character cells, not Japanese
                    # glyphs. Measure both lines in pixels to avoid clipping
                    # readings such as たんまつしきべつばんごう.
                    font_spec = self.label.cget("font")
                    unit_px = max(1, int(self.root.tk.call("font", "measure", font_spec, "0")))
                    text_px = max(int(self.root.tk.call("font", "measure", font_spec, line))
                                  for line in value)
                    screen_w = self.root.winfo_screenwidth()
                    reserved_px = 95  # popup border, text padding and speaker
                    max_cells = max(12, (screen_w - reserved_px) // unit_px)
                    cells = (text_px + unit_px - 1) // unit_px + 3
                    self.label.configure(width=min(max_cells, max(12, cells)),
                                         wrap="none" if cells <= max_cells else "char")
                    self.root.update_idletasks()
                    w = self.root.winfo_reqwidth()
                    h = self.root.winfo_reqheight()
                    screen_w, screen_h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
                    dx = max(0, min(x + 16, screen_w - w - 4))
                    dy = max(0, min(y + 24, screen_h - h - 4))
                    self.root.geometry(f"+{dx}+{dy}")
                    hwnd = self.prevent_popup_activation()
                    self.root.deiconify()
                    import win32gui
                    import win32con
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE)
                    self.popup_bounds = (dx, dy, w, h)
                    self.popup_opened_at = time.monotonic()
                    self.last_value = value
        except queue.Empty:
            pass
        if self.running.is_set():
            self.root.after(80, self.consume)

    def scan(self):
        import comtypes
        import win32api
        import win32con
        comtypes.CoInitialize()
        last = None
        pressed = False
        press_xy = (0, 0)
        last_click = 0.0
        try:
            while self.running.is_set():
                time.sleep(0.065)
                if self.capture_active:
                    pressed = False
                    last = None
                    continue
                if self.paused:
                    if last is not None:
                        self.messages.put(None)
                        last = None
                    continue
                now = time.monotonic()
                down = bool(win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000)
                if down and not pressed:
                    press_xy = pointer()
                if pressed and not down:
                    # Selecting/copying text inside the popup must not trigger
                    # the original selection-reading pathway.
                    if self.point_in_popup(*press_xy):
                        pressed = down
                        continue
                    xy = pointer()
                    drag = abs(xy[0]-press_xy[0])+abs(xy[1]-press_xy[1]) > 6
                    doubleclick = (now - last_click) < 0.45
                    last_click = now
                    time.sleep(0.075)
                    try:
                        value = selected_reading()
                        if not value and (drag or doubleclick):
                            value = clipboard_selected_reading()
                        if value != last:
                            last = value
                            self.messages.put((xy[0],xy[1],value) if value else None)
                    except Exception:
                        logger.exception("selection read")
                pressed = down
        finally:
            comtypes.CoUninitialize()

if __name__ == "__main__":
    try:
        HoverApp().root.mainloop()
    except Exception:
        logger.exception("fatal")
        raise



