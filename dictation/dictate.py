#!/usr/bin/env python3
"""
Dictation Tool v2 — CapsLock-activated speech-to-text for Windows.

Tap CapsLock to start recording, tap again to transcribe and paste.
Runs silently in the system tray.

Controls:
    CapsLock        — toggle recording on/off (tap to start, tap to stop & paste)
    System tray     — right-click to quit
"""

import sys
import os
import platform
import time
import logging
import threading
import ctypes
import ctypes.wintypes
import winsound

if platform.system() != "Windows":
    print("This version supports Windows only.")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------
_missing = []
for _pkg, _mod in [
    ("faster-whisper", "faster_whisper"),
    ("sounddevice", "sounddevice"),
    ("numpy", "numpy"),
    ("pynput", "pynput"),
    ("pystray", "pystray"),
    ("Pillow", "PIL"),
]:
    try:
        __import__(_mod)
    except ImportError:
        _missing.append(_pkg)
if _missing:
    msg = f"Missing packages: {', '.join(_missing)}\nRun: pip install -r requirements.txt"
    try:
        ctypes.windll.user32.MessageBoxW(0, msg, "Dictation Tool", 0x10)
    except Exception:
        print(msg)
    sys.exit(1)

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from pynput import keyboard
from pynput.keyboard import Key
import pystray
from PIL import Image, ImageDraw

# ═══════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════
LANGUAGE = "en"
GPU_MODEL = "large-v3-turbo"   # Best accuracy — fast on RTX GPUs
CPU_MODEL = "small.en"         # Fallback for no-GPU systems
MIN_DURATION_SEC = 0.3         # Ignore recordings shorter than this
SAMPLE_RATE = 16000            # Whisper expects 16 kHz mono
BEEP_START = (600, 80)         # (Hz, ms) — beep when recording starts
BEEP_DONE = (800, 80)          # beep when transcription is pasted

# ═══════════════════════════════════════════════════════════════════
# Logging (file only — no console with pythonw)
# ═══════════════════════════════════════════════════════════════════
LOG_FILE = os.path.join(SCRIPT_DIR, "dictation.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8")],
)
log = logging.getLogger("dictation")

# ═══════════════════════════════════════════════════════════════════
# Windows helpers
# ═══════════════════════════════════════════════════════════════════
VK_CAPITAL = 0x14
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Flag to distinguish synthetic CapsLock events (from our watchdog/timer)
# from real user keypresses. Without this, the watchdog's CapsLock toggling
# gets picked up by the keyboard hook and falsely triggers recording.
_synthetic_caps = threading.Event()


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.c_ulong),
        ("wParamL", ctypes.c_ushort),
        ("wParamH", ctypes.c_ushort),
    ]


class _INPUTunion(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("union", _INPUTunion)]


_SendInput = user32.SendInput


def _send_ctrl_v():
    """Simulate Ctrl+V via SendInput."""
    VK_CONTROL = 0x11
    VK_V = 0x56
    inputs = (INPUT * 4)()
    # Ctrl down
    inputs[0].type = INPUT_KEYBOARD
    inputs[0].union.ki.wVk = VK_CONTROL
    # V down
    inputs[1].type = INPUT_KEYBOARD
    inputs[1].union.ki.wVk = VK_V
    # V up
    inputs[2].type = INPUT_KEYBOARD
    inputs[2].union.ki.wVk = VK_V
    inputs[2].union.ki.dwFlags = KEYEVENTF_KEYUP
    # Ctrl up
    inputs[3].type = INPUT_KEYBOARD
    inputs[3].union.ki.wVk = VK_CONTROL
    inputs[4 - 1].union.ki.dwFlags = KEYEVENTF_KEYUP
    _SendInput(4, inputs, ctypes.sizeof(INPUT))


def _set_clipboard(text):
    """Copy text to the Windows clipboard."""
    if not user32.OpenClipboard(0):
        time.sleep(0.05)
        if not user32.OpenClipboard(0):
            return False
    user32.EmptyClipboard()
    data = (text + "\0").encode("utf-16-le")
    h = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
    p = kernel32.GlobalLock(h)
    ctypes.memmove(p, data, len(data))
    kernel32.GlobalUnlock(h)
    user32.SetClipboardData(CF_UNICODETEXT, h)
    user32.CloseClipboard()
    return True


def _force_caps_off():
    """Turn CapsLock off if it's currently on. Marks the event as synthetic
    so the keyboard hook ignores it."""
    if user32.GetKeyState(VK_CAPITAL) & 1:
        _synthetic_caps.set()
        user32.keybd_event(VK_CAPITAL, 0, 0, 0)
        user32.keybd_event(VK_CAPITAL, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.05)
        _synthetic_caps.clear()


