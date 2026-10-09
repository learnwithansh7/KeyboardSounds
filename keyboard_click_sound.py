"""
Klack Clone (Windows) - Mechanical Keyboard Sound Simulator
--------------------------------------------------------------
A background app with a system tray icon that plays a click sound on
key-down and (optionally) a softer sound on key-up, like a real mechanical
keyboard. Uses pygame's audio mixer so sounds overlap cleanly even when
typing fast (winsound can only play one sound at a time - pygame can play
many at once).

Setup:
    pip install pynput pystray pillow pygame

Folder layout expected (create these yourself):

    sounds/
        <profile_name_1>/
            down/   <- .wav files played on key press (one picked at random)
            up/     <- .wav files played on key release (optional)
        <profile_name_2>/
            down/
            up/

Example: put your click_1.wav ... click_5.wav files into:
    sounds/custom/down/

Run:
    python klack_clone.py

The app lives in your system tray (bottom-right, near the clock).
Right-click the tray icon to: switch profile, mute/unmute, or quit.
"""

import glob
import os
import random
import sys

import pygame
import pystray
from PIL import Image, ImageDraw
from pynput import keyboard

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SOUNDS_DIR = os.path.join(SCRIPT_DIR, "sounds")

# Small buffer = lower latency between keypress and sound.
# Enough channels = many overlapping clicks won't get cut off.
pygame.mixer.pre_init(frequency=44100, size=-16, channels=1, buffer=256)
pygame.mixer.init()
pygame.mixer.set_num_channels(32)


def load_profiles():
    """Scan the sounds/ folder and load down/up click sounds for each profile."""
    profiles = {}
    if not os.path.isdir(SOUNDS_DIR):
        return profiles

    for name in sorted(os.listdir(SOUNDS_DIR)):
        profile_path = os.path.join(SOUNDS_DIR, name)
        if not os.path.isdir(profile_path):
            continue

        down_files = sorted(glob.glob(os.path.join(profile_path, "down", "*.wav")))
        up_files = sorted(glob.glob(os.path.join(profile_path, "up", "*.wav")))

        if not down_files:
            continue  # a profile needs at least key-down sounds

        down_sounds = [pygame.mixer.Sound(f) for f in down_files]
        up_sounds = [pygame.mixer.Sound(f) for f in up_files]
        profiles[name] = {"down": down_sounds, "up": up_sounds}

    return profiles


PROFILES = load_profiles()

if not PROFILES:
    print(f"No sound profiles found under: {SOUNDS_DIR}")
    print("Create a folder like sounds/custom/down/ and put .wav files in it.")
    sys.exit(1)

state = {
    "profile": next(iter(PROFILES)),  # first profile found, alphabetically
    "muted": False,
}


def play(sound_list):
    if not sound_list or state["muted"]:
        return
    random.choice(sound_list).play()


def on_press(key):
    profile = PROFILES[state["profile"]]
    play(profile["down"])


def on_release(key):
    profile = PROFILES[state["profile"]]
    play(profile["up"])


def start_keyboard_listener():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


# ---------------- System tray icon ----------------

def make_icon_image():
    img = Image.new("RGB", (64, 64), (30, 30, 30))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([8, 20, 56, 44], radius=6, fill=(90, 200, 120))
    d.text((22, 24), "K", fill=(20, 20, 20))
    return img


def set_profile(profile_name):
    def handler(icon_, item):
        state["profile"] = profile_name
        icon_.notify(f"Profile: {profile_name}")
    return handler


def toggle_mute(icon, item):
    state["muted"] = not state["muted"]
    icon.notify("Muted" if state["muted"] else "Unmuted")


def quit_app(icon, item):
    icon.stop()
    os._exit(0)


def build_menu():
    profile_items = [
        pystray.MenuItem(
            name,
            set_profile(name),
            checked=lambda item, n=name: state["profile"] == n,
            radio=True,
        )
        for name in PROFILES
    ]
    return pystray.Menu(
        pystray.MenuItem("Sound profile", pystray.Menu(*profile_items)),
        pystray.MenuItem("Muted", toggle_mute, checked=lambda item: state["muted"]),
        pystray.MenuItem("Quit", quit_app),
    )


if __name__ == "__main__":
    import threading
    threading.Thread(target=start_keyboard_listener, daemon=True).start()

    tray_icon = pystray.Icon(
        "klack_clone",
        icon=make_icon_image(),
        title=f"Keyboard Sounds ({state['profile']})",
    )
    tray_icon.menu = build_menu()
    tray_icon.run()