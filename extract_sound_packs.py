"""
Extract and decrypt all sound profiles from D:\\python project\\sounds\\sounds
into D:\\python project\\keyboard typing\\sounds\\<profile_name>\\down and \\up.
"""

import glob
import os
import sys
import wave

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEST_SOUNDS_DIR = os.path.join(SCRIPT_DIR, "sounds")
SRC_SOUNDS_DIR = r"D:\python project\sounds\sounds"

c1 = b'"BmL9aJv7XcY4tK`Wz'
c2 = b'2B}L9qJf7YsY$uKqWj'
c3 = b'2BmL)qJw7HsX4t[qWz'
c4 = b'2RmL9qZv7XsI4tKpGz'
c5 = b"2Bm\\9qJv'XsY4dKpWz"
MASTER = c1 + c2 + c3 + c4 + c5
MASTER_LEN = len(MASTER)  # 90


def decrypt_ksnd_to_wav(in_path, out_path):
    with open(in_path, "rb") as f:
        data = f.read()

    if not data:
        return

    # Find the best offset for the 90-byte stream cipher
    # Compare both header and tail against master stream
    check_len = min(60, len(data))
    head = data[:check_len]
    tail = data[-check_len:]
    tail_offset_base = (len(data) - len(tail)) % MASTER_LEN

    best_offset = 0
    best_score = -1

    for offset in range(MASTER_LEN):
        # Header score
        s_head = sum(
            1
            for i in range(len(head))
            if head[i] == MASTER[(offset + i) % MASTER_LEN]
            or (head[i] ^ 0xFF) == MASTER[(offset + i) % MASTER_LEN]
        )
        # Tail score
        s_tail = sum(
            1
            for i in range(len(tail))
            if tail[i] == MASTER[(offset + tail_offset_base + i) % MASTER_LEN]
            or (tail[i] ^ 0xFF) == MASTER[(offset + tail_offset_base + i) % MASTER_LEN]
        )
        total = s_head + s_tail
        if total > best_score:
            best_score = total
            best_offset = offset

    # Decrypt with the best stream alignment
    decrypted = bytearray(len(data))
    for i in range(len(data)):
        decrypted[i] = data[i] ^ MASTER[(best_offset + i) % MASTER_LEN]

    # Ensure even number of bytes for 16-bit PCM
    if len(decrypted) % 2 != 0:
        decrypted = decrypted[:-1]

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with wave.open(out_path, "wb") as wav:
        wav.setnchannels(1)  # Mono
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(44100)  # 44.1 kHz
        wav.writeframes(decrypted)


def convert_all_packs():
    if not os.path.isdir(SRC_SOUNDS_DIR):
        print(f"Source folder not found: {SRC_SOUNDS_DIR}")
        return

    pack_folders = [
        d
        for d in sorted(os.listdir(SRC_SOUNDS_DIR))
        if os.path.isdir(os.path.join(SRC_SOUNDS_DIR, d)) and not d.startswith(".")
    ]

    print(f"Found packs to convert: {pack_folders}")
    total_converted = 0

    for pack in pack_folders:
        src_pack_dir = os.path.join(SRC_SOUNDS_DIR, pack)
        # Clean folder name for profile (e.g. "Cardboard", "Crystal Purple")
        dest_pack_dir = os.path.join(DEST_SOUNDS_DIR, pack)

        for sub in ["down", "up"]:
            pattern = os.path.join(src_pack_dir, f"*-{sub}.ksnd")
            files = sorted(glob.glob(pattern))
            if not files:
                continue

            dest_sub_dir = os.path.join(dest_pack_dir, sub)
            os.makedirs(dest_sub_dir, exist_ok=True)

            print(f"Converting {pack} -> {sub} ({len(files)} sounds)...")
            for f in files:
                base_name = os.path.splitext(os.path.basename(f))[0]
                out_file = os.path.join(dest_sub_dir, f"{base_name}.wav")
                decrypt_ksnd_to_wav(f, out_file)
                total_converted += 1

    print(f"\nAll done! Successfully converted {total_converted} sounds into {DEST_SOUNDS_DIR}")


if __name__ == "__main__":
    convert_all_packs()
