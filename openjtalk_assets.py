"""Stage the bundled OpenJTalk assets at an ASCII-only path for native HTS."""
import os
import shutil
import tempfile
from pathlib import Path

from app_paths import RESOURCE_ROOT

CACHE_NAME = "KanaHover_OpenJTalk_041"


def _copy_if_different(source: Path, dest: Path):
    if dest.is_file() and dest.stat().st_size == source.stat().st_size:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".copying")
    shutil.copy2(source, tmp)
    os.replace(tmp, dest)


def prepare_openjtalk_assets():
    """Return (dictionary, HTS voice) with ASCII-only filenames.

    Native OpenJTalk on Windows can fail to open UTF-8 encoded filenames when
    the software is located under a non-ASCII directory such as OneDrive/文档.
    Assets remain in the portable _internal bundle. An offline, per-user cache
    is populated once for the native engine's benefit.
    """
    source = RESOURCE_ROOT / "pyopenjtalk"
    if not source.is_dir():
        # Source checkout uses vendor/python; PyInstaller uses _internal/pyopenjtalk.
        source = RESOURCE_ROOT / "vendor" / "python" / "pyopenjtalk"
    dictionary = source / "dictionary"
    voice = source / "htsvoice" / "mei_normal.htsvoice"
    if not dictionary.is_dir() or not voice.is_file():
        raise FileNotFoundError("Bundled OpenJTalk dictionary/voice is missing.")
    # With pure ASCII directory paths, use the resources in-place.
    if str(dictionary).isascii() and str(voice).isascii():
        return dictionary, voice

    base = Path(tempfile.gettempdir())
    if not str(base).isascii():
        # A Unicode cache path would reproduce the native Windows error.
        # Windows may expose an ASCII short path when 8.3 naming is enabled.
        import ctypes
        buf = ctypes.create_unicode_buffer(32768)
        count = ctypes.windll.kernel32.GetShortPathNameW(str(base), buf, len(buf))
        if not count or not buf.value.isascii():
            raise RuntimeError(
                "OpenJTalk needs an ASCII-only cache path. "
                "Set TEMP/TMP to a user-writable ASCII directory and restart KanaHover."
            )
        base = Path(buf.value)
    dest = base / CACHE_NAME
    dest_dict = dest / "dictionary"
    dest_voice = dest / "htsvoice" / voice.name

    # Copy only the compiled dictionary payload and metadata; no network access.
    for file in dictionary.rglob("*"):
        if file.is_file():
            target = dest_dict / file.relative_to(dictionary)
            _copy_if_different(file, target)
    _copy_if_different(voice, dest_voice)
    return dest_dict, dest_voice
