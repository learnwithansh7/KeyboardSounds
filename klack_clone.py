"""
Klack Clone (Windows) - Mechanical Keyboard & Mouse Sound Simulator
-------------------------------------------------------------------
A background app with a system tray icon and a quick-access global
sound switcher window that plays authentic mechanical keyboard sounds
on keystrokes and authentic mouse clicks & scroll wheel sounds.

Features:
- Global Switcher Window: press Ctrl+Alt+K (or click tray icon) to open
  a sleek floating window with Keyboard and Mouse sound switchers.
- Global Hotkeys:
    * Ctrl + Alt + K: Show / Hide the Sound Switcher window
    * Ctrl + Alt + M: Quick Mute / Unmute toggle
- Multiple authentic keyboard sound profiles:
    * Cream (NovelKeys Cream - thocky linear)
    * Crystal Purple (Everglide Crystal Purple - tactile)
    * Japanese Black (Cherry MX Black - heavy linear)
    * Milky Yellow (Gateron Milky Yellow)
    * Oreo (tactile switch)
    * Super Red (crisp switch)
    * Cardboard (classic Klack switch)
    * Cherry MX Brown (tactile)
    * Cherry MX Red (smooth linear)
    * Holy Panda (tactile thock)
    * Kailh Box White (crisp clicky)
    * Buckling Spring (vintage IBM Model M)
    * Tealios V2 (ultra-smooth linear)
    * custom (Pixabay audio clicks)
- Authentic Mouse Sounds:
    * Classic Mouse (Mechvibes Classic Mouse)
    * Logitech G502 X (High-end optical-mechanical gaming mouse)
    * Logitech G203 (Crisp gaming switch)
    * Logitech Superlight (Pro esports mouse click)
    * Razer DeathAdder (Optical mouse switch click)
    * Glorious Model O (Lightweight gaming mouse click)
    * Match Keyboard (repurposes your active keyboard switch for mouse clicks)
    * Scroll Wheel Ratchet (tactile notch ticks when scrolling up & down)
- Low-latency multi-channel audio via pygame.mixer.
- Remembers your settings across restarts (config.json).
"""

import ctypes
import glob
import json
import os
import random
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk

import pygame
import pystray
from PIL import Image, ImageDraw
from pynput import keyboard, mouse