def _check_single_instance():
    """Prevent multiple instances via a named mutex."""
    kernel32.CreateMutexW(None, True, "Global\\DictationToolV2Mutex")
    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        log.info("Already running, exiting.")
        sys.exit(0)


# ═══════════════════════════════════════════════════════════════════
# Audio Recorder
# ═══════════════════════════════════════════════════════════════════
class Recorder:
    def __init__(self):
        self._active = False
        self._chunks = []
        self._lock = threading.Lock()
        self._stream = None

    @property
    def active(self):
        return self._active

    def start(self):
        with self._lock:
            self._chunks.clear()
        self._active = True
        try:
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
                callback=self._callback,
                blocksize=int(SAMPLE_RATE * 0.1),
            )
            self._stream.start()
        except Exception as e:
            log.error(f"Mic start failed: {e}")
            self._active = False

    def stop(self):
        self._active = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        with self._lock:
            if not self._chunks:
                return None
            audio = np.concatenate(self._chunks).flatten()
            self._chunks.clear()
        if len(audio) / SAMPLE_RATE < MIN_DURATION_SEC:
            return None
        return audio

    def _callback(self, indata, frames, time_info, status):
        if status:
            log.warning(f"Audio: {status}")
        if self._active:
            with self._lock:
                self._chunks.append(indata.copy())


# ═══════════════════════════════════════════════════════════════════
# Transcriber
# ═══════════════════════════════════════════════════════════════════
class Transcriber:
    def __init__(self):
        self._model = None
        self._lock = threading.Lock()

    def load(self):
        log.info("Loading Whisper model...")
        try:
            self._model = WhisperModel(
                GPU_MODEL, device="cuda", compute_type="float16"
            )
            log.info(f"Loaded {GPU_MODEL} on CUDA")
        except Exception as e:
            log.info(f"CUDA unavailable ({e}), trying CPU...")
            try:
                self._model = WhisperModel(
                    CPU_MODEL, device="cpu", compute_type="int8"
                )
                log.info(f"Loaded {CPU_MODEL} on CPU")
            except Exception as e2:
                log.error(f"Model load failed: {e2}")
                user32.MessageBoxW(
                    0,
                    f"Failed to load Whisper model:\n{e2}",
                    "Dictation Tool Error",
                    0x10,
                )
                os._exit(1)

    def transcribe(self, audio):
        with self._lock:
            segments, _ = self._model.transcribe(
                audio, language=LANGUAGE, beam_size=5, vad_filter=True
            )
            return " ".join(s.text for s in segments).strip()


# ═══════════════════════════════════════════════════════════════════
# Text Output
# ═══════════════════════════════════════════════════════════════════
def paste_text(text):
    """Copy text to clipboard and simulate Ctrl+V to paste it."""
    if not text:
        return
    if _set_clipboard(text):
        time.sleep(0.03)
        _send_ctrl_v()
        log.info(f"Pasted: {text[:80]}{'...' if len(text) > 80 else ''}")
    else:
        log.error("Failed to set clipboard")


# ═══════════════════════════════════════════════════════════════════
# System Tray
# ═══════════════════════════════════════════════════════════════════
_ICON_COLORS = {
    "loading": (158, 158, 158),
    "ready": (76, 175, 80),
    "recording": (244, 67, 54),
    "transcribing": (33, 150, 243),
}


def _make_icon(state):
    c = _ICON_COLORS.get(state, _ICON_COLORS["ready"])
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([4, 4, 60, 60], fill=(*c, 255))
    # Mic body
    d.rounded_rectangle([25, 14, 39, 38], radius=7, fill=(255, 255, 255, 220))
    # Mic arc
    d.arc([20, 28, 44, 50], 0, 180, fill=(255, 255, 255, 220), width=3)
    # Mic stand
    d.line([32, 50, 32, 56], fill=(255, 255, 255, 220), width=3)
    return img


