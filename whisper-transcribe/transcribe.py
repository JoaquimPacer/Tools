# Transcribe audio/video files to timestamped Markdown using OpenAI Whisper.
# Runs locally on your GPU for speed. Whisper handles mp4/mp3/wav directly.
#
# USAGE (from Anaconda Prompt):
#
#   Transcribe one file:
#     python transcribe.py "path\to\file.mp4"
#
#   Transcribe all audio/video files in a folder:
#     python transcribe.py "path\to\folder"
#
#   Save output to a different folder:
#     python transcribe.py "path\to\folder" -o "path\to\output\folder"
#
#   Use a smaller/faster model (less accurate):
#     python transcribe.py "path\to\file.mp4" --model medium

import subprocess
import sys
import shutil
import os
import argparse
import time

SUPPORTED = {'.mp3', '.mp4', '.m4a', '.wav', '.webm', '.mkv', '.avi', '.flac', '.ogg'}


def format_timestamp(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def find_files(path):
    path = os.path.abspath(path)
    if os.path.isfile(path):
        ext = os.path.splitext(path)[1].lower()
        if ext not in SUPPORTED:
            print(f"ERROR: Unsupported file type '{ext}'.")
            print(f"Supported: {', '.join(sorted(SUPPORTED))}")
            sys.exit(1)
        return [path]
    elif os.path.isdir(path):
        files = []
        for f in sorted(os.listdir(path)):
            if os.path.splitext(f)[1].lower() in SUPPORTED:
                files.append(os.path.join(path, f))
        if not files:
            print(f"ERROR: No audio/video files found in:\n  {path}")
            print(f"Supported: {', '.join(sorted(SUPPORTED))}")
            sys.exit(1)
        return files
    else:
        print(f"ERROR: Path not found:\n  {path}")
        sys.exit(1)


def ensure_dependencies():
    # ffmpeg
    if not shutil.which("ffmpeg"):
        print("Installing ffmpeg via conda...")
        subprocess.run(["conda", "install", "-y", "conda-forge::ffmpeg"], capture_output=False)
        if not shutil.which("ffmpeg"):
            print("ERROR: ffmpeg install failed. Run: conda install conda-forge::ffmpeg")
            sys.exit(1)

    # PyTorch
    try:
        import torch
    except ImportError:
        print("Installing PyTorch with CUDA support (may take a few minutes)...")
        subprocess.run(["conda", "install", "-y", "pytorch", "torchvision", "torchaudio",
                        "pytorch-cuda=12.6", "-c", "pytorch", "-c", "nvidia"], capture_output=False)
        try:
            import torch
        except ImportError:
            print("conda failed, trying pip...")
            subprocess.run([sys.executable, "-m", "pip", "install", "torch", "torchaudio",
                            "--index-url", "https://download.pytorch.org/whl/cu124"], capture_output=False)
            try:
                import torch
            except ImportError:
                print("ERROR: PyTorch install failed.")
                print("Run: conda install pytorch torchvision torchaudio pytorch-cuda=12.6 -c pytorch -c nvidia")
                sys.exit(1)

    # Whisper
    try:
        import whisper
    except ImportError:
        print("Installing openai-whisper...")
        subprocess.run([sys.executable, "-m", "pip", "install", "openai-whisper"], capture_output=False)
        try:
            import whisper
        except ImportError:
            print("ERROR: openai-whisper install failed. Run: pip install openai-whisper")
            sys.exit(1)


def format_elapsed(seconds):
    """Format elapsed seconds into human-readable string."""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h {m}m {s}s"
    elif m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


def transcribe_file(filepath, output_dir, model):
    basename = os.path.splitext(os.path.basename(filepath))[0]
    output_path = os.path.join(output_dir, basename + ".md")

    print(f"\n{'=' * 60}")
    print(f"  Transcribing: {os.path.basename(filepath)}")
    print(f"  Output:       {basename}.md")
    print(f"{'=' * 60}")

    file_start = time.time()
    result = model.transcribe(filepath, verbose=True)
    file_elapsed = time.time() - file_start

    detected_lang = result.get("language", "unknown")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# {basename} \u2014 Transcription\n\n")
        f.write(f"**Source file:** `{os.path.basename(filepath)}`\n\n")
        f.write(f"**Detected language:** {detected_lang}\n\n")
        f.write("---\n\n")
        for seg in result["segments"]:
            start = format_timestamp(seg["start"])
            end = format_timestamp(seg["end"])
            text = seg["text"].strip()
            f.write(f"**[{start} \u2013 {end}]** {text}\n\n")

    print(f"\nSaved: {output_path}")
    print(f"Time for this file: {format_elapsed(file_elapsed)}")
    return output_path, file_elapsed


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe audio/video files to timestamped Markdown using Whisper."
    )
    parser.add_argument("input",
                        help="File or folder to transcribe (mp4, mp3, wav, etc.)")
    parser.add_argument("-o", "--output",
                        help="Output folder for .md files (default: same as input)")
    parser.add_argument("--model", default="large-v3",
                        help="Whisper model: tiny, base, small, medium, large-v3 (default: large-v3)")
    args = parser.parse_args()

    # Python version check
    v = sys.version_info
    print(f"Python {v.major}.{v.minor}.{v.micro}")
    if v.minor >= 14:
        print("\nERROR: Python 3.14 detected. PyTorch does not support 3.14 yet.")
        print("Please run this from Anaconda Prompt (uses Python 3.12).")
        sys.exit(1)

    # Find files to transcribe
    files = find_files(args.input)
    print(f"\nFound {len(files)} file(s) to transcribe:")
    for f in files:
        print(f"  \u2022 {os.path.basename(f)}")

    # Determine output directory
    if args.output:
        output_dir = os.path.abspath(args.output)
        os.makedirs(output_dir, exist_ok=True)
    elif os.path.isdir(os.path.abspath(args.input)):
        output_dir = os.path.abspath(args.input)
    else:
        output_dir = os.path.dirname(os.path.abspath(args.input))

    print(f"\nOutput folder: {output_dir}")

    # Dependencies (skips instantly if already installed)
    ensure_dependencies()

    # Load model once, transcribe all files
    import torch
    import whisper

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\nDevice: {device}")
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    total_start = time.time()

    print(f"\nLoading Whisper model ({args.model})... ", end="", flush=True)
    model = whisper.load_model(args.model, device=device)
    print("done.")

    results = []
    for filepath in files:
        md_path, elapsed = transcribe_file(filepath, output_dir, model)
        results.append((md_path, elapsed))

    total_elapsed = time.time() - total_start

    print(f"\n{'=' * 60}")
    print(f"  ALL DONE! {len(results)} file(s) transcribed.")
    print(f"{'=' * 60}")
    print()
    for md_path, elapsed in results:
        print(f"  {os.path.basename(md_path)}  ({format_elapsed(elapsed)})")
    print(f"\n  Total time: {format_elapsed(total_elapsed)}")
    print(f"  Transcription complete. Ready for next step.")


if __name__ == "__main__":
    main()
