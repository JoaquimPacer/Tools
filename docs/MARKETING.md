# Tools: how I explain this project

This repo is a personal toolbox with nothing to sell, so this is the "how I explain it out loud" version rather than a pitch. What every folder does lives in [REPO_MAP.md](REPO_MAP.md). Written 2026-07-16.

## The one-liner

"It's my public toolbox. The headline tool takes any recording, a meeting, a talk, a voice memo, and hands back a timestamped transcript, running entirely on your own machine."

## The 30-second version

I record a lot: client calls, talks, my own notes. Uploading all that to a cloud transcription service never sat right with me, so the toolbox has a script that runs OpenAI's Whisper model locally. Point it at a file or a whole folder and it writes a Markdown transcript with timestamps, next to the originals. The setup guide is written so someone who has never touched Python can follow it, no admin rights needed. An hour of audio takes about ten minutes on a decent graphics card.

## Specifics that land in conversation

- One hour of audio transcribes in roughly 6 to 12 minutes on an NVIDIA card, and the same script falls back to Apple Silicon or plain CPU on its own.
- It handles nine formats (mp4, mp3, wav, m4a, mkv, webm, avi, flac, ogg) and pulls the audio out of video files itself.
- Privacy is structural, not a promise: after the one-time model download, nothing goes over the network at all.
- The setup guide assumes zero Python knowledge and no admin rights, because I wrote it for people who aren't developers.

## What makes it different (and the story I actually tell)

The best part of this repo is the folder that's nearly empty. I built my own live-dictation tool here, fought through audio bugs and hotkey bugs across four commits, and then found an open-source project that did the whole thing better. So I deleted my code and left a README pointing at theirs, with the one GPU fix that took me hours to figure out. Knowing when to retire your own work is a skill I want clients to know I have; nobody pays me to be precious about code.

## Honest answers to fair questions

- "Why not just use Otter or a cloud transcriber?" For public content, fine. For client calls and private notes, I'd rather the audio never leave my machine, and free-and-local beats subscription-and-uploaded on both counts.
- "Is it accurate?" Whisper's large model is very good on clear English speech; it still mishears names and struggles with heavy crosstalk. I treat transcripts as searchable notes, not court records.
- "Why keep a retired tool's folder around?" Because the redirect and the GPU troubleshooting note save the next person a day. An empty folder with good directions is worth more than my deleted code was.
