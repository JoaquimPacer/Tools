# Whisper Transcription Setup Guide (Windows)

How to set up and run OpenAI Whisper on a standard Windows PC to transcribe audio/video files into timestamped Markdown documents. No admin privileges required.

---

## What You Need

- **Windows 10 or 11**
- **An NVIDIA GPU** (any modern one works; a dedicated GPU like GTX 1060 or better is recommended for speed)
- **An internet connection** (for one-time downloads during setup)

If you don't have an NVIDIA GPU, the script still works — it just runs on your CPU, which is significantly slower.

---

## Setup Steps (One-Time)

### Step 1: Install Anaconda

Anaconda gives you Python 3.12 and a package manager (conda) that handles GPU libraries cleanly. Windows ships with Python 3.14 on some systems, which is too new for PyTorch — Anaconda avoids this problem entirely.

1. Go to: **https://www.anaconda.com/download**
2. Click **Download** (the Windows 64-bit installer)
3. Run the installer
   - When asked, check **"Add Anaconda to my PATH"** (makes things easier)
   - Install for **"Just Me"** (no admin needed)
4. Finish the installer

**How to verify:** Open the **Start menu**, type **Anaconda Prompt**, and open it. You should see a terminal window. Type:
```
python --version
```
You should see something like `Python 3.12.x`. If you see 3.14, you opened the wrong terminal — make sure you're in **Anaconda Prompt**, not PowerShell or Command Prompt.

> **Why Anaconda Prompt and not PowerShell / Command Prompt / Terminal?**
>
> - **Anaconda Prompt** activates the conda environment with Python 3.12 and all the right library paths. It's the only terminal where PyTorch and Whisper are guaranteed to work.
> - **PowerShell / Command Prompt / Windows Terminal** use whatever Python is on your system PATH — often Python 3.14, which PyTorch doesn't support yet.
> - All four are just different terminal programs. The key difference is which Python they point to.

### Step 2: Install PyTorch (with GPU support)

PyTorch is the deep learning engine that Whisper runs on. Installing it with CUDA lets it use your NVIDIA GPU.

Open **Anaconda Prompt** and run:
```
conda install pytorch torchvision torchaudio pytorch-cuda=12.6 -c pytorch -c nvidia
```

Type `y` when prompted. This downloads ~2-4 GB (one-time).

**If conda fails** (e.g., "PackagesNotFoundError"), use the pip fallback:
```
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124
```

**How to verify:** In the same Anaconda Prompt, type:
```
python -c "import torch; print(torch.cuda.is_available())"
```
- `True` = GPU is ready (fast transcription)
- `False` = will use CPU (works, but slower). Try reinstalling PyTorch with the command above.

### Step 3: Install ffmpeg

ffmpeg is the tool Whisper uses to decode audio and video files.

In **Anaconda Prompt**, run:
```
conda install conda-forge::ffmpeg
```

Type `y` when prompted.

**How to verify:**
```
ffmpeg -version
```
Should print version info (not "command not found").

### Step 4: Install OpenAI Whisper

Whisper is the speech-to-text AI model by OpenAI. It runs locally on your PC — nothing is sent to the cloud.

In **Anaconda Prompt**, run:
```
pip install openai-whisper
```

The first time you run a transcription, Whisper will also download the language model (~3 GB for `large-v3`). This is cached at `~/.cache/whisper/` so it only downloads once.

### Step 5: Download transcribe.py

Download `transcribe.py` from this repository and save it somewhere convenient — for example:
```
C:\Users\YourName\Documents\transcribe.py
```

Or clone the whole repo:
```
git clone https://github.com/JoaquimPacer/Tools.git
```

This script is a wrapper around Whisper that:
- Accepts any audio or video file (mp3, mp4, wav, m4a, mkv, webm, avi, flac, ogg)
- Accepts a folder (transcribes all media files inside)
- Outputs timestamped Markdown files
- Loads the Whisper model once and processes all files in sequence
- Prints timing information when finished
- Auto-installs any missing dependencies (Steps 2-4 above happen automatically if you skip them)

---

## How to Transcribe Files

