#!/usr/bin/env python3
"""
Live Dictation Tool — Caps Lock toggles speech-to-text at your cursor.

Cross-platform: Windows, macOS, Linux.

Usage:
    python dictate.py

Controls:
    Caps Lock  — toggle dictation on/off
    Escape     — quit the tool
"""

import sys
import os
import platform
import time
import logging
import threading

PLATFORM = platform.system()  # "Windows", "Darwin", "Linux"

# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------
_missing = []
for _mod in ["pynput", "RealtimeSTT"]:
    try:
        __import__(_mod)
    except ImportError:
        _missing.append(_mod)
if _missing:
    print(f"Missing: {', '.join(_missing)}")
    print("Run:  pip install -r requirements.txt")
    if PLATFORM == "Windows":
        input("Press Enter to exit...")
    sys.exit(1)

from pynput import keyboard
from pynput.keyboard import Key, Controller as KBController

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEBOUNCE_SEC = 0.30

# ---------------------------------------------------------------------------
# Logging (file + console)
# ---------------------------------------------------------------------------
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dictation.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("dictation")

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
_synthetic_caps = threading.Event()
_kb = KBController()

# ===========================================================================
# Platform-specific implementations
# ===========================================================================

if PLATFORM == "Windows":
    import ctypes

    # -- Windows constants --
    INPUT_KEYBOARD = 1
    KEYEVENTF_UNICODE = 0x0004
    KEYEVENTF_KEYUP = 0x0002
    VK_BACK = 0x08
    VK_CAPITAL = 0x14

    # -- ctypes structures for SendInput --
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
        _fields_ = [
            ("mi", MOUSEINPUT),
            ("ki", KEYBDINPUT),
            ("hi", HARDWAREINPUT),
        ]

    class INPUT(ctypes.Structure):
        _fields_ = [
            ("type", ctypes.c_ulong),
            ("union", _INPUTunion),
        ]

    _SendInput = ctypes.windll.user32.SendInput

    def _send_vk(vk):
        inp = (INPUT * 2)()
        inp[0].type = INPUT_KEYBOARD
        inp[0].union.ki.wVk = vk
        inp[1].type = INPUT_KEYBOARD
        inp[1].union.ki.wVk = vk
        inp[1].union.ki.dwFlags = KEYEVENTF_KEYUP
        _SendInput(2, inp, ctypes.sizeof(INPUT))

    def send_backspaces(n):
        for _ in range(n):
            _send_vk(VK_BACK)
            time.sleep(0.003)

    def send_unicode_string(text):
        for ch in text:
            inp = (INPUT * 2)()
            inp[0].type = INPUT_KEYBOARD
            inp[0].union.ki.wVk = 0
            inp[0].union.ki.wScan = ord(ch)
            inp[0].union.ki.dwFlags = KEYEVENTF_UNICODE
            inp[1].type = INPUT_KEYBOARD
            inp[1].union.ki.wVk = 0
            inp[1].union.ki.wScan = ord(ch)
            inp[1].union.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
            _SendInput(2, inp, ctypes.sizeof(INPUT))
            time.sleep(0.003)

    def caps_lock_on():
        return bool(ctypes.windll.user32.GetKeyState(VK_CAPITAL) & 1)

    def force_caps_off():
        if caps_lock_on():
            _synthetic_caps.set()
            _send_vk(VK_CAPITAL)
            time.sleep(0.05)
            _synthetic_caps.clear()

    def check_single_instance():
        mutex = ctypes.windll.kernel32.CreateMutexW(
            None, True, "Global\\DictationToolMutex"
        )
        if ctypes.windll.kernel32.GetLastError() == 183:
            print("Dictation tool is already running.")
            sys.exit(0)
        return mutex

    def set_title(t):
        try:
            ctypes.windll.kernel32.SetConsoleTitleW(t)
        except Exception:
            pass


