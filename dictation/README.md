# Live Dictation Tool

Press **Caps Lock** to toggle live speech-to-text at your cursor — in any application.

Cross-platform: **Windows**, **macOS**, **Linux**.

## Controls

| Key | Action |
|---|---|
| **Caps Lock** | Toggle dictation on/off |
| **Escape** | Quit the tool |

---

## Windows Setup

### Prerequisites
- Python 3.8+ ([python.org](https://www.python.org/downloads/) or Anaconda/Miniconda)
- A microphone
- GPU with CUDA recommended (works on CPU, just slower)

### Quick Start
1. **Install once** — double-click `install.bat`
   - Installs Python dependencies
   - Registers the tool to auto-start on login
2. **Restart your PC** (or double-click `start_dictation.bat` to start now)
3. **Press Caps Lock** in any app to start/stop dictating

The tool runs minimized in the background on every login.

### Uninstall
Double-click `uninstall.bat`, or manually delete:
```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Dictation.vbs
```

---

## macOS Setup

### Prerequisites
- Python 3.8+ (`brew install python` or [python.org](https://www.python.org/downloads/))
- A microphone
- **Accessibility permissions** (required for keyboard interception)
- PortAudio: `brew install portaudio`

### Install
```bash
cd dictation
pip install -r requirements.txt
```

### Grant Accessibility Permissions
The tool needs accessibility access to intercept Caps Lock and type text:

1. Open **System Settings → Privacy & Security → Accessibility**
2. Click the **+** button
3. Add your **Terminal app** (Terminal, iTerm2, etc.)
4. If running via a Python IDE, add that IDE instead

Without this step, the tool cannot detect Caps Lock or type text.

### Run
```bash
python dictate.py
```

### Auto-Start on Login (optional)
1. Open **System Settings → General → Login Items**
2. Click **+** and add a shell script or `.command` file that runs `python /path/to/dictate.py`

Or create a Launch Agent:
```bash
cat > ~/Library/LaunchAgents/com.dictation.tool.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.dictation.tool</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/path/to/dictation/dictate.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
EOF
```
Edit the paths to match your setup, then:
```bash
launchctl load ~/Library/LaunchAgents/com.dictation.tool.plist
```

---

## Linux Setup

### Prerequisites
- Python 3.8+
- A microphone
- X11 (Xorg) display server
- `xdotool` and `portaudio` system packages

### Install System Dependencies

**Ubuntu / Debian:**
```bash
sudo apt install portaudio19-dev python3-pyaudio xdotool xset
```

**Fedora:**
```bash
sudo dnf install portaudio-devel python3-pyaudio xdotool xset
```

**Arch Linux:**
```bash
sudo pacman -S portaudio python-pyaudio xdotool xorg-xset
```

### Install Python Dependencies
```bash
cd dictation
pip install -r requirements.txt
```

### Run
```bash
python dictate.py
```

### Auto-Start on Login (optional)

Create a systemd user service:
```bash
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/dictation.service << 'EOF'
[Unit]
Description=Live Dictation Tool

[Service]
ExecStart=/usr/bin/python3 /path/to/dictation/dictate.py
Restart=on-failure
Environment=DISPLAY=:0

[Install]
WantedBy=default.target
EOF
```
Edit the path, then enable:
```bash
systemctl --user enable --now dictation.service
```

---

## How It Works

- **pynput** intercepts Caps Lock (suppressed so it doesn't toggle caps state)
- **RealtimeSTT** captures audio, runs Silero VAD, and streams through faster-whisper
- Partial transcriptions update in-place using backspace + retype (diff-based)
- Final transcription replaces partials for higher accuracy after each pause

### Platform-Specific Text Input
| Platform | Method | Notes |
|---|---|---|
| Windows | `SendInput` with `KEYEVENTF_UNICODE` | Immune to Caps Lock / modifier state |
| macOS | `pynput.keyboard.Controller` | Uses Quartz events |
| Linux | `xdotool --clearmodifiers` | Falls back to pynput if xdotool unavailable |

## Models

| Model | Size | Purpose |
|---|---|---|
| `base.en` | 74 MB | Real-time partials (fast) |
| `small.en` | 244 MB | Final transcription (accurate) |
| `tiny.en` | 39 MB | CPU fallback |

GPU (CUDA) is used automatically if available. On macOS, Apple Silicon is detected. Falls back to CPU with smaller models.

## Troubleshooting

### All Platforms
- **No microphone error**: Check that a mic is connected and recognized by the OS
- **Slow transcription**: Ensure GPU acceleration is available (CUDA on Windows/Linux)
- **Caps Lock LED briefly flashes**: Normal — the tool corrects it immediately
- **Check logs**: See `dictation.log` in the tool's folder

### Windows
- **PyAudio errors**: `pip install pyaudio` (or `conda install pyaudio`)
- **Verify CUDA**: `python -c "import torch; print(torch.cuda.is_available())"`

### macOS
- **"Input monitoring" prompt**: Grant accessibility permissions (see setup above)
- **PortAudio missing**: `brew install portaudio && pip install pyaudio`
- **No Quartz module**: `pip install pyobjc-framework-Quartz` (usually installed with pynput)

### Linux
- **Wayland**: This tool requires X11. If using Wayland, either switch to an X11 session or run under XWayland
- **xdotool not found**: `sudo apt install xdotool` (typing will fall back to pynput)
- **PortAudio missing**: Install `portaudio19-dev` (see setup above)
- **Permission denied for keyboard**: You may need to add your user to the `input` group: `sudo usermod -aG input $USER` then log out/in
