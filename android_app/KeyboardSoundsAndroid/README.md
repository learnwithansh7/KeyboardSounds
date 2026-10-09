# ⌨ Keyboard Sounds for Android

Mechanical Keyboard typing sound simulator for your **internal phone keyboard** (Gboard, Samsung Keyboard, SwiftKey, etc.).

Plays authentic mechanical switch clicks (NovelKeys Cream, Cherry MX Red/Brown, Holy Panda, Kailh Box White, etc.) whenever you type in **any app** on your phone!

---

## 🌟 How It Works

Android does not allow apps to modify Gboard directly. Instead, this app uses Android's native **Accessibility Service API**:

1. **Keystroke Detection:** Listens to `TYPE_VIEW_TEXT_CHANGED` events whenever any text changes in any app (WhatsApp, Chrome, Notes, Instagram, etc.).
2. **Audio Engine (`SoundPool`):** Low-latency native multi-channel audio playback with preloaded WAV/OGG mechanical sound files.
3. **Smart Sound Mapping:**
   - **Letters / Numbers:** Plays random down-stroke switch clicks for authentic variation.
   - **Spacebar / Enter:** Heavy stabilizer sound effects.
   - **Backspace:** Distinct key-deletion click.
4. **Haptic Tactile Feedback:** Synchronized subtle vibration tick for each keystroke.
5. **🔒 100% Private & Offline:** The app does not request `INTERNET` permission in its AndroidManifest. It cannot store, log, or transmit anything you type.

---

## 🎧 Included Sound Profiles

- **NovelKeys Cream** (Thocky linear)
- **Cherry MX Red** (Smooth linear)
- **Cherry MX Brown** (Classic tactile)
- **Holy Panda** (Crisp tactile thock)
- **Kailh Box White** (Crisp clicky switch)
- **Tealios V2** (Ultra-smooth linear)
- **Buckling Spring** (Vintage IBM Model M)
- **Cardboard** (Classic Klack switch)

---

## 🚀 How to Build the APK

### Option 1: Using Android Studio (Recommended)
1. Download and install [Android Studio](https://developer.android.com/studio).
2. Open Android Studio and select **Open** -> choose `KeyboardSoundsAndroid`.
3. Wait for Gradle sync to complete.
4. In the top menu, go to **Build** -> **Build Bundle(s) / APK(s)** -> **Build APK(s)**.
5. Android Studio will generate `app-debug.apk`. Transfer this `.apk` to your phone and install!

### Option 2: Using GitHub Actions (No Android Studio required!)
This project includes a `.github/workflows/build_apk.yml` workflow:
1. Push this folder to a GitHub repository (Public or Private).
2. Go to the **Actions** tab in your repository.
3. Click **Build Android APK** -> **Run workflow**.
4. Once finished (~2 minutes), download the compiled **`KeyboardSounds-APK`** directly from the run artifacts!

### Option 3: Command Line
```bash
./gradlew assembleDebug
# The output APK will be in:
# app/build/outputs/apk/debug/app-debug.apk
```

---

## 📱 How to Enable on Your Phone

1. Install `app-debug.apk` on your Android device (allow "Install from unknown sources" if prompted).
2. Open the **Keyboard Sounds** app.
3. Tap **"Enable in Accessibility Settings"**.
4. In the Android Accessibility menu:
   - Tap **Installed Apps** (or **Downloaded Services** depending on your phone brand).
   - Find **Keyboard Sounds Typing Engine** and toggle it **ON**.
   - Tap **Allow**.
5. Return to the Keyboard Sounds app:
   - Select your favorite switch profile (e.g. *NovelKeys Cream* or *Cherry MX Red*).
   - Adjust volume and toggle haptic tactile feedback.
   - Type in the **Test Typing Area** at the bottom to verify the sound!
6. Now open **WhatsApp**, **Chrome**, or any app and start typing on your regular internal keyboard!

---

## 🔋 Keep Running in Background (MIUI / Samsung / OnePlus)

To prevent aggressive battery management from stopping the service:
- **Samsung:** Settings -> Apps -> Keyboard Sounds -> Battery -> set to **Unrestricted**.
- **Xiaomi (MIUI/HyperOS):** Settings -> Apps -> Keyboard Sounds -> Autostart -> toggle **ON**, and set Battery Saver to **No Restrictions**.
- **OnePlus / Realme / Oppo:** Long press app icon -> App info -> Battery usage -> Allow background activity.
