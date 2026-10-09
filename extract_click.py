"""
Extract several short click sounds from a longer reference audio file.

Requires ffmpeg installed and on PATH:
    winget install ffmpeg
(then restart your terminal)

Usage:
    1. Set SOURCE_FILE below to your downloaded audio file (e.g. the Pixabay clip).
    2. Add one entry to CLIPS for each distinct click sound you want to grab:
       (start_time_in_seconds, duration_in_seconds)
       Tip: open the file in Windows Media Player / VLC and note timestamps
       where you hear distinct, clean key sounds.
    3. Run: python extract_click.py
    4. This creates click_1.wav, click_2.wav, click_3.wav, ... in this folder.
    5. Use these with keyboard_click_sound.py (it will pick randomly between them).
"""

import os
import subprocess
import sys

# ---- EDIT THESE ----
SOURCE_FILE = "soundreality-keyboard-typing-sfx-525007.mp3"   # your downloaded file's name/path

# Add as many (start_time, duration) pairs as you like - each one becomes
# a separate click sound. Pick moments spread across the file for variety.
CLIPS = [
    (0.5, 0.12),
    (3.0, 0.12),
    (6.5, 0.12),
    (10.0, 0.12),
    (14.0, 0.12),
]
# ---------------------


def extract_clip(start_time, duration, output_file):
    cmd = [
        "ffmpeg", "-y",
        "-i", SOURCE_FILE,
        "-ss", str(start_time),
        "-t", str(duration),
        "-ar", "44100",
        "-ac", "1",
        output_file,
    ]
    subprocess.run(cmd, check=True)


def main():
    if not os.path.isfile(SOURCE_FILE):
        print(f"Could not find: {SOURCE_FILE}")
        print("Set SOURCE_FILE to the correct path of your audio file.")
        sys.exit(1)

    try:
        for i, (start_time, duration) in enumerate(CLIPS, start=1):
            output_file = f"click_{i}.wav"
            extract_clip(start_time, duration, output_file)
            print(f"Saved {output_file} (from {start_time}s, {duration}s long)")
    except FileNotFoundError:
        print("ffmpeg was not found on your system.")
        print("Install it with: winget install ffmpeg   (then restart your terminal)")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print("ffmpeg reported an error:", e)
        sys.exit(1)

    print(f"\nDone! Created {len(CLIPS)} click sounds.")
    print("Now run keyboard_click_sound.py - it will pick randomly between them.")


if __name__ == "__main__":
    main()