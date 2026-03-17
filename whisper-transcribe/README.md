# Whisper Transcription Setup Guide

How to set up and run OpenAI Whisper to transcribe audio/video files into timestamped Markdown documents. Works on **Windows**, **Mac**, and **Linux**. No admin privileges required.

---

## What You Need

- **Windows 10/11**, **macOS 12+**, or **Linux** (Ubuntu, Fedora, etc.)
- **A GPU** (optional but highly recommended for speed):
  - **Windows/Linux:** NVIDIA GPU (GTX 1060 or better)
  - **Mac:** Apple Silicon (M1/M2/M3/M4) — uses Metal acceleration automatically
- **An internet connection** (for one-time downloads during setup)

No GPU? The script still works on CPU — just slower.

---

## Setup Steps (One-Time)

### Step 1: Install Anaconda

Anaconda gives you Python 3.12 and a package manager (conda) that handles GPU libraries cleanly.

1. Go to: **https://www.anaconda.com/download**
2. Download the installer for your OS
3. Run the installer — install for **"Just Me"** (no admin needed)

**How to verify:**

| OS | Open | Command |
|---|---|---|
| **Windows** | **Anaconda Prompt** from the Start menu | `python --version` |
| **Mac** | **Terminal** | `python --version` |
| **Linux** | **Terminal** | `python --version` |

You should see `Python 3.12.x`. On Windows, make sure you're in **Anaconda Prompt**, not PowerShell or Command Prompt — those may point to a different Python version.

> **Windows users: Why Anaconda Prompt?**
>
> Windows often has Python 3.14 on the system PATH, which is too new for PyTorch. Anaconda Prompt activates the conda environment with Python 3.12. PowerShell, Command Prompt, and Windows Terminal don't do this automatically.
>
> Mac and Linux users don't have this problem — conda activates in the regular Terminal.

### Step 2: Install PyTorch (with GPU support)

PyTorch is the deep learning engine that Whisper runs on.

**Windows / Linux (NVIDIA GPU):**
```
conda install pytorch torchvision torchaudio pytorch-cuda=12.6 -c pytorch -c nvidia
```

If conda fails (e.g., "PackagesNotFoundError"), use the pip fallback:
```
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124
```

**Mac (Apple Silicon — M1/M2/M3/M4):**
```
conda install pytorch torchvision torchaudio -c pytorch
```
Metal (MPS) acceleration is built into PyTorch on Apple Silicon — no extra drivers needed.

**Mac (Intel) / Any machine without a GPU:**
```
conda install pytorch torchvision torchaudio -c pytorch
```
This installs CPU-only PyTorch. It works, just slower.

**How to verify:**
```
python -c "import torch; print(torch.cuda.is_available())"
```
- `True` = NVIDIA GPU ready
- `False` = will use CPU or MPS (Mac)

For Mac Apple Silicon, check MPS:
```
python -c "import torch; print(torch.backends.mps.is_available())"
```

### Step 3: Install ffmpeg

ffmpeg is the tool Whisper uses to decode audio and video files.

| OS | Command |
|---|---|
| **Windows** | `conda install conda-forge::ffmpeg` |
| **Mac** | `brew install ffmpeg` or `conda install conda-forge::ffmpeg` |
| **Linux (Ubuntu/Debian)** | `sudo apt install ffmpeg` |
| **Linux (Fedora)** | `sudo dnf install ffmpeg` |
| **Any OS (conda)** | `conda install conda-forge::ffmpeg` |

**How to verify:**
```
ffmpeg -version
```

### Step 4: Install OpenAI Whisper

Whisper is the speech-to-text AI model by OpenAI. It runs entirely on your machine — nothing is sent to the cloud.

```
pip install openai-whisper
```

This works the same on all platforms. The first time you transcribe, Whisper will also download the language model (~3 GB for `large-v3`). This is cached at `~/.cache/whisper/` so it only downloads once.

### Step 5: Download transcribe.py

Download `transcribe.py` from this repository and save it somewhere convenient.

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
- Auto-detects your GPU (NVIDIA CUDA, Apple MPS, or CPU fallback)
- Auto-installs any missing dependencies (Steps 2-4 above happen automatically if you skip them)

---

## How to Transcribe Files

Open your terminal (**Anaconda Prompt** on Windows, **Terminal** on Mac/Linux) and navigate to where `transcribe.py` is saved.

### Transcribe all files in a folder

```
python transcribe.py "/path/to/folder/with/media/files"
```

This finds every audio/video file in the folder and creates a `.md` file for each one, right next to the originals.

### Transcribe a single file

```
python transcribe.py "/path/to/my/recording.mp4"
```

### Save the .md files to a different location

```
python transcribe.py "/path/to/folder" -o "/path/to/output/folder"
```

### Use a faster (less accurate) model

```
python transcribe.py "/path/to/file.mp4" --model medium
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

Speed depends on your hardware. The `large-v3` model:

| Hardware | Speed | 1-hour file takes |
|---|---|---|
| **NVIDIA RTX 3060–4090** | ~5-10x real-time | ~6-12 minutes |
| **Apple Silicon M1–M4** | ~2-5x real-time | ~12-30 minutes |
| **CPU only** | ~0.5-1x real-time | ~1-2 hours |

| Audio/video length | NVIDIA GPU | Apple Silicon | CPU only |
|---|---|---|---|
| 15 minutes | ~2-3 min | ~3-8 min | ~15-30 min |
| 30 minutes | ~3-6 min | ~6-15 min | ~30-60 min |
| 1 hour | ~6-12 min | ~12-30 min | ~1-2 hours |
| 2 hours | ~12-20 min | ~24-60 min | ~2-4 hours |

The script prints exact timing after each file finishes and a total at the end.

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
| `Python 3.14 detected` error | **Windows:** Use Anaconda Prompt, not PowerShell. **Mac/Linux:** Activate conda: `conda activate base` |
| `CUDA not available` (Windows/Linux) | Reinstall PyTorch: `conda install pytorch torchvision torchaudio pytorch-cuda=12.6 -c pytorch -c nvidia` |
| `MPS not available` (Mac) | Update macOS to 12.3+ and reinstall PyTorch: `conda install pytorch torchvision torchaudio -c pytorch` |
| `ffmpeg not found` | See Step 3 above for your OS |
| Out of GPU memory | Use a smaller model: `--model medium` or `--model small` |
| Very slow transcription | Check that the script prints "Device: cuda" or "Device: mps". If it says "cpu", reinstall PyTorch. |
| Download is extremely slow | Check your VPN — if routed through a distant country, switch to a closer server or disconnect. |
| `No audio/video files found` | Check the folder path and ensure it contains supported file types. |

---

## Quick Reference

```
# Transcribe everything in a folder:
python transcribe.py "/path/to/folder"

# Transcribe one file:
python transcribe.py "/path/to/file.mp4"

# Save output elsewhere:
python transcribe.py "/path/to/folder" -o "/other/folder"

# Use faster model:
python transcribe.py "/path/to/folder" --model medium
```

No admin privileges needed. Everything runs in your user-level conda environment.
