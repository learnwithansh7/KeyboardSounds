# ⌨️ Keyboard & Mouse Sounds Simulator

A lightweight, authentic mechanical keyboard and mouse sound simulator for **Windows** and **Android**. Plays authentic tactile mechanical switch sounds on keystrokes, and crisp microswitch clicks & ratchet sounds on mouse clicks and scroll wheel turns.

---

## ✨ Features

### 🎧 14 Authentic Keyboard Sound Profiles
- **Cream** (NovelKeys Cream — thocky linear switch)
- **Crystal Purple** (Everglide Crystal Purple — crisp tactile switch)
- **Japanese Black** (Cherry MX Black — heavy, smooth linear switch)
- **Milky Yellow** (Gateron Milky Yellow — deep, smooth linear switch)
- **Oreo** (Tactile mechanical switch)
- **Super Red** (Crisp, snappy switch)
- **Cardboard** (Classic Klack switch)
- **Cherry MX Brown** (Balanced tactile switch)
- **Cherry MX Red** (Light, smooth linear switch)
- **Holy Panda** (Thocky tactile switch)
- **Kailh Box White** (Crisp clickbar switch)
- **Buckling Spring** (Vintage IBM Model M)
- **Tealios V2** (Ultra-smooth linear switch)
- **custom** (Studio audio click samples)

### 🖱️ Authentic Mouse Clicks & Scroll Wheel Sounds
- **Mouse Clicks**: Down-stroke and up-stroke (release) audio for Left, Right, and Middle clicks.
- **Scroll Wheel Ratchet**: Satisfying mechanical detent ticks when scrolling up and down.
- **14 Mouse Profiles**:
  - Gaming Mice: **Logitech G502 X**, **Logitech G203**, **Logitech G Pro Superlight**, **Razer DeathAdder**, **Glorious Model O**, **Classic Mouse**.
  - Switch Profiles: **Cream Mouse**, **Japanese Black Mouse**, **Oreo Mouse**, **Crystal Purple Mouse**, **Cardboard Mouse**, **Milky Yellow Mouse**, **Super Red Mouse**.
  - **Match Keyboard Switch**: Automatically repurposes your current active keyboard switch profile for mouse clicks.

### 💻 Windows PC Application
- **Global Hotkeys**:
  - `Ctrl + Alt + K` : Show / Hide Sound Switcher Window
  - `Ctrl + Alt + M` : Quick Mute / Unmute
- **Dual-Tab Switcher GUI**:
  - Switch between keyboard profiles and mouse profiles on the fly.
  - Interactive mouse testing pad with instant visual feedback.
  - Master volume slider.
- **System Tray Integration**:
  - Runs quietly in background without taskbar clutter.
  - Direct profile selector menu from tray icon.
  - One-click "Start with Windows" toggle.
- **Low-Latency Audio Engine**: Built on `pygame.mixer` with 32 dedicated audio channels.

### 📱 Android Application
- **Accessibility Service**: Works across any keyboard and app system-wide.
- **Audio Routing**: Built with Android `SoundPool` for ultra-low latency.
- **Intelligent Backspace Handling**: Single sound on backspace press with hold-suppression (no machine-gun loop).
- **Haptic Feedback**: Optional tactile vibration on every keystroke.

---

## 🚀 Getting Started (Windows)

### Requirements
- Python 3.10+
- Dependencies: `pygame`, `pynput`, `pystray`, `Pillow`

### Installation
```bash
# Clone the repository
git clone https://github.com/learnwithansh7/KeyboardSounds.git
cd KeyboardSounds

# Install dependencies
pip install pygame pynput pystray Pillow

# Run the application
python klack_clone.py
```

### Building the Windows Installer
```bash
# Build standalone application
pyinstaller -y KeyboardSounds.spec

# Package installer setup
python -c "import shutil; shutil.make_archive('payload', 'zip', 'dist/KeyboardSounds')"
pyinstaller -y KeyboardSounds_Setup.spec
```

---

## 📱 Getting Started (Android)

1. Open `android_app/KeyboardSoundsAndroid` in **Android Studio**.
2. Connect your Android device or start an emulator.
3. Build and run:
   ```bash
   cd android_app/KeyboardSoundsAndroid
   ./gradlew assembleRelease
   ```
4. Enable **Keyboard Sounds** in Android `Settings > Accessibility`.

---

## 📁 Project Structure

```
├── klack_clone.py                  # Windows desktop application
├── installer.py                    # Windows setup installer GUI
├── KeyboardSounds.spec             # PyInstaller spec for app
├── KeyboardSounds_Setup.spec       # PyInstaller spec for setup installer
├── sounds/                         # WAV sound profiles
│   ├── Cream/                      # Keyboard sound pack (down & up)
│   ├── Japanese Black/
│   ├── Crystal Purple/
│   ├── Milky Yellow/
│   ├── Oreo/
│   ├── Super Red/
│   ├── Cardboard/
│   └── mouse/                      # Mouse clicks & scroll ratchet sounds
└── android_app/                    # Android Studio project
    └── KeyboardSoundsAndroid/
        ├── app/src/main/java/      # Kotlin accessibility service & UI
        └── app/src/main/assets/    # Android audio assets
```

---

## 📜 License
MIT License