Every time you want to transcribe, open **Anaconda Prompt** and navigate to where `transcribe.py` is saved.

### Transcribe all files in a folder

```
cd C:\Users\YourName\Documents
python transcribe.py "C:\path\to\folder\with\media\files"
```

This finds every audio/video file in the folder and creates a `.md` file for each one, right next to the originals.

### Transcribe a single file

```
python transcribe.py "C:\path\to\my\recording.mp4"
```

### Save the .md files to a different location

```
python transcribe.py "C:\path\to\folder" -o "C:\path\to\output\folder"
```

### Use a faster (less accurate) model

```
python transcribe.py "C:\path\to\file.mp4" --model medium
```

Available models (from fastest to most accurate):

| Model | Size | Speed | Accuracy | GPU VRAM needed |
|---|---|---|---|---|
| `tiny` | 39 MB | Fastest | Low | ~1 GB |
| `base` | 74 MB | Very fast | Fair | ~1 GB |
| `small` | 244 MB | Fast | Good | ~2 GB |
| `medium` | 769 MB | Moderate | Very good | ~5 GB |
| `large-v3` | 3.1 GB | Slowest | Best | ~10 GB |

**Default is `large-v3`** — use this unless you have a GPU with less than 10 GB VRAM or you need results faster and can accept lower accuracy.

---

## How Long Does It Take?

With a modern NVIDIA GPU (e.g., RTX 3060, 4070, 4080), the `large-v3` model transcribes at roughly **5-10x real-time speed**:

| Audio/video length | Estimated time |
|---|---|
| 15 minutes | ~2-3 minutes |
| 30 minutes | ~3-6 minutes |
| 1 hour | ~6-12 minutes |
| 2 hours | ~12-20 minutes |

The script prints exact timing after each file finishes and a total at the end.

**CPU-only** (no NVIDIA GPU): expect roughly **0.5-1x real-time** — a 1-hour file could take 1-2 hours.

---

## Supported File Formats

The script accepts these file types directly — no conversion needed:

| Format | Type |
|---|---|
| `.mp4` | Video |
| `.mkv` | Video |
| `.webm` | Video |
| `.avi` | Video |
| `.mp3` | Audio |
| `.wav` | Audio |
| `.m4a` | Audio |
| `.flac` | Audio |
| `.ogg` | Audio |

Whisper extracts the audio track from video files automatically using ffmpeg.

---

## Output Format

Each transcription is saved as a Markdown file with the same name as the source file but with a `.md` extension. For example:

- Input: `My Recording.mp4`
- Output: `My Recording.md`

The Markdown file contains timestamped paragraphs:

```markdown
# My Recording — Transcription

**Source file:** `My Recording.mp4`

**Detected language:** english

---

**[0:00 – 0:15]** Hello, welcome to today's discussion...

**[0:15 – 0:32]** So the topic we're going to cover is...
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Python 3.14 detected` error | You opened the wrong terminal. Use **Anaconda Prompt** from the Start menu. |
| `CUDA not available` | PyTorch was installed without GPU support. Run: `conda install pytorch torchvision torchaudio pytorch-cuda=12.6 -c pytorch -c nvidia` |
| `ffmpeg not found` | Run: `conda install conda-forge::ffmpeg` |
| Out of GPU memory | Use a smaller model: `--model medium` or `--model small` |
| Very slow transcription | Check that CUDA is available (script prints "Device: cuda"). If it says "cpu", reinstall PyTorch with CUDA. |
| Download is extremely slow | Check your VPN — if routed through a distant country, switch to a closer server or disconnect VPN. |
| `No audio/video files found` | Make sure the folder path is correct and contains supported file types. |

---

## Quick Reference

```
# Open Anaconda Prompt, then:

# Transcribe everything in a folder:
python transcribe.py "C:\path\to\folder"

# Transcribe one file:
python transcribe.py "C:\path\to\file.mp4"

# Save output elsewhere:
python transcribe.py "C:\path\to\folder" -o "C:\other\folder"

# Use faster model:
python transcribe.py "C:\path\to\folder" --model medium
```

No admin privileges needed. Everything runs in your user-level Anaconda environment.