elif PLATFORM == "Darwin":  # macOS

    def send_backspaces(n):
        for _ in range(n):
            _kb.press(Key.backspace)
            _kb.release(Key.backspace)
            time.sleep(0.003)

    def send_unicode_string(text):
        _kb.type(text)

    def caps_lock_on():
        try:
            import Quartz

            flags = Quartz.CGEventSourceFlagsState(
                Quartz.kCGEventSourceStateHIDSystemState
            )
            return bool(flags & Quartz.kCGEventFlagMaskAlphaShift)
        except ImportError:
            return False

    def force_caps_off():
        if caps_lock_on():
            _synthetic_caps.set()
            _kb.press(Key.caps_lock)
            _kb.release(Key.caps_lock)
            time.sleep(0.05)
            _synthetic_caps.clear()

    def check_single_instance():
        import fcntl

        lock_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), ".dictation.lock"
        )
        lock_file = open(lock_path, "w")
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (IOError, OSError):
            print("Dictation tool is already running.")
            sys.exit(0)
        return lock_file

    def set_title(t):
        sys.stdout.write(f"\033]0;{t}\007")
        sys.stdout.flush()


elif PLATFORM == "Linux":
    import subprocess as _sp

    def send_backspaces(n):
        if n <= 0:
            return
        try:
            _sp.run(
                ["xdotool", "key", "--clearmodifiers", "--delay", "3"]
                + ["BackSpace"] * n,
                check=True,
                timeout=10,
            )
        except (FileNotFoundError, _sp.SubprocessError):
            for _ in range(n):
                _kb.press(Key.backspace)
                _kb.release(Key.backspace)
                time.sleep(0.003)

    def send_unicode_string(text):
        if not text:
            return
        try:
            _sp.run(
                ["xdotool", "type", "--clearmodifiers", "--delay", "3", "--", text],
                check=True,
                timeout=10,
            )
        except (FileNotFoundError, _sp.SubprocessError):
            _kb.type(text)

    def caps_lock_on():
        try:
            result = _sp.run(
                ["xset", "q"], capture_output=True, text=True, timeout=2
            )
            return "Caps Lock:   on" in result.stdout
        except Exception:
            return False

    def force_caps_off():
        if caps_lock_on():
            _synthetic_caps.set()
            try:
                _sp.run(["xdotool", "key", "Caps_Lock"], timeout=2)
            except (FileNotFoundError, _sp.SubprocessError):
                _kb.press(Key.caps_lock)
                _kb.release(Key.caps_lock)
            time.sleep(0.05)
            _synthetic_caps.clear()

    def check_single_instance():
        import fcntl

        lock_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), ".dictation.lock"
        )
        lock_file = open(lock_path, "w")
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (IOError, OSError):
            print("Dictation tool is already running.")
            sys.exit(0)
        return lock_file

    def set_title(t):
        sys.stdout.write(f"\033]0;{t}\007")
        sys.stdout.flush()


else:
    print(f"Unsupported platform: {PLATFORM}")
    sys.exit(1)


# ===========================================================================
# Common code (all platforms)
# ===========================================================================

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
_listener = None
recording = False
recorder = None
_partial = ""
_text_lock = threading.Lock()
_last_caps_time = 0.0
_shutdown = threading.Event()

# ---------------------------------------------------------------------------
# RealtimeSTT callbacks
# ---------------------------------------------------------------------------
def on_realtime_stabilized(text):
    global _partial
    if not recording:
        return
    text = text.strip()
    with _text_lock:
        common = 0
        for a, b in zip(_partial, text):
            if a == b:
                common += 1
            else:
                break
        to_delete = len(_partial) - common
        to_type = text[common:]
        if to_delete:
            send_backspaces(to_delete)
        if to_type:
            send_unicode_string(to_type)
        _partial = text


def on_final_text(text):
    global _partial
    if not recording:
        return
    text = text.strip()
    with _text_lock:
        if _partial:
            send_backspaces(len(_partial))
            _partial = ""
        if text:
            send_unicode_string(text + " ")


# ---------------------------------------------------------------------------
# GPU / model selection
# ---------------------------------------------------------------------------
def pick_device_and_models():
    try:
        import torch

        if torch.cuda.is_available():
            log.info(f"GPU (CUDA): {torch.cuda.get_device_name(0)}")
            return "cuda", "base.en", "small.en"
    except ImportError:
        pass

    # macOS: check for Apple Silicon MPS
    if PLATFORM == "Darwin":
        try:
            import torch

            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                log.info("GPU: Apple Silicon (MPS)")
                return "mps", "base.en", "small.en"
        except ImportError:
            pass

    log.info("No GPU — CPU fallback with tiny model (slower).")
    return "cpu", "tiny.en", "tiny.en"


