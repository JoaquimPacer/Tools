# Dictation (Live Speech-to-Text)

This folder previously contained a custom dictation tool. It's been retired in favor of a much better project:

## Use [Whisper Key Local](https://github.com/PinW/whisper-key-local)

**Whisper Key** by [PinW](https://github.com/PinW) is a standalone speech-to-text app that does exactly what this custom tool was trying to do — and does it well. Press a hotkey, speak, and text appears at your cursor in any app.

- Runs locally (no cloud, full privacy)
- Uses OpenAI's Whisper model with GPU acceleration
- System tray app, configurable hotkeys
- Auto-pastes transcription at your cursor
- Windows and macOS

### Quick Start (Windows)

1. Download `whisper-key.exe` from the [latest release](https://github.com/PinW/whisper-key-local/releases/latest)
2. Run it — it self-installs and launches as a tray app
3. Press **Ctrl+Win** to start recording, **Ctrl** to stop and paste

### GPU Note

If you have an NVIDIA GPU and transcription fails with a `cublas64_12.dll` error, you need to copy that DLL into the app's bundled ctranslate2 directory. The standalone exe uses pyapp, which stores its Python environment in `%LOCALAPPDATA%\pyapp\data\whisper-key-local\`. Find `ctranslate2.dll` in there and copy `cublas64_12.dll` and `cublasLt64_12.dll` next to it. These DLLs come from PyTorch or the [CUDA 12 Toolkit](https://developer.nvidia.com/cuda-downloads).
