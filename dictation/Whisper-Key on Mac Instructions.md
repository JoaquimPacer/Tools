  Install and fully verify PinW/whisper-key-local v0.8.2 on this Mac.

  Success means:
  - Speech is transcribed locally and pasted into TextEdit and a Codex CLI prompt.
  - No paid service, cloud transcription, API key, sudo pip, or source clone is used.
  - Global start/stop hotkeys work.
  - The selected model is responsive on this exact 2020 MacBook Pro.
  - Every skipped or failed check is reported explicitly.

  1. Inspect before changing anything:

  system_profiler SPHardwareDataType | egrep 'Model Name|Model Identifier|Chip|Processor Name|Memory'
  uname -m
  sw_vers -productVersion
  sysctl -in sysctl.proc_translated 2>/dev/null || true
  command -v brew || true
  command -v python3 || true
  command -v pipx || true

  Report whether this is Intel or M1, its RAM, macOS version, and whether Terminal
  is running through Rosetta.

  If it is an M1 but `uname -m` is x86_64 or `sysctl.proc_translated` is 1, stop.
  Tell me to open Terminal’s Get Info window, disable “Open using Rosetta,” and
  restart Terminal before continuing.

  If macOS is older than 11, stop because the required CTranslate2 wheel is
  unsupported. Do not update macOS automatically. If macOS is 11–13 and no working
  Homebrew installation exists, recommend updating macOS before installing the
  current Homebrew toolchain.

  2. Install the published package, not the Git repository.

  If Homebrew is absent on a supported macOS version, use only the official
  Homebrew installer and follow its printed `brew shellenv` instruction:

  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

  Then run:

  brew install python@3.13 pipx
  pipx ensurepath
  pipx install --python "$(brew --prefix python@3.13)/bin/python3.13" \
    "whisper-key-local==0.8.2"

  Verify with:

  pipx list
  pipx runpip whisper-key-local show whisper-key-local
  test -x "$HOME/.local/bin/whisper-key"

  Do not use sudo, global pip, or an unpinned package version.

  3. Create `~/.whisperkey/user_settings.yaml` as a minimal override.

  For an M1 use `distil-small.en`; for Intel use `base.en`:

  whisper:
    model: distil-small.en  # replace with base.en on Intel
    device: cpu
    compute_type: int8
    language: en
    beam_size: 1
    hotwords:
      - Codex
      - GitHub
      - Whisper Key
  clipboard:
    auto_paste: true
    delivery_method: paste
  voice_commands:
    enabled: false

  Do not copy the Windows settings, which use CUDA, float16, and Large-V3-Turbo.

  4. Have me run this in a separate Terminal tab and leave it running:

  $HOME/.local/bin/whisper-key

  Do not daemonize it or create a LaunchAgent yet. I need only one Codex CLI
  session; Whisper Key occupies a separate ordinary Terminal tab.

  5. Walk me through macOS permissions.

  Grant Microphone and Accessibility to the exact terminal application launching
  Whisper Key. Quit and reopen that terminal when macOS requests it, then rerun
  Whisper Key. Before any required Terminal restart, print a checkpoint describing
  what is complete and what remains.

  If recording works but global hotkeys do not, check Privacy & Security → Input
  Monitoring for that terminal. Inspect `~/.whisperkey/app.log` if anything remains
  broken. Never claim success while a permission is denied.

  6. Test safely in a blank TextEdit document first.

  Default controls:
  - Fn+Control: start recording
  - Fn: stop, transcribe, and paste
  - Shift: cancel
  - Option: stop, paste, and press Enter

  Do not test the Option auto-send action in Codex or a shell because an imperfect
  transcription could be submitted as a command.

  If Fn changes the Mac input source, requires a double press, or is not detected,
  add this override and restart Whisper Key:

  hotkey:
    recording_hotkey: ctrl+option+r
    stop_key: ctrl+option+s

  After TextEdit succeeds, verify ordinary stop-and-paste in a Codex CLI prompt
  without pressing Enter.

  7. Benchmark after one unscored warm-up recording.

  Record these three sentences at a normal pace and capture the console’s
  “Transcription completed in … seconds” value:

  - “Codex, inspect the repository and explain the failing test before changing any files.”
  - “Create a focused regression test for the GitHub authentication callback, then run only that test.”
  - “Summarize what changed, what was verified, and what remains uncertain.”

  Punctuation and capitalization do not count as errors. A material error changes
  the instruction or loses a technical term.

  Keep the initial model when all three preserve meaning, the median transcription
  time is at most five seconds, and the Mac does not stutter. Report anything over
  three seconds as noticeable latency.

  If latency exceeds five seconds or the system stutters:
  - M1: change `distil-small.en` to `base.en`.
  - Intel: change `base.en` to `tiny.en`.
  - Restart and repeat the benchmark.

  If latency passes but two or more sentences contain material errors:
  - M1: try `distil-medium.en`.
  - Intel: try `distil-small.en`.
  - Keep the larger model only if it still meets the five-second/stability limit;
    otherwise restore the initial model.

  8. Finish with a concise report containing hardware, macOS architecture, installed
  version, Python environment, chosen model, permissions granted, hotkeys used,
  all three timings, observed errors, configuration/log/model-cache paths, and
  anything not verified.

  ## Acceptance and fallback

  - The installation is accepted only after global recording, transcription, paste into TextEdit, and paste into an unsubmitted
    Codex prompt all succeed.

  - First-run model download requires internet; subsequent transcription is local. Configuration is in ~/.whisperkey, and
    downloaded models are under ~/.cache/huggingface/hub.

  - Do not configure start-at-login until the manual workflow proves stable.
  - If Whisper Key remains slow or unstable, report—without automatically installing—Handy (https://github.com/cjpais/Handy) as the
    recommended free/local fallback. It is a native Mac app whose transcription backend supports Apple Metal, installable later
    with brew install --cask handy.

  - macOS may require Microphone, Accessibility, and sometimes Input Monitoring permission for Terminal, as covered in Apple’s
    Privacy & Security documentation
    (https://support.apple.com/guide/mac-help/change-privacy-security-settings-on-mac-mchl211c911f/mac).