# ---------------------------------------------------------------------------
# Recorder
# ---------------------------------------------------------------------------
def create_recorder(device, rt_model, final_model):
    from RealtimeSTT import AudioToTextRecorder

    compute = "float16" if device in ("cuda", "mps") else "int8"
    return AudioToTextRecorder(
        model=final_model,
        language="en",
        compute_type=compute,
        device=device if device != "mps" else "cpu",  # faster-whisper uses CPU on MPS
        enable_realtime_transcription=True,
        realtime_model_type=rt_model,
        realtime_processing_pause=0.15,
        on_realtime_transcription_stabilized=on_realtime_stabilized,
        silero_sensitivity=0.4,
        post_speech_silence_duration=0.6,
        spinner=False,
        print_transcription_time=False,
    )


# ---------------------------------------------------------------------------
# Toggle
# ---------------------------------------------------------------------------
def start_recording():
    global recording, _partial
    with _text_lock:
        recording = True
        _partial = ""
    log.info("[MIC ON]  Speak now...")
    set_title("Dictation [LISTENING]")
    threading.Thread(target=_listen_loop, daemon=True).start()


def _listen_loop():
    try:
        while recording and not _shutdown.is_set():
            recorder.text(on_final_text)
    except Exception as e:
        if recording:
            log.error(f"Recorder error: {e}")


def stop_recording():
    global recording, _partial
    with _text_lock:
        recording = False
        _partial = ""
    log.info("[MIC OFF] Paused.")
    set_title("Dictation [ready]")
    try:
        recorder.abort()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Keyboard hook
# ---------------------------------------------------------------------------
def on_press(key):
    global _last_caps_time
    if key == Key.esc:
        log.info("Escape — shutting down...")
        _shutdown.set()
        if recording:
            stop_recording()
        return False

    # macOS / Linux: handle Caps Lock in on_press
    if PLATFORM != "Windows" and key == Key.caps_lock:
        if _synthetic_caps.is_set():
            return
        now = time.time()
        if now - _last_caps_time >= DEBOUNCE_SEC:
            _last_caps_time = now
            if recording:
                stop_recording()
            else:
                start_recording()
        threading.Timer(0.05, force_caps_off).start()


def win32_filter(msg, data):
    """Windows-only low-level keyboard hook for Caps Lock interception."""
    global _last_caps_time
    VK_CAPITAL_LOCAL = 0x14
    if data.vkCode == VK_CAPITAL_LOCAL:
        if _synthetic_caps.is_set():
            return True
        if msg == 256:  # WM_KEYDOWN
            now = time.time()
            if now - _last_caps_time >= DEBOUNCE_SEC:
                _last_caps_time = now
                if recording:
                    stop_recording()
                else:
                    start_recording()
            threading.Timer(0.05, force_caps_off).start()
        return False
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    global _listener, recorder

    _mutex = check_single_instance()  # noqa: F841

    set_title("Dictation [loading...]")
    log.info("=" * 50)
    log.info("  Live Dictation Tool")
    log.info(f"  Platform: {PLATFORM}")
    log.info("  Caps Lock = toggle  |  Escape = quit")
    log.info("=" * 50)

    force_caps_off()

    device, rt_model, final_model = pick_device_and_models()
    log.info(f"Loading: realtime={rt_model}, final={final_model} ...")
    log.info("(First run downloads models — may take a minute.)")

    try:
        recorder = create_recorder(device, rt_model, final_model)
    except Exception as e:
        log.error(f"Recorder init failed: {e}")
        if "microphone" in str(e).lower() or "pyaudio" in str(e).lower():
            log.error("Make sure a microphone is connected and PyAudio is installed.")
        if PLATFORM == "Windows":
            input("Press Enter to exit...")
        sys.exit(1)

    set_title("Dictation [ready]")
    log.info("Ready!  Press Caps Lock to start dictating.\n")

    # Platform-specific listener setup
    if PLATFORM == "Windows":
        _listener = keyboard.Listener(
            on_press=on_press,
            win32_event_filter=win32_filter,
            suppress=False,
        )
    else:
        _listener = keyboard.Listener(
            on_press=on_press,
            suppress=False,
        )

    _listener.start()
    _listener.join()

    try:
        recorder.shutdown()
    except Exception:
        pass
    force_caps_off()
    log.info("Goodbye.")


if __name__ == "__main__":
    main()
