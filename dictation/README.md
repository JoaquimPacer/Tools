# Dictation Tool v2

**Hold CapsLock** to record speech, **release** to transcribe and paste — in any application.

Uses OpenAI's Whisper (`large-v3-turbo`) for high-accuracy local transcription. Runs silently in the system tray.

## Controls

| Action | Effect |
|---|---|
| **Hold CapsLock** | Record while held, transcribe & paste on release |
| **Tap CapsLock** | Toggle recording on/off (for longer dictation) |
| **System tray → Quit** | Stop the tool |

## How It Works

1. **Hold CapsLock** — audio recording starts immediately
2. **Speak** — your microphone captures everything
3. **Release CapsLock** — audio is transcribed by Whisper and pasted at your cursor via clipboard

No real-time partial text. No jittery corrections. Just clean, accurate text after you finish speaking — like ChatGPT voice input.

For longer dictation, **tap CapsLock once** to start recording (hands-free), then **tap again** to stop and paste.

## Setup

### Prerequisites
- Windows 10/11
- Python 3.8+ ([python.org](https://www.python.org/downloads/) or Anaconda/Miniconda)
- A microphone
- NVIDIA GPU with CUDA recommended (works on CPU, just slower)

### Install
1. Double-click `install.bat`
   - Installs Python packages
   - Registers auto-start on login (Task Scheduler)
2. Double-click `start_dictation.bat` to start now
3. **First run downloads the Whisper model (~1.5 GB)** — look for the system tray icon to turn green

### System Tray Icon

| Color | Meaning |
|---|---|
| Grey | Loading model |
| Green | Ready — press CapsLock to dictate |
| Red | Recording |
| Blue | Transcribing |

### Stop / Uninstall
- **Stop**: right-click tray icon → Quit, or run `stop_dictation.bat`
- **Uninstall**: run `uninstall.bat`

## Audio Feedback

- **Low beep** (600 Hz) — recording started
- **High beep** (800 Hz) — transcription pasted

## Model

| GPU Available | Model | Size | Notes |
|---|---|---|---|
| Yes (CUDA) | `large-v3-turbo` | ~1.5 GB | Best accuracy, fast on modern GPUs |
| No | `small.en` | ~244 MB | Reasonable accuracy on CPU |

## Troubleshooting

- **No tray icon**: check `dictation.log` in this folder for errors
- **Slow transcription**: ensure CUDA is working — `python -c "import faster_whisper; print('OK')"`
- **CapsLock LED flashes**: normal — the tool turns it off immediately
- **No sound from mic**: check Windows Sound settings → Input
- **Already running**: only one instance allowed; stop the existing one first
- **Model download fails**: check internet connection; models come from Hugging Face
