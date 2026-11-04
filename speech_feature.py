"""Local Japanese speech for KanaHover using OpenJTalk/HTS and Windows WAV playback."""
import json
import logging
import os
import queue
import tempfile
import threading
import time
import wave
import winsound
from pathlib import Path
from tkinter import messagebox
from app_paths import APP_ROOT

LOG = logging.getLogger("kana-hover")
SETTINGS = APP_ROOT / "voice_settings.json"
SPEEDS = (0.8, 1.0, 1.2)


class OpenJTalkSpeaker:
    def __init__(self, app):
        self.app = app
        self.speed = 1.0
        self._load()
        self._events = queue.Queue()
        self._generation = 0
        self._active = False
        self._wav_path = None
        self._playing_since = 0.0
        self._duration = 0.0
        self.app.root.after(100, self._pump)

    def _load(self):
        try:
            value = float(json.loads(SETTINGS.read_text("utf-8")).get("speed", 1.0))
            if value in SPEEDS:
                self.speed = value
        except (OSError, ValueError, TypeError):
            pass

    def set_speed(self, speed):
        value = float(speed)
        if value not in SPEEDS:
            raise ValueError("Unsupported voice speed")
        self.speed = value
        SETTINGS.write_text(json.dumps({"speed": value}, indent=2), encoding="utf-8")

    def toggle(self, original):
        if self._active:
            self.stop()
            return
        original = str(original or "").strip()
        if not original:
            return
        self._generation += 1
        generation = self._generation
        self._active = True
        self.app.set_speaker_playing(True)
        threading.Thread(target=self._synthesize, args=(generation, original, self.speed),
                         daemon=True, name="OpenJTalkTTS").start()

    def _synthesize(self, generation, original, speed):
        filename = None
        try:
            import numpy as np
            from openjtalk_assets import prepare_openjtalk_assets
            dictionary_path, voice_path = prepare_openjtalk_assets()
            # Set the dictionary before importing: pyopenjtalk reads this at import.
            os.environ["OPEN_JTALK_DICT_DIR"] = str(dictionary_path)
            import pyopenjtalk
            # HTS uses a native file API and requires an ASCII-compatible path.
            pyopenjtalk.OPEN_JTALK_DICT_DIR = str(dictionary_path).encode("ascii")
            pyopenjtalk.DEFAULT_HTS_VOICE = str(voice_path).encode("ascii")
            # Original Japanese text only. No translation or reading text.
            audio, sample_rate = pyopenjtalk.tts(original, speed=speed, predict_nani=False)
            audio = np.asarray(audio, dtype=np.float64)
            if audio.size == 0:
                raise RuntimeError("OpenJTalk returned empty speech.")
            samples = np.clip(audio, -32768, 32767).astype("<i2")
            with tempfile.NamedTemporaryFile(suffix=".wav", prefix="kanahover_voice_",
                                             delete=False) as temporary:
                filename = temporary.name
            with wave.open(filename, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(int(sample_rate))
                wav.writeframes(samples.tobytes())
            self._events.put(("ready", generation, filename, audio.size / sample_rate))
        except Exception as exc:
            LOG.exception("OpenJTalk speech generation failed")
            if filename:
                self._safe_unlink(filename)
            self._events.put(("error", generation, str(exc), 0))

    def _safe_unlink(self, filename):
        if filename:
            try:
                os.unlink(filename)
            except OSError:
                pass

    def stop(self):
        self._generation += 1
        self._active = False
        try:
            winsound.PlaySound(None, 0)
        except RuntimeError:
            LOG.exception("OpenJTalk playback stop failed")
        self._safe_unlink(self._wav_path)
        self._wav_path = None
        self._playing_since = 0.0
        self.app.set_speaker_playing(False)

    def _pump(self):
        try:
            while True:
                kind, generation, payload, duration = self._events.get_nowait()
                if generation != self._generation or not self._active:
                    if kind == "ready":
                        self._safe_unlink(payload)
                    continue
                if kind == "error":
                    self.stop()
                    messagebox.showerror("KanaHover OpenJTalk", payload)
                    continue
                if kind == "ready":
                    try:
                        winsound.PlaySound(payload, winsound.SND_FILENAME |
                                           winsound.SND_ASYNC | winsound.SND_NODEFAULT)
                        self._wav_path = payload
                        self._duration = duration
                        self._playing_since = time.monotonic()
                    except Exception as exc:
                        LOG.exception("OpenJTalk WAV playback failed")
                        self.stop()
                        self._safe_unlink(payload)
                        messagebox.showerror("KanaHover OpenJTalk", str(exc))
        except queue.Empty:
            pass
        if (self._active and self._playing_since > 0 and
                time.monotonic() - self._playing_since >= self._duration + 0.3):
            self.stop()
        if self.app.running.is_set():
            self.app.root.after(100, self._pump)