# ═══════════════════════════════════════════════════════════════════
# Controller
# ═══════════════════════════════════════════════════════════════════
class DictationController:
    def __init__(self):
        self.recorder = Recorder()
        self.transcriber = Transcriber()
        self._tray = None
        self._listener = None
        self._lock = threading.Lock()
        self._caps_held = False

    # --- CapsLock handler (called from hook thread via short-lived thread) ---

    def on_caps_toggle(self):
        """Toggle recording on/off. Called once per CapsLock press-release cycle."""
        with self._lock:
            is_recording = self.recorder.active
        if is_recording:
            log.info("[STOP] CapsLock pressed — stopping recording")
            self._stop_and_transcribe()
        else:
            log.info("[START] CapsLock pressed — starting recording")
            self._start_recording()

    # --- Recording / transcription ---

    def _start_recording(self):
        self.recorder.start()
        if self.recorder.active:
            log.info("[MIC ON] Recording...")
            self._update_tray("recording")
            threading.Thread(
                target=lambda: winsound.Beep(*BEEP_START), daemon=True
            ).start()

    def _stop_and_transcribe(self):
        audio = self.recorder.stop()
        if audio is None:
            log.info("[MIC OFF] No audio captured (too short or empty)")
            self._update_tray("ready")
            return
        duration = len(audio) / SAMPLE_RATE
        log.info(f"[MIC OFF] Got {duration:.1f}s of audio, transcribing...")
        self._update_tray("transcribing")
        threading.Thread(
            target=self._transcribe_worker, args=(audio,), daemon=True
        ).start()

    def _transcribe_worker(self, audio):
        try:
            text = self.transcriber.transcribe(audio)
            if text:
                paste_text(text + " ")
        except Exception as e:
            log.error(f"Transcription error: {e}")
        finally:
            self._update_tray("ready")
            try:
                winsound.Beep(*BEEP_DONE)
            except Exception:
                pass

    # --- Tray ---

    def _update_tray(self, state):
        if self._tray:
            try:
                self._tray.icon = _make_icon(state)
                self._tray.title = f"Dictation [{state}]"
            except Exception:
                pass

    def _quit(self, icon=None, item=None):
        log.info("Shutting down...")
        if self.recorder.active:
            self.recorder.stop()
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
        if self._tray:
            try:
                self._tray.stop()
            except Exception:
                pass
        _cleanup_pid()
        os._exit(0)

    # --- Keyboard hook ---

    def _start_listener(self):
        """Start the pynput keyboard listener with CapsLock interception."""
        controller = self

        def win32_filter(msg, data):
            if data.vkCode == VK_CAPITAL:
                # Ignore synthetic CapsLock events from our watchdog/timer
                if _synthetic_caps.is_set():
                    return True  # let it through without processing
                # Toggle on key-UP (one clean action per press-release cycle)
                if msg == 257:  # WM_KEYUP
                    threading.Thread(
                        target=controller.on_caps_toggle, daemon=True
                    ).start()
                # Force CapsLock LED off after any real CapsLock event
                threading.Timer(0.05, _force_caps_off).start()
                return False  # suppress CapsLock from reaching other apps
            return True  # pass other keys through

        self._listener = keyboard.Listener(
            win32_event_filter=win32_filter,
            suppress=False,
        )
        self._listener.start()
        log.info("Keyboard hook active")

    def _monitor_listener(self):
        """Restart the keyboard listener if it dies."""
        while True:
            time.sleep(5)
            if self._listener and not self._listener.is_alive():
                log.warning("Keyboard listener died — restarting...")
                try:
                    self._start_listener()
                except Exception as e:
                    log.error(f"Listener restart failed: {e}")

    def _caps_watchdog(self):
        """Periodically force CapsLock off in case suppression misses."""
        while True:
            time.sleep(0.5)
            try:
                if user32.GetKeyState(VK_CAPITAL) & 1:
                    _force_caps_off()
            except Exception:
                pass

    # --- Main entry ---

    def run(self):
        _check_single_instance()
        _write_pid()

        log.info("=" * 50)
        log.info("  Dictation Tool v2")
        log.info("  CapsLock = toggle recording on/off")
        log.info("=" * 50)

        # Force CapsLock off before hooking
        _force_caps_off()

        # System tray
        menu = pystray.Menu(
            pystray.MenuItem("Dictation Tool v2", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit),
        )
        self._tray = pystray.Icon(
            "dictation", _make_icon("loading"), "Dictation [loading...]", menu
        )

        def init(icon):
            # Load model (may download on first run — ~1.5 GB for large-v3-turbo)
            self.transcriber.load()

            # Start keyboard hook
            self._start_listener()

            # Start watchdogs
            threading.Thread(target=self._monitor_listener, daemon=True).start()
            threading.Thread(target=self._caps_watchdog, daemon=True).start()

            self._update_tray("ready")
            log.info("Ready! Tap CapsLock to start dictating.")

        self._tray.run(setup=init)


# ═══════════════════════════════════════════════════════════════════
# PID file (for stop_dictation.bat)
# ═══════════════════════════════════════════════════════════════════
_PID_FILE = os.path.join(SCRIPT_DIR, ".dictation.pid")


def _write_pid():
    try:
        with open(_PID_FILE, "w") as f:
            f.write(str(os.getpid()))
    except Exception:
        pass


def _cleanup_pid():
    try:
        os.remove(_PID_FILE)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    DictationController().run()