if getattr(sys, "frozen", False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
    if hasattr(sys, "_MEIPASS") and os.path.isdir(os.path.join(sys._MEIPASS, "sounds")):
        SOUNDS_DIR = os.path.join(sys._MEIPASS, "sounds")
    else:
        SOUNDS_DIR = os.path.join(SCRIPT_DIR, "sounds")
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    SOUNDS_DIR = os.path.join(SCRIPT_DIR, "sounds")

# Low latency audio initialization
pygame.mixer.pre_init(frequency=44100, size=-16, channels=1, buffer=256)
pygame.mixer.init()
pygame.mixer.set_num_channels(32)

user32 = ctypes.windll.user32

CONFIG_DIR = os.path.join(os.environ.get("APPDATA", ""), "KeyboardSounds")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


# ---------------- Profile Loaders ----------------

def load_profiles():
    """
    Scan the sounds/ folder and load keyboard sound profiles.
    Maps named keys (e.g. 'space', 'enter', 'backspace') and scancodes,
    with list fallback for generic typing.
    """
    profiles = {}
    if not os.path.isdir(SOUNDS_DIR):
        return profiles

    for name in sorted(os.listdir(SOUNDS_DIR)):
        if name.lower() == "mouse":
            continue
        profile_path = os.path.join(SOUNDS_DIR, name)
        if not os.path.isdir(profile_path):
            continue

        down_files = sorted(glob.glob(os.path.join(profile_path, "down", "*.wav")))
        up_files = sorted(glob.glob(os.path.join(profile_path, "up", "*.wav")))

        if not down_files:
            continue

        down_map = {}
        down_list = []
        for f in down_files:
            try:
                snd = pygame.mixer.Sound(f)
            except Exception:
                continue
            down_list.append(snd)
            base = os.path.splitext(os.path.basename(f))[0].lower()
            down_map[base] = snd

            prefix = base.split("-")[0]
            if prefix.isdigit():
                down_map[int(prefix)] = snd

            if base in ("space", "spacebar"):
                down_map[57] = snd
                down_map["space"] = snd
            elif base in ("enter", "return"):
                down_map[28] = snd
                down_map["enter"] = snd
            elif base in ("backspace", "back"):
                down_map[14] = snd
                down_map["backspace"] = snd
            elif base in ("tab",):
                down_map[15] = snd
                down_map["tab"] = snd
            elif base in ("shift", "shift_l", "shift_r"):
                down_map["shift"] = snd

        up_map = {}
        up_list = []
        for f in up_files:
            try:
                snd = pygame.mixer.Sound(f)
            except Exception:
                continue
            up_list.append(snd)
            base = os.path.splitext(os.path.basename(f))[0].lower()
            up_map[base] = snd
            prefix = base.split("-")[0]
            if prefix.isdigit():
                up_map[int(prefix)] = snd
            if base in ("space", "spacebar"):
                up_map[57] = snd
                up_map["space"] = snd
            elif base in ("enter", "return"):
                up_map[28] = snd
                up_map["enter"] = snd
            elif base in ("backspace", "back"):
                up_map[14] = snd
                up_map["backspace"] = snd
            elif base in ("tab",):
                up_map[15] = snd
                up_map["tab"] = snd

        if down_list:
            profiles[name] = {
                "down_map": down_map,
                "down_list": down_list,
                "up_map": up_map,
                "up_list": up_list,
            }

    return profiles


def load_mouse_profiles():
    """
    Load mouse sound profiles and scroll wheel sound effects.
    Includes gaming mice and sounds extracted from authentic keyboard packs.
    """
    mouse_dir = os.path.join(SOUNDS_DIR, "mouse")
    if not os.path.isdir(mouse_dir):
        return {}, {}

    def load_snd(fname):
        p = os.path.join(mouse_dir, fname)
        if os.path.isfile(p):
            try:
                return pygame.mixer.Sound(p)
            except Exception:
                pass
        return None

    # Gaming & classic mouse files
    c_down = load_snd("classic_down.wav")
    c_up = load_snd("classic_up.wav")
    g502_p_down = load_snd("g502_primary_down.wav")
    g502_p_up = load_snd("g502_primary_up.wav")
    g502_s_down = load_snd("g502_secondary_down.wav")
    g502_s_up = load_snd("g502_secondary_up.wav")
    g502_mid = load_snd("g502_middle.wav")
    g203_clk = load_snd("logitech_g203_click.wav")
    superlight_clk = load_snd("logitech_superlight_click.wav")
    razer_clk = load_snd("razer_deathadder_click.wav")
    model_o_clk = load_snd("glorious_model_o_click.wav")

    # Authentic sounds extracted from user packs
    cream_d = load_snd("cream_click_down.wav")
    cream_u = load_snd("cream_click_up.wav")
    jp_black_d = load_snd("japanese_black_click_down.wav")
    jp_black_u = load_snd("japanese_black_click_up.wav")
    oreo_d = load_snd("oreo_click_down.wav")
    oreo_u = load_snd("oreo_click_up.wav")
    crystal_d = load_snd("crystal_purple_click_down.wav")
    crystal_u = load_snd("crystal_purple_click_up.wav")
    milky_d = load_snd("milky_yellow_click_down.wav")
    milky_u = load_snd("milky_yellow_click_up.wav")
    cardboard_d = load_snd("cardboard_click_down.wav")
    cardboard_u = load_snd("cardboard_click_up.wav")
    super_red_d = load_snd("super_red_click_down.wav")
    super_red_u = load_snd("super_red_click_up.wav")

    # Scroll sounds
    scroll_up = load_snd("scroll_up.wav")
    scroll_down = load_snd("scroll_down.wav")
    scroll_step = load_snd("scroll_step.wav")

    cream_tick = load_snd("cream_wheel_tick.wav")
    jp_tick = load_snd("japan_black_wheel_tick.wav")
    oreo_tick = load_snd("oreo_wheel_tick.wav")
    crystal_tick = load_snd("crystal_purple_wheel_tick.wav")
    cardboard_tick = load_snd("cardboard_wheel_tick.wav")
    milky_tick = load_snd("milky_yellow_wheel_tick.wav")

    scroll_sounds = {
        "up": scroll_up or scroll_step,
        "down": scroll_down or scroll_step,
        "step": scroll_step or scroll_up,
        # Profile-specific wheel ticks
        "Cream": cream_tick or scroll_step,
        "Japanese Black": jp_tick or scroll_step,
        "Oreo": oreo_tick or scroll_step,
        "Crystal Purple": crystal_tick or scroll_step,
        "Cardboard": cardboard_tick or scroll_step,
        "Milky Yellow": milky_tick or scroll_step,
    }

    profiles = {
        "Classic Mouse": {
            "left_down": c_down,
            "left_up": c_up,
            "right_down": c_down,
            "right_up": c_up,
            "middle": g502_mid or c_down,
            "scroll": scroll_step,
        },
        "Logitech G502 X": {
            "left_down": g502_p_down or c_down,
            "left_up": g502_p_up or c_up,
            "right_down": g502_s_down or c_down,
            "right_up": g502_s_up or c_up,
            "middle": g502_mid or c_down,
            "scroll": scroll_step,
        },
        "Logitech G203": {
            "left_down": g203_clk or c_down,
            "left_up": c_up,
            "right_down": g203_clk or c_down,
            "right_up": c_up,
            "middle": g502_mid or c_down,
            "scroll": scroll_step,
        },
        "Logitech Superlight": {
            "left_down": superlight_clk or c_down,
            "left_up": c_up,
            "right_down": superlight_clk or c_down,
            "right_up": c_up,
            "middle": g502_mid or c_down,
            "scroll": scroll_step,
        },
        "Razer DeathAdder": {
            "left_down": razer_clk or c_down,
            "left_up": c_up,
            "right_down": razer_clk or c_down,
            "right_up": c_up,
            "middle": g502_mid or c_down,
            "scroll": scroll_step,
        },
        "Glorious Model O": {
            "left_down": model_o_clk or c_down,
            "left_up": c_up,
            "right_down": model_o_clk or c_down,
            "right_up": c_up,
            "middle": g502_mid or c_down,
            "scroll": scroll_step,
        },
        "Cream Mouse": {
            "left_down": cream_d or c_down,
            "left_up": cream_u or c_up,
            "right_down": cream_d or c_down,
            "right_up": cream_u or c_up,
            "middle": cream_tick or g502_mid,
            "scroll": cream_tick or scroll_step,
        },
        "Japanese Black Mouse": {
            "left_down": jp_black_d or c_down,
            "left_up": jp_black_u or c_up,
            "right_down": jp_black_d or c_down,
            "right_up": jp_black_u or c_up,
            "middle": jp_tick or g502_mid,
            "scroll": jp_tick or scroll_step,
        },
        "Oreo Mouse": {
            "left_down": oreo_d or c_down,
            "left_up": oreo_u or c_up,
            "right_down": oreo_d or c_down,
            "right_up": oreo_u or c_up,
            "middle": oreo_tick or g502_mid,
            "scroll": oreo_tick or scroll_step,
        },
        "Crystal Purple Mouse": {
            "left_down": crystal_d or c_down,
            "left_up": crystal_u or c_up,
            "right_down": crystal_d or c_down,
            "right_up": crystal_u or c_up,
            "middle": crystal_tick or g502_mid,
            "scroll": crystal_tick or scroll_step,
        },
        "Cardboard Mouse": {
            "left_down": cardboard_d or c_down,
            "left_up": cardboard_u or c_up,
            "right_down": cardboard_d or c_down,
            "right_up": cardboard_u or c_up,
            "middle": cardboard_tick or g502_mid,
            "scroll": cardboard_tick or scroll_step,
        },
        "Milky Yellow Mouse": {
            "left_down": milky_d or c_down,
            "left_up": milky_u or c_up,
            "right_down": milky_d or c_down,
            "right_up": milky_u or c_up,
            "middle": milky_tick or g502_mid,
            "scroll": milky_tick or scroll_step,
        },
        "Super Red Mouse": {
            "left_down": super_red_d or c_down,
            "left_up": super_red_u or c_up,
            "right_down": super_red_d or c_down,
            "right_up": super_red_u or c_up,
            "middle": g502_mid or c_down,
            "scroll": scroll_step,
        },
        "Match Keyboard": {},
    }
    return profiles, scroll_sounds


PROFILES = load_profiles()
MOUSE_PROFILES, SCROLL_SOUNDS = load_mouse_profiles()

if not PROFILES:
    print(f"No sound profiles found under: {SOUNDS_DIR}")
    sys.exit(1)


# ---------------- State & Config Persistence ----------------

def load_config():
    default_cfg = {
        "profile": "Cream" if "Cream" in PROFILES else next(iter(PROFILES)),
        "volume": 0.85,
        "muted": False,
        "auto_hide": True,
        "mouse_enabled": True,
        "mouse_profile": "Classic Mouse",
        "scroll_enabled": True,
    }
    try:
        if os.path.isfile(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_cfg.update(data)
    except Exception:
        pass
    if default_cfg["profile"] not in PROFILES:
        default_cfg["profile"] = next(iter(PROFILES))
    if default_cfg["mouse_profile"] not in MOUSE_PROFILES:
        default_cfg["mouse_profile"] = "Classic Mouse"
    return default_cfg


saved_config = load_config()

state = {
    "profile": saved_config["profile"],
    "muted": saved_config["muted"],
    "volume": float(saved_config["volume"]),
    "auto_hide": bool(saved_config["auto_hide"]),
    "mouse_enabled": bool(saved_config["mouse_enabled"]),
    "mouse_profile": saved_config["mouse_profile"],
    "scroll_enabled": bool(saved_config["scroll_enabled"]),
    "pressed_keys": set(),
}


def save_config():
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        data = {
            "profile": state["profile"],
            "volume": state["volume"],
            "muted": state["muted"],
            "auto_hide": state["auto_hide"],
            "mouse_enabled": state["mouse_enabled"],
            "mouse_profile": state["mouse_profile"],
            "scroll_enabled": state["scroll_enabled"],
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


# ---------------- Keyboard Audio Hook ----------------

def get_scancode(key):
    try:
        if hasattr(key, "_scan") and key._scan:
            return key._scan
        if hasattr(key, "vk") and key.vk:
            return user32.MapVirtualKeyW(key.vk, 0)
        if hasattr(key, "value") and hasattr(key.value, "vk"):
            return user32.MapVirtualKeyW(key.value.vk, 0)
    except Exception:
        pass
    return None


def resolve_key_info(key):
    scancode = get_scancode(key)
    key_char = None
    if hasattr(key, "char") and key.char:
        key_char = key.char.lower()
    elif key == keyboard.Key.space:
        key_char = "space"
    elif key == keyboard.Key.enter:
        key_char = "enter"
    elif key == keyboard.Key.backspace:
        key_char = "backspace"
    elif key == keyboard.Key.tab:
        key_char = "tab"
    elif key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
        key_char = "shift"
    elif key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
        key_char = "ctrl"
    elif key == keyboard.Key.caps_lock:
        key_char = "caps lock"
    elif key == keyboard.Key.esc:
        key_char = "esc"
    return scancode, key_char


def play_sound(sound_map, sound_list, scancode=None, key_char=None):
    if state["muted"]:
        return
    snd = None
    if key_char is not None and key_char in sound_map:
        snd = sound_map[key_char]
    elif scancode is not None and scancode in sound_map:
        snd = sound_map[scancode]
    elif sound_list:
        snd = random.choice(sound_list)

    if snd:
        snd.set_volume(state["volume"])
        snd.play()


def on_press(key):
    scancode, key_char = resolve_key_info(key)
    key_id = scancode if scancode is not None else key_char
    if key_id is None or key_id in state["pressed_keys"]:
        return
    state["pressed_keys"].add(key_id)
    if state["muted"]:
        return
    profile = PROFILES.get(state["profile"])
    if not profile:
        return
    play_sound(profile["down_map"], profile["down_list"], scancode, key_char)


def on_release(key):
    scancode, key_char = resolve_key_info(key)
    key_id = scancode if scancode is not None else key_char
    if key_id is not None:
        state["pressed_keys"].discard(key_id)
    if state["muted"]:
        return
    profile = PROFILES.get(state["profile"])
    if not profile:
        return
    play_sound(profile["up_map"], profile["up_list"], scancode, key_char)


def start_keyboard_listener():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


# ---------------- Mouse Audio Hook ----------------

_last_scroll_time = 0.0


def play_mouse_click(button, pressed):
    if state["muted"] or not state.get("mouse_enabled", True):
        return

    prof_name = state.get("mouse_profile", "Classic Mouse")
    vol = state.get("volume", 0.85)

    if prof_name == "Match Keyboard":
        kb_prof = PROFILES.get(state["profile"])
        if not kb_prof:
            return
        if pressed:
            if kb_prof["down_list"]:
                snd = random.choice(kb_prof["down_list"])
                snd.set_volume(vol)
                snd.play()
        else:
            if kb_prof["up_list"]:
                snd = random.choice(kb_prof["up_list"])
                snd.set_volume(vol)
                snd.play()
        return

    mprof = MOUSE_PROFILES.get(prof_name)
    if not mprof:
        return

    if pressed:
        snd = None
        if button == mouse.Button.left:
            snd = mprof.get("left_down")
        elif button == mouse.Button.right:
            snd = mprof.get("right_down") or mprof.get("left_down")
        elif button == mouse.Button.middle:
            snd = mprof.get("middle") or mprof.get("left_down")
        else:
            snd = mprof.get("left_down")
        if snd:
            snd.set_volume(vol)
            snd.play()
    else:
        snd = None
        if button == mouse.Button.left:
            snd = mprof.get("left_up")
        elif button == mouse.Button.right:
            snd = mprof.get("right_up") or mprof.get("left_up")
        elif button == mouse.Button.middle:
            snd = mprof.get("middle")
        if snd:
            snd.set_volume(vol)
            snd.play()


def on_mouse_click(x, y, button, pressed):
    play_mouse_click(button, pressed)


def play_mouse_scroll(dy):
    global _last_scroll_time
    if state["muted"] or not state.get("mouse_enabled", True) or not state.get("scroll_enabled", True):
        return

    now = time.time()
    if now - _last_scroll_time < 0.028:
        return
    _last_scroll_time = now

    vol = state.get("volume", 0.85) * 0.75
    prof_name = state.get("mouse_profile", "Classic Mouse")
    mprof = MOUSE_PROFILES.get(prof_name, {})
    
    # Priority 1: Profile's custom scroll sound (e.g. Cream, Japanese Black, Oreo, etc.)
    snd = mprof.get("scroll")
    # Priority 2: Profile name lookup in SCROLL_SOUNDS
    if not snd:
        base_name = prof_name.replace(" Mouse", "").strip()
        snd = SCROLL_SOUNDS.get(base_name)
    # Priority 3: Direction-based tick (up or down)
    if not snd:
        snd = SCROLL_SOUNDS.get("up" if dy > 0 else "down") or SCROLL_SOUNDS.get("step")

    if snd:
        snd.set_volume(vol)
        snd.play()


def on_mouse_scroll(x, y, dx, dy):
    play_mouse_scroll(dy)


def start_mouse_listener():
    with mouse.Listener(on_click=on_mouse_click, on_scroll=on_mouse_scroll) as listener:
        listener.join()


# ---------------- Global Switcher GUI (Tkinter) ----------------

class SoundSwitcherWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Keyboard & Mouse Sounds")
        self.root.geometry("380x620")
        self.root.resizable(False, False)
        self.root.configure(bg="#18181b")

        self.root.withdraw()
        self.is_visible = False
        self.current_tab = "keyboard"

        self.root.protocol("WM_DELETE_WINDOW", self.hide)
        self.root.bind("<Escape>", lambda e: self.hide())

        self.setup_ui()

    def setup_ui(self):
        # Header Bar
        header = tk.Frame(self.root, bg="#18181b")
        header.pack(fill="x", padx=16, pady=(14, 4))

        title_lbl = tk.Label(
            header,
            text="🎧 Sound Switcher",
            font=("Segoe UI", 12, "bold"),
            fg="#f4f4f5",
            bg="#18181b",
        )
        title_lbl.pack(side="left")

        close_btn = tk.Button(
            header,
            text="✕",
            font=("Segoe UI", 10, "bold"),
            fg="#a1a1aa",
            bg="#27272a",
            activeforeground="#ffffff",
            activebackground="#ef4444",
            relief="flat",
            bd=0,
            padx=8,
            pady=2,
            cursor="hand2",
            command=self.hide,
        )
        close_btn.pack(side="right")

        tip_lbl = tk.Label(
            self.root,
            text="Hotkeys: Ctrl+Alt+K (Switcher)  |  Ctrl+Alt+M (Mute)",
            font=("Segoe UI", 8),
            fg="#71717a",
            bg="#18181b",
        )
        tip_lbl.pack(anchor="w", padx=16, pady=(0, 6))

        # Modern Segmented Tab Buttons
        tab_frame = tk.Frame(self.root, bg="#27272a", bd=1, relief="flat")
        tab_frame.pack(fill="x", padx=16, pady=(0, 10))

        self.btn_kb_tab = tk.Button(
            tab_frame,
            text="⌨️ Keyboard",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            padx=16,
            pady=6,
            cursor="hand2",
            command=lambda: self.switch_tab("keyboard"),
        )
        self.btn_kb_tab.pack(side="left", fill="x", expand=True)

        self.btn_mouse_tab = tk.Button(
            tab_frame,
            text="🖱️ Mouse",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            padx=16,
            pady=6,
            cursor="hand2",
            command=lambda: self.switch_tab("mouse"),
        )
        self.btn_mouse_tab.pack(side="left", fill="x", expand=True)

        # Tab Content Container
        self.content_container = tk.Frame(self.root, bg="#18181b")
        self.content_container.pack(fill="both", expand=True, padx=16, pady=0)

        # 1. Keyboard Profiles Tab
        self.kb_container = tk.Frame(self.content_container, bg="#18181b")

        kb_canvas = tk.Canvas(self.kb_container, bg="#18181b", highlightthickness=0)
        kb_scrollbar = ttk.Scrollbar(self.kb_container, orient="vertical", command=kb_canvas.yview)
        self.kb_scrollable = tk.Frame(kb_canvas, bg="#18181b")

        self.kb_scrollable.bind(
            "<Configure>",
            lambda e: kb_canvas.configure(scrollregion=kb_canvas.bbox("all")),
        )
        kb_canvas.create_window((0, 0), window=self.kb_scrollable, anchor="nw", width=326)
        kb_canvas.configure(yscrollcommand=kb_scrollbar.set)

        kb_canvas.pack(side="left", fill="both", expand=True)
        kb_scrollbar.pack(side="right", fill="y")
        kb_canvas.bind_all("<MouseWheel>", lambda event: kb_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))

        self.profile_buttons = {}
        for name in PROFILES:
            btn = tk.Button(
                self.kb_scrollable,
                text=f"  {name}",
                anchor="w",
                font=("Segoe UI", 10),
                relief="flat",
                bd=0,
                padx=12,
                pady=6,
                cursor="hand2",
                command=lambda n=name: self.select_profile(n),
            )
            btn.pack(fill="x", pady=2)
            self.profile_buttons[name] = btn

        # 2. Mouse Profiles Tab
        self.mouse_container = tk.Frame(self.content_container, bg="#18181b")

        # Toggles frame
        m_toggles = tk.Frame(self.mouse_container, bg="#27272a", padx=10, pady=8)
        m_toggles.pack(fill="x", pady=(0, 8))

        self.mouse_enable_var = tk.BooleanVar(value=state["mouse_enabled"])
        chk_m_enable = tk.Checkbutton(
            m_toggles,
            text="Enable Mouse Sounds (Click & Scroll)",
            variable=self.mouse_enable_var,
            font=("Segoe UI", 9, "bold"),
            fg="#22c55e",
            bg="#27272a",
            activebackground="#27272a",
            activeforeground="#22c55e",
            selectcolor="#18181b",
            command=self.on_mouse_enable_toggle,
        )
        chk_m_enable.pack(anchor="w")

        self.scroll_enable_var = tk.BooleanVar(value=state["scroll_enabled"])
        chk_scroll = tk.Checkbutton(
            m_toggles,
            text="Scroll Wheel Ratchet Sound",
            variable=self.scroll_enable_var,
            font=("Segoe UI", 8),
            fg="#a1a1aa",
            bg="#27272a",
            activebackground="#27272a",
            activeforeground="#e4e4e7",
            selectcolor="#18181b",
            command=self.on_scroll_enable_toggle,
        )
        chk_scroll.pack(anchor="w", pady=(4, 0))

        # Mouse Model List
        m_canvas = tk.Canvas(self.mouse_container, bg="#18181b", highlightthickness=0)
        m_scrollbar = ttk.Scrollbar(self.mouse_container, orient="vertical", command=m_canvas.yview)
        self.m_scrollable = tk.Frame(m_canvas, bg="#18181b")

        self.m_scrollable.bind(
            "<Configure>",
            lambda e: m_canvas.configure(scrollregion=m_canvas.bbox("all")),
        )
        m_canvas.create_window((0, 0), window=self.m_scrollable, anchor="nw", width=326)
        m_canvas.configure(yscrollcommand=m_scrollbar.set)

        m_canvas.pack(side="left", fill="both", expand=True)
        m_scrollbar.pack(side="right", fill="y")

        self.mouse_profile_buttons = {}
        for name in MOUSE_PROFILES:
            btn = tk.Button(
                self.m_scrollable,
                text=f"  {name}",
                anchor="w",
                font=("Segoe UI", 10),
                relief="flat",
                bd=0,
                padx=12,
                pady=6,
                cursor="hand2",
                command=lambda n=name: self.select_mouse_profile(n),
            )
            btn.pack(fill="x", pady=2)
            self.mouse_profile_buttons[name] = btn

        # Interactive Test Area
        self.test_box = tk.Label(
            self.mouse_container,
            text="🖱️ Click or Scroll here to test sound",
            font=("Segoe UI", 8, "italic"),
            fg="#a1a1aa",
            bg="#27272a",
            pady=8,
            cursor="hand2",
            relief="groove",
            bd=1,
        )
        self.test_box.pack(fill="x", pady=(8, 0))
        self.test_box.bind("<Button-1>", lambda e: self.on_test_click("Left Click"))
        self.test_box.bind("<Button-2>", lambda e: self.on_test_click("Middle Click"))
        self.test_box.bind("<Button-3>", lambda e: self.on_test_click("Right Click"))
        self.test_box.bind("<MouseWheel>", self.on_test_scroll)

        # Show initial tab
        self.switch_tab("keyboard")
        self.update_profile_buttons()
        self.update_mouse_profile_buttons()

        # Bottom Control Panel
        footer = tk.Frame(self.root, bg="#27272a", padx=14, pady=10)
        footer.pack(fill="x", side="bottom")

        # Volume Controls
        vol_frame = tk.Frame(footer, bg="#27272a")
        vol_frame.pack(fill="x", pady=(0, 4))

        self.vol_label = tk.Label(
            vol_frame,
            text=f"🔊 Volume: {int(state['volume'] * 100)}%",
            font=("Segoe UI", 9, "bold"),
            fg="#e4e4e7",
            bg="#27272a",
        )
        self.vol_label.pack(side="left")

        self.mute_btn = tk.Button(
            vol_frame,
            text="Mute" if not state["muted"] else "Unmute",
            font=("Segoe UI", 8, "bold"),
            bg="#ef4444" if state["muted"] else "#3f3f46",
            fg="#ffffff",
            activebackground="#dc2626",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=10,
            pady=2,
            cursor="hand2",
            command=self.toggle_mute,
        )
        self.mute_btn.pack(side="right")

        self.vol_slider = ttk.Scale(
            footer,
            from_=0,
            to=100,
            orient="horizontal",
            command=self.on_volume_change,
        )
        self.vol_slider.set(int(state["volume"] * 100))
        self.vol_slider.pack(fill="x", pady=(0, 4))

        # Auto-hide checkbox
        self.auto_hide_var = tk.BooleanVar(value=state["auto_hide"])
        chk_autohide = tk.Checkbutton(
            footer,
            text="Auto-hide after selecting sound",
            variable=self.auto_hide_var,
            font=("Segoe UI", 8),
            fg="#a1a1aa",
            bg="#27272a",
            activebackground="#27272a",
            activeforeground="#e4e4e7",
            selectcolor="#18181b",
            command=self.on_autohide_toggle,
        )
        chk_autohide.pack(anchor="w")

    def switch_tab(self, tab):
        self.current_tab = tab
        if tab == "keyboard":
            self.btn_kb_tab.configure(bg="#22c55e", fg="#000000", activebackground="#16a34a", activeforeground="#000000")
            self.btn_mouse_tab.configure(bg="#27272a", fg="#a1a1aa", activebackground="#3f3f46", activeforeground="#ffffff")
            self.mouse_container.pack_forget()
            self.kb_container.pack(fill="both", expand=True)
        else:
            self.btn_mouse_tab.configure(bg="#22c55e", fg="#000000", activebackground="#16a34a", activeforeground="#000000")
            self.btn_kb_tab.configure(bg="#27272a", fg="#a1a1aa", activebackground="#3f3f46", activeforeground="#ffffff")
            self.kb_container.pack_forget()
            self.mouse_container.pack(fill="both", expand=True)

    def on_test_click(self, name):
        self.test_box.configure(text=f"✓ {name} played!", fg="#22c55e")
        self.root.after(1000, lambda: self.test_box.configure(text="🖱️ Click or Scroll here to test sound", fg="#a1a1aa"))

    def on_test_scroll(self, event):
        direction = "Up ↑" if event.delta > 0 else "Down ↓"
        self.test_box.configure(text=f"✓ Scrolled {direction}", fg="#38bdf8")
        self.root.after(1000, lambda: self.test_box.configure(text="🖱️ Click or Scroll here to test sound", fg="#a1a1aa"))

    def update_profile_buttons(self):
        curr = state["profile"]
        for name, btn in self.profile_buttons.items():
            if name == curr:
                btn.configure(
                    bg="#22c55e",
                    fg="#000000",
                    activebackground="#16a34a",
                    activeforeground="#000000",
                    text=f"✓ {name}",
                    font=("Segoe UI", 10, "bold"),
                )
            else:
                btn.configure(
                    bg="#27272a",
                    fg="#fafafa",
                    activebackground="#3f3f46",
                    activeforeground="#ffffff",
                    text=f"  {name}",
                    font=("Segoe UI", 10),
                )

    def update_mouse_profile_buttons(self):
        curr = state["mouse_profile"]
        for name, btn in self.mouse_profile_buttons.items():
            if name == curr:
                btn.configure(
                    bg="#22c55e",
                    fg="#000000",
                    activebackground="#16a34a",
                    activeforeground="#000000",
                    text=f"✓ {name}",
                    font=("Segoe UI", 10, "bold"),
                )
            else:
                btn.configure(
                    bg="#27272a",
                    fg="#fafafa",
                    activebackground="#3f3f46",
                    activeforeground="#ffffff",
                    text=f"  {name}",
                    font=("Segoe UI", 10),
                )

    def select_profile(self, profile_name):
        state["profile"] = profile_name
        self.update_profile_buttons()
        save_config()

        prof = PROFILES.get(profile_name)
        if prof and prof["down_list"]:
            snd = random.choice(prof["down_list"])
            snd.set_volume(state["volume"])
            snd.play()

        if tray_icon:
            tray_icon.title = f"Keyboard Sounds ({state['profile']})"

        if self.auto_hide_var.get():
            self.root.after(160, self.hide)

    def select_mouse_profile(self, profile_name):
        state["mouse_profile"] = profile_name
        self.update_mouse_profile_buttons()
        save_config()

        play_mouse_click(mouse.Button.left, True)
        self.root.after(80, lambda: play_mouse_click(mouse.Button.left, False))

        if self.auto_hide_var.get():
            self.root.after(160, self.hide)

    def on_mouse_enable_toggle(self):
        state["mouse_enabled"] = self.mouse_enable_var.get()
        save_config()

    def on_scroll_enable_toggle(self):
        state["scroll_enabled"] = self.scroll_enable_var.get()
        save_config()

    def on_volume_change(self, val):
        v = float(val) / 100.0
        state["volume"] = v
        self.vol_label.configure(text=f"🔊 Volume: {int(float(val))}%")
        save_config()

    def on_autohide_toggle(self):
        state["auto_hide"] = self.auto_hide_var.get()
        save_config()

    def toggle_mute(self):
        state["muted"] = not state["muted"]
        self.mute_btn.configure(
            text="Unmute" if state["muted"] else "Mute",
            bg="#ef4444" if state["muted"] else "#3f3f46",
        )
        save_config()
        if tray_icon:
            tray_icon.notify("Muted" if state["muted"] else "Unmuted")

    def show(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w, h = 380, 620
        x = sw - w - 24
        y = sh - h - 64
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        self.update_profile_buttons()
        self.update_mouse_profile_buttons()
        self.mouse_enable_var.set(state["mouse_enabled"])
        self.scroll_enable_var.set(state["scroll_enabled"])
        self.vol_slider.set(int(state["volume"] * 100))
        self.mute_btn.configure(
            text="Unmute" if state["muted"] else "Mute",
            bg="#ef4444" if state["muted"] else "#3f3f46",
        )

        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.focus_force()
        self.is_visible = True

    def hide(self):
        self.root.withdraw()
        self.is_visible = False

    def toggle(self):
        if self.is_visible:
            self.hide()
        else:
            self.show()


# ---------------- System Tray Icon ----------------

tray_icon = None
switcher_app = None


def make_icon_image():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 6, 60, 58], radius=10, fill=(35, 35, 42), outline=(70, 70, 85), width=2)
    d.rounded_rectangle([10, 10, 54, 48], radius=7, fill=(90, 200, 120))
    d.text((22, 16), "K", fill=(20, 20, 20), font_size=28)
    return img


def set_profile_from_tray(name):
    def handler(icon_, item):
        state["profile"] = name
        save_config()
        if switcher_app:
            root.after(0, switcher_app.update_profile_buttons)
        icon_.title = f"Keyboard Sounds ({name})"
        icon_.notify(f"Keyboard: {name}")
    return handler


def set_mouse_profile_from_tray(name):
    def handler(icon_, item):
        state["mouse_profile"] = name
        save_config()
        if switcher_app:
            root.after(0, switcher_app.update_mouse_profile_buttons)
        icon_.notify(f"Mouse: {name}")
    return handler


def toggle_mouse_enable_tray(icon, item):
    state["mouse_enabled"] = not state["mouse_enabled"]
    save_config()
    if switcher_app:
        root.after(0, lambda: switcher_app.mouse_enable_var.set(state["mouse_enabled"]))
    icon.notify("Mouse sounds " + ("enabled" if state["mouse_enabled"] else "disabled"))


def toggle_scroll_enable_tray(icon, item):
    state["scroll_enabled"] = not state["scroll_enabled"]
    save_config()
    if switcher_app:
        root.after(0, lambda: switcher_app.scroll_enable_var.set(state["scroll_enabled"]))
    icon.notify("Scroll wheel sounds " + ("enabled" if state["scroll_enabled"] else "disabled"))


def toggle_mute_tray(icon, item):
    state["muted"] = not state["muted"]
    save_config()
    if switcher_app:
        root.after(
            0,
            lambda: switcher_app.mute_btn.configure(
                text="Unmute" if state["muted"] else "Mute",
                bg="#ef4444" if state["muted"] else "#3f3f46",
            ),
        )
    icon.notify("Muted" if state["muted"] else "Unmuted")


def toggle_switcher_from_tray(icon=None, item=None):
    if switcher_app:
        root.after(0, switcher_app.toggle)


# ---------------- Windows Startup & Single-Instance Mutex ----------------

import subprocess

STARTUP_LINK = os.path.join(
    os.environ.get("APPDATA", ""),
    r"Microsoft\Windows\Start Menu\Programs\Startup\KeyboardSounds.lnk",
)


def is_autostart_enabled():
    return os.path.exists(STARTUP_LINK)


def create_startup_shortcut():
    if getattr(sys, "frozen", False):
        exe_path = sys.executable
        work_dir = os.path.dirname(exe_path)
        cmd = (
            f'$WshShell = New-Object -ComObject WScript.Shell; '
            f'$Shortcut = $WshShell.CreateShortcut("{STARTUP_LINK}"); '
            f'$Shortcut.TargetPath = "{exe_path}"; '
            f'$Shortcut.WorkingDirectory = "{work_dir}"; '
            f'$Shortcut.Description = "Mechanical Keyboard & Mouse Sound Simulator"; '
            f'$Shortcut.Save()'
        )
    else:
        pyw_path = os.path.join(sys.prefix, "pythonw.exe")
        script_path = os.path.abspath(__file__)
        work_dir = os.path.dirname(script_path)
        cmd = (
            f'$WshShell = New-Object -ComObject WScript.Shell; '
            f'$Shortcut = $WshShell.CreateShortcut("{STARTUP_LINK}"); '
            f'$Shortcut.TargetPath = "{pyw_path}"; '
            f'$Shortcut.Arguments = \'"{script_path}"\'; '
            f'$Shortcut.WorkingDirectory = "{work_dir}"; '
            f'$Shortcut.Description = "Mechanical Keyboard & Mouse Sound Simulator"; '
            f'$Shortcut.Save()'
        )
    subprocess.run(
        ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", cmd],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )


def toggle_autostart(icon, item):
    if is_autostart_enabled():
        try:
            os.remove(STARTUP_LINK)
            icon.notify("Auto-start with Windows disabled.")
        except Exception:
            pass
    else:
        try:
            create_startup_shortcut()
            icon.notify("Auto-start with Windows enabled!")
        except Exception:
            pass


def quit_app(icon, item):
    icon.stop()
    root.after(0, root.destroy)
    os._exit(0)


def build_tray_menu():
    kb_profile_items = [
        pystray.MenuItem(
            name,
            set_profile_from_tray(name),
            checked=lambda item, n=name: state["profile"] == n,
            radio=True,
        )
        for name in sorted(PROFILES.keys())
    ]

    mouse_profile_items = [
        pystray.MenuItem("Enable Mouse Sounds", toggle_mouse_enable_tray, checked=lambda item: state["mouse_enabled"]),
        pystray.MenuItem("Scroll Wheel Sound", toggle_scroll_enable_tray, checked=lambda item: state["scroll_enabled"]),
        pystray.Menu.SEPARATOR,
    ] + [
        pystray.MenuItem(
            name,
            set_mouse_profile_from_tray(name),
            checked=lambda item, n=name: state["mouse_profile"] == n,
            radio=True,
        )
        for name in sorted(MOUSE_PROFILES.keys())
    ]

    return pystray.Menu(
        pystray.MenuItem("⚡ Sound Switcher (Ctrl+Alt+K)", toggle_switcher_from_tray, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Keyboard Profile", pystray.Menu(*kb_profile_items)),
        pystray.MenuItem("Mouse Profile", pystray.Menu(*mouse_profile_items)),
        pystray.MenuItem("Muted (Ctrl+Alt+M)", toggle_mute_tray, checked=lambda item: state["muted"]),
        pystray.MenuItem("Start with Windows (24/7)", toggle_autostart, checked=lambda item: is_autostart_enabled()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", quit_app),
    )


# ---------------- Global Hotkeys ----------------

def start_global_hotkeys():
    def on_hotkey_toggle():
        if switcher_app:
            root.after(0, switcher_app.toggle)

    def on_hotkey_mute():
        state["muted"] = not state["muted"]
        save_config()
        if switcher_app:
            root.after(
                0,
                lambda: switcher_app.mute_btn.configure(
                    text="Unmute" if state["muted"] else "Mute",
                    bg="#ef4444" if state["muted"] else "#3f3f46",
                ),
            )
        if tray_icon:
            tray_icon.notify("Muted" if state["muted"] else "Unmuted")

    hotkeys = keyboard.GlobalHotKeys({
        "<ctrl>+<alt>+k": on_hotkey_toggle,
        "<ctrl>+<alt>+m": on_hotkey_mute,
    })
    hotkeys.start()


# ---------------- Main Entry Point ----------------

if __name__ == "__main__":
    try:
        kernel32 = ctypes.windll.kernel32
        MUTEX_NAME = "Global_KlackCloneKeyboardSound_Mutex"
        _app_mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
        if kernel32.GetLastError() == 183:
            sys.exit(0)

        if not is_autostart_enabled():
            try:
                create_startup_shortcut()
            except Exception:
                pass

        root = tk.Tk()
        switcher_app = SoundSwitcherWindow(root)

        threading.Thread(target=start_keyboard_listener, daemon=True).start()
        threading.Thread(target=start_mouse_listener, daemon=True).start()
        start_global_hotkeys()

        tray_icon = pystray.Icon(
            "klack_clone",
            icon=make_icon_image(),
            title=f"Keyboard Sounds ({state['profile']})",
        )
        tray_icon.menu = build_tray_menu()
        threading.Thread(target=tray_icon.run, daemon=True).start()

        root.mainloop()
    except Exception as e:
        import traceback
        with open(os.path.join(SCRIPT_DIR, "app_error.log"), "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        sys.exit(1)
