"""Optional local screenshot OCR mode for KanaHover. All recognition is offline."""
import json
import logging
import queue
import threading
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import keyboard
import pytesseract
from PIL import Image, ImageEnhance, ImageGrab, ImageOps, ImageTk
from app_paths import APP_ROOT, RESOURCE_ROOT

LOG = logging.getLogger("kana-hover")
CONFIG = APP_ROOT / "ocr_settings.json"
DEFAULT = "alt+c"

def tesseract_path():
    # Always use the bundled engine: no dependency on system Tesseract/PATH.
    candidates = [str(RESOURCE_ROOT / "vendor" / "tesseract" / "tesseract.exe")]
    for path in candidates:
        if path and Path(path).is_file():
            return path
    return None

def recognize(image):
    path = tesseract_path()
    if not path:
        raise RuntimeError("Tesseract OCR is not installed.")
    pytesseract.pytesseract.tesseract_cmd = path
    data_dir = RESOURCE_ROOT / "tessdata"
    if not (data_dir / "jpn.traineddata").exists():
        raise RuntimeError("Japanese OCR language file (jpn.traineddata) is missing.")
    # Single-line screenshots need raw-line mode; page mode misreads short kanji.
    single_line = image.height <= 130 and image.width >= image.height * 1.2
    if image.width < 900:
        image = image.resize((image.width * 2, image.height * 2), Image.Resampling.LANCZOS)
    image = ImageOps.autocontrast(ImageOps.grayscale(image))
    import os
    os.environ["TESSDATA_PREFIX"] = str(data_dir)
    mode = 13 if single_line else 6
    text = pytesseract.image_to_string(image, lang="jpn", config=f"--psm {mode}")
    return " ".join(text.split()).strip()

