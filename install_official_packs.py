import io
import os
import shutil
import subprocess
import urllib.request
import zipfile

SCRIPT_DIR = r"D:\python project\keyboard typing"
SOUNDS_DIR = os.path.join(SCRIPT_DIR, "sounds")

PACK_MAP = {
    "nk_cream": "Cream",
    "eg_crystal_purple": "Crystal Purple",
    "cherry_mx_black_abs": "Japanese Black",
    "cherry_mx_brown_abs": "Cherry MX Brown",
    "cherry_mx_red_abs": "Cherry MX Red",
    "glorious_panda": "Holy Panda",
    "kailh_box_white": "Kailh Box White",
    "unicomp_classic": "Buckling Spring",
    "tealios_v2": "Tealios V2",
}


def install_packs():
    url = "https://github.com/dusklinux/wayclick_soundpacks/archive/refs/heads/main.zip"
    print("Downloading authentic mechanical keyboard sound packs from GitHub...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        data = resp.read()

    print(f"Downloaded {len(data) / (1024*1024):.1f} MB.")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for repo_pack, display_name in PACK_MAP.items():
            dest_down = os.path.join(SOUNDS_DIR, display_name, "down")
            if os.path.exists(os.path.join(SOUNDS_DIR, display_name)):
                shutil.rmtree(os.path.join(SOUNDS_DIR, display_name))
            os.makedirs(dest_down, exist_ok=True)

            prefix = f"wayclick_soundpacks-main/{repo_pack}/"
            count = 0
            for name in z.namelist():
                if not name.startswith(prefix):
                    continue
                ext = os.path.splitext(name)[1].lower()
                if ext not in [".wav", ".ogg", ".mp3"]:
                    continue

                filename = os.path.basename(name)
                temp_file = os.path.join(dest_down, filename)
                with z.open(name) as src_f, open(temp_file, "wb") as dst_f:
                    dst_f.write(src_f.read())

                # Convert to .wav if not already .wav
                if ext != ".wav":
                    wav_file = os.path.splitext(temp_file)[0] + ".wav"
                    try:
                        subprocess.run(
                            ["ffmpeg", "-y", "-i", temp_file, "-ar", "44100", "-ac", "1", wav_file],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            check=True,
                        )
                        os.remove(temp_file)
                    except Exception:
                        pass
                count += 1
            print(f"Installed {display_name}: {count} sounds into down/")

    print("\nAll mechanical sound packs installed and converted!")


if __name__ == "__main__":
    install_packs()