class OCRFeature:
    def __init__(self, app, reading_func, point_func):
        self.app = app
        self.reading_func = reading_func
        self.pointer = point_func
        self.requests = queue.Queue()
        self.active = False
        self.overlay = None
        self.screenshot = None
        self.shortcut = DEFAULT
        self.hotkey_id = None
        self.dragging = False
        self.origin = None
        self.rect_id = None
        self.offset = (0, 0)
        self._load()
        self._register(self.shortcut)
        self.app.root.after(50, self._pump)

    def _load(self):
        try:
            data = json.loads(CONFIG.read_text(encoding="utf-8"))
            self.shortcut = str(data.get("shortcut", DEFAULT))
        except (OSError, ValueError, TypeError):
            self.shortcut = DEFAULT

    def _register(self, shortcut):
        previous = self.shortcut
        old_id = self.hotkey_id
        if old_id is not None:
            keyboard.remove_hotkey(old_id)
            self.hotkey_id = None
        try:
            new_id = keyboard.add_hotkey(shortcut, self.request_capture, suppress=False)
        except Exception:
            if old_id is not None:
                self.hotkey_id = keyboard.add_hotkey(previous, self.request_capture, suppress=False)
            raise
        self.hotkey_id = new_id
        self.shortcut = shortcut

    def request_capture(self):
        self.requests.put(("capture", None))

    def request_settings(self):
        self.requests.put(("settings", None))

    def _pump(self):
        try:
            while True:
                action, arg = self.requests.get_nowait()
                if action == "capture":
                    if not self.active and not self.app.paused:
                        self._begin()
                elif action == "settings":
                    if not self.active:
                        self._settings()
                elif action == "result":
                    self.app.messages.put(arg)
                elif action == "error":
                    messagebox.showerror("KanaHover OCR", arg)
        except queue.Empty:
            pass
        if self.app.running.is_set():
            self.app.root.after(50, self._pump)

    def _begin(self):
        self.active = True
        self.app.capture_active = True
        self.app.messages.put(None)
        self.app.root.withdraw()
        try:
            image = ImageGrab.grab(all_screens=True)
            # ImageGrab's all_screens=True image is aligned with the virtual desktop.
            import win32api
            import win32con
            x0 = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
            y0 = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
            self.offset = (x0, y0)
            self.screenshot = image
            overlay = tk.Toplevel(self.app.root)
            self.overlay = overlay
            overlay.overrideredirect(True)
            overlay.attributes("-topmost", True)
            overlay.geometry(f"{image.width}x{image.height}{x0:+d}{y0:+d}")
            overlay.configure(cursor="crosshair")
            canvas = tk.Canvas(overlay, width=image.width, height=image.height,
                               highlightthickness=0, cursor="crosshair")
            canvas.pack(fill="both", expand=True)
            self.photo = ImageTk.PhotoImage(image, master=overlay)
            canvas.create_image(0, 0, image=self.photo, anchor="nw")
            self.canvas = canvas
            canvas.bind("<ButtonPress-1>", self._press)
            canvas.bind("<B1-Motion>", self._move)
            canvas.bind("<ButtonRelease-1>", self._release)
            canvas.bind("<ButtonPress-3>", self._cancel)
            overlay.bind("<Escape>", self._cancel)
            overlay.bind("<ButtonPress-3>", self._cancel)
            overlay.update_idletasks()
            overlay.update()
            overlay.focus_force()
            overlay.grab_set()
        except Exception:
            LOG.exception("OCR capture failed")
            self._finish()
            self.requests.put(("error", "Cannot open screen capture. See kana-hover.log."))

    def _press(self, event):
        self.dragging = True
        self.origin = (event.x, event.y)
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="#0089ed", width=3)

    def _move(self, event):
        if self.dragging and self.origin:
            self.canvas.coords(self.rect_id, *self.origin, event.x, event.y)

    def _release(self, event):
        if not self.dragging or self.origin is None:
            return
        x1, y1 = self.origin
        x2, y2 = event.x, event.y
        box = (max(0, min(x1, x2)), max(0, min(y1, y2)),
               min(self.screenshot.width, max(x1, x2)),
               min(self.screenshot.height, max(y1, y2)))
        self._finish()
        if box[2] - box[0] < 8 or box[3] - box[1] < 8:
            return
        cropped = self.screenshot.crop(box)
        location = self.pointer()
        threading.Thread(target=self._recognize, args=(cropped, location), daemon=True).start()

    def _recognize(self, image, location):
        try:
            text = recognize(image)
            value = self.reading_func(text)
            if value:
                self.requests.put(("result", (location[0], location[1], value)))
            elif not text:
                self.requests.put(("error", "No Japanese text was recognized in this region."))
            else:
                self.requests.put(("error", "OCR result has no Japanese reading: " + text[:100]))
        except Exception as exc:
            LOG.exception("local OCR failed")
            self.requests.put(("error", str(exc)))

    def _cancel(self, event=None):
        self._finish()

    def _finish(self):
        self.dragging = False
        self.origin = None
        self.rect_id = None
        if self.overlay is not None:
            try:
                self.overlay.grab_release()
                self.overlay.destroy()
            except tk.TclError:
                pass
            self.overlay = None
        self.photo = None
        self.active = False
        # Keep scan disabled briefly to avoid replaying the capture mouse release.
        self.app.root.after(200, self._restore_scan)

    def _restore_scan(self):
        self.app.capture_active = False

    def _settings(self):
        dlg = tk.Toplevel(self.app.root)
        dlg.title("KanaHover - OCR Shortcut")
        dlg.geometry("390x190")
        dlg.resizable(False, False)
        dlg.attributes("-topmost", True)
        tk.Label(dlg, text="Screenshot OCR hotkey", font=("Segoe UI", 12, "bold")).pack(pady=(16, 6))
        status = tk.StringVar(value=self.shortcut.upper())
        tk.Label(dlg, textvariable=status, font=("Consolas", 16)).pack(pady=7)
        tk.Label(dlg, text="Press Alt/Ctrl/Shift + a key, then Save.", font=("Segoe UI", 9)).pack()
        chosen = [self.shortcut]

        def on_key(event):
            modifier_names = {"Alt_L", "Alt_R", "Control_L", "Control_R",
                              "Shift_L", "Shift_R", "Win_L", "Win_R"}
            if event.keysym in modifier_names:
                return
            modifiers = []
            # Tk on Windows: Shift 0x1, Ctrl 0x4, Alt 0x20000
            if event.state & 0x20000:
                modifiers.append("alt")
            if event.state & 0x4:
                modifiers.append("ctrl")
            if event.state & 0x1:
                modifiers.append("shift")
            if not modifiers:
                status.set("Please hold Alt, Ctrl or Shift")
                return "break"
            key = event.keysym.lower()
            if key.startswith("f") and key[1:].isdigit():
                pass
            elif len(key) != 1 or not key.isalnum():
                status.set("Use a letter, digit or F-key")
                return "break"
            chosen[0] = "+".join(modifiers + [key])
            status.set(chosen[0].upper())
            return "break"

        def save():
            try:
                self._register(chosen[0])
                CONFIG.write_text(json.dumps({"shortcut": self.shortcut}, indent=2), encoding="utf-8")
                dlg.destroy()
            except Exception as exc:
                messagebox.showerror("Invalid shortcut", str(exc), parent=dlg)

        dlg.bind("<KeyPress>", on_key)
        tk.Button(dlg, text="Save", command=save, width=12).pack(pady=(12, 0))
        dlg.focus_force()
        dlg.grab_set()

    def stop(self):
        if self.hotkey_id is not None:
            try:
                keyboard.remove_hotkey(self.hotkey_id)
            except Exception:
                pass
            self.hotkey_id = None
