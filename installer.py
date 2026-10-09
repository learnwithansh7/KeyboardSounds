"""
Keyboard Sounds - Standalone Windows Setup Installer
---------------------------------------------------
Installs Keyboard Sounds to %LOCALAPPDATA%\\KeyboardSounds,
extracts all sound profiles and runtime files, creates Desktop,
Start Menu, and Startup shortcuts, and registers in Windows
Settings / Control Panel (Add/Remove Programs).
"""

import os
import sys
import shutil
import zipfile
import threading
import subprocess
import winreg
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


def get_default_install_dir():
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        local_app_data = os.path.expanduser("~\\AppData\\Local")
    return os.path.join(local_app_data, "KeyboardSounds")


def get_shell_folders():
    """Retrieve actual Windows Shell folder paths (handles OneDrive redirection)."""
    folders = {
        "Desktop": os.path.join(os.environ.get("USERPROFILE", ""), "Desktop"),
        "Programs": os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
        "Startup": os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup"),
    }
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        ) as k:
            for name in ("Desktop", "Programs", "Startup"):
                try:
                    val, _ = winreg.QueryValueEx(k, name)
                    expanded = os.path.expandvars(val)
                    if os.path.exists(expanded):
                        folders[name] = expanded
                except Exception:
                    pass
    except Exception:
        pass
    return folders


def get_payload_path():
    # 1. Bundled via PyInstaller _MEIPASS
    if hasattr(sys, "_MEIPASS"):
        p = os.path.join(sys._MEIPASS, "payload.zip")
        if os.path.exists(p):
            return p
    # 2. Next to executable
    exe_dir = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
    p = os.path.join(exe_dir, "payload.zip")
    if os.path.exists(p):
        return p
    # 3. Project directory
    p = r"D:\python project\keyboard typing\payload.zip"
    if os.path.exists(p):
        return p
    return None


def kill_existing_instances():
    """Terminate existing KeyboardSounds or klack_clone processes to unlock files."""
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command",
             "Get-Process KeyboardSounds -ErrorAction SilentlyContinue | Stop-Process -Force;"
             "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*klack_clone*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
    except Exception:
        pass


def create_shortcut(target_exe, shortcut_path, icon_path=None, work_dir=None, desc=""):
    work_dir = work_dir or os.path.dirname(target_exe)
    icon_arg = f'$Shortcut.IconLocation = "{icon_path}"; ' if (icon_path and os.path.exists(icon_path)) else ""
    cmd = (
        f'$WshShell = New-Object -ComObject WScript.Shell; '
        f'$Shortcut = $WshShell.CreateShortcut("{shortcut_path}"); '
        f'$Shortcut.TargetPath = "{target_exe}"; '
        f'$Shortcut.WorkingDirectory = "{work_dir}"; '
        f'{icon_arg}'
        f'$Shortcut.Description = "{desc}"; '
        f'$Shortcut.Save()'
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", cmd],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )


def register_uninstaller(install_dir, exe_path, icon_path, folders):
    """Register in Windows Settings / Control Panel (Add or Remove Programs)."""
    reg_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\KeyboardSounds"
    try:
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "Keyboard Sounds (Klack Clone)")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Mechanical Keyboard Simulator")
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, install_dir)
            if icon_path and os.path.exists(icon_path):
                winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, icon_path)
            uninst_cmd = f'powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File "{os.path.join(install_dir, "uninstall.ps1")}"'
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, uninst_cmd)
            winreg.SetValueEx(key, "QuietUninstallString", 0, winreg.REG_SZ, f'{uninst_cmd} -Silent')
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
    except Exception as e:
        print(f"Failed to register uninstaller in registry: {e}")


def write_uninstaller_scripts(install_dir, folders):
    """Create clean PowerShell and batch uninstallers."""
    ps1_path = os.path.join(install_dir, "uninstall.ps1")
    desk_lnk = os.path.join(folders["Desktop"], "Keyboard Sounds.lnk")
    prog_lnk = os.path.join(folders["Programs"], "Keyboard Sounds.lnk")
    uninst_lnk = os.path.join(folders["Programs"], "Uninstall Keyboard Sounds.lnk")
    startup_lnk = os.path.join(folders["Startup"], "KeyboardSounds.lnk")

    ps1_content = f'''param([switch]$Silent)

if (-not $Silent) {{
    $ans = [System.Windows.Forms.MessageBox]::Show(
        "Are you sure you want to completely uninstall Keyboard Sounds?",
        "Uninstall Keyboard Sounds",
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Question
    )
    if ($ans -ne [System.Windows.Forms.DialogResult]::Yes) {{ exit }}
}}

# Stop running process
Get-Process KeyboardSounds -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 500

# Remove shortcuts
Remove-Item "{desk_lnk}" -Force -ErrorAction SilentlyContinue
Remove-Item "{prog_lnk}" -Force -ErrorAction SilentlyContinue
Remove-Item "{uninst_lnk}" -Force -ErrorAction SilentlyContinue
Remove-Item "{startup_lnk}" -Force -ErrorAction SilentlyContinue

# Remove Registry Entries
Remove-Item "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\KeyboardSounds" -Recurse -Force -ErrorAction SilentlyContinue
Remove-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" -Name "KeyboardSounds" -ErrorAction SilentlyContinue

# Remove files and self
$installDir = "{install_dir}"
Start-Process -FilePath "cmd.exe" -ArgumentList "/c timeout /t 1 /nobreak >nul & rd /s /q `"$installDir`"" -WindowStyle Hidden

if (-not $Silent) {{
    [System.Windows.Forms.MessageBox]::Show(
        "Keyboard Sounds has been removed from your computer.",
        "Uninstall Complete",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Information
    )
}}
'''
    with open(ps1_path, "w", encoding="utf-8") as f:
        f.write(ps1_content)


def perform_install(target_dir, create_desktop, create_startmenu, enable_autostart, launch_after, progress_callback, finish_callback):
    try:
        folders = get_shell_folders()

        progress_callback(10, "Stopping existing instances...")
        kill_existing_instances()

        progress_callback(20, "Preparing installation folder...")
        os.makedirs(target_dir, exist_ok=True)

        payload_path = get_payload_path()
        if not payload_path or not os.path.exists(payload_path):
            raise FileNotFoundError("Installation payload.zip not found!")

        progress_callback(30, "Extracting application and sound packs...")
        with zipfile.ZipFile(payload_path, "r") as zf:
            total_files = len(zf.namelist())
            for idx, member in enumerate(zf.namelist()):
                zf.extract(member, target_dir)
                if idx % 60 == 0:
                    pct = 30 + int((idx / max(total_files, 1)) * 45)
                    progress_callback(pct, f"Extracting {os.path.basename(member)}...")

        exe_path = os.path.join(target_dir, "KeyboardSounds.exe")
        icon_path = os.path.join(target_dir, "app_icon.ico")
        if not os.path.exists(icon_path):
            icon_path = exe_path

        progress_callback(80, "Configuring uninstaller...")
        write_uninstaller_scripts(target_dir, folders)
        register_uninstaller(target_dir, exe_path, icon_path, folders)

        progress_callback(90, "Creating shortcuts...")
        if create_desktop:
            desk_path = os.path.join(folders["Desktop"], "Keyboard Sounds.lnk")
            try:
                create_shortcut(exe_path, desk_path, icon_path, target_dir, "Mechanical Keyboard Sound Simulator")
            except Exception:
                pass

        if create_startmenu:
            start_menu_path = os.path.join(folders["Programs"], "Keyboard Sounds.lnk")
            try:
                create_shortcut(exe_path, start_menu_path, icon_path, target_dir, "Mechanical Keyboard Sound Simulator")
            except Exception:
                pass

        if enable_autostart:
            startup_path = os.path.join(folders["Startup"], "KeyboardSounds.lnk")
            try:
                create_shortcut(exe_path, startup_path, icon_path, target_dir, "Mechanical Keyboard Sound Simulator (24/7)")
            except Exception:
                pass
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as rk:
                    winreg.SetValueEx(rk, "KeyboardSounds", 0, winreg.REG_SZ, f'"{exe_path}"')
            except Exception:
                pass

        progress_callback(95, "Finalizing installation...")
        if launch_after and os.path.exists(exe_path):
            try:
                subprocess.Popen(["explorer.exe", exe_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                try:
                    os.startfile(exe_path)
                except Exception:
                    pass

        progress_callback(100, "Installation Complete!")
        finish_callback(True, "Installation completed successfully!")
    except Exception as e:
        finish_callback(False, str(e))


class InstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Keyboard Sounds Setup")
        self.root.geometry("540x510")
        self.root.resizable(False, False)
        self.root.configure(bg="#18181b")

        # Center on screen
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"+{x}+{y}")

        self.setup_ui()

    def setup_ui(self):
        # Header banner
        header = tk.Frame(self.root, bg="#27272a", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_lbl = tk.Label(
            header,
            text="⌨  Keyboard Sounds Setup",
            font=("Segoe UI", 16, "bold"),
            fg="#f4f4f5",
            bg="#27272a"
        )
        title_lbl.pack(anchor="w", padx=24, pady=(16, 2))

        sub_lbl = tk.Label(
            header,
            text="Install Mechanical Keyboard Sound Simulator on your PC",
            font=("Segoe UI", 9),
            fg="#a1a1aa",
            bg="#27272a"
        )
        sub_lbl.pack(anchor="w", padx=24)

        # Main content
        content = tk.Frame(self.root, bg="#18181b")
        content.pack(fill=tk.BOTH, expand=True, padx=24, pady=16)

        # Destination Folder Frame
        folder_lbl = tk.Label(
            content,
            text="Destination Folder:",
            font=("Segoe UI", 10, "bold"),
            fg="#e4e4e7",
            bg="#18181b"
        )
        folder_lbl.pack(anchor="w", pady=(0, 4))

        path_frame = tk.Frame(content, bg="#18181b")
        path_frame.pack(fill=tk.X, pady=(0, 16))

        self.path_var = tk.StringVar(value=get_default_install_dir())
        self.path_entry = tk.Entry(
            path_frame,
            textvariable=self.path_var,
            font=("Segoe UI", 9),
            bg="#27272a",
            fg="#fafafa",
            insertbackground="#fafafa",
            relief=tk.FLAT,
            bd=6
        )
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        browse_btn = tk.Button(
            path_frame,
            text="Browse...",
            command=self.browse_folder,
            font=("Segoe UI", 9),
            bg="#3f3f46",
            fg="#f4f4f5",
            relief=tk.FLAT,
            padx=12,
            pady=4,
            cursor="hand2"
        )
        browse_btn.pack(side=tk.RIGHT)

        # Options Frame
        opts_lbl = tk.Label(
            content,
            text="Installation Options:",
            font=("Segoe UI", 10, "bold"),
            fg="#e4e4e7",
            bg="#18181b"
        )
        opts_lbl.pack(anchor="w", pady=(0, 6))

        self.desktop_var = tk.BooleanVar(value=True)
        self.startmenu_var = tk.BooleanVar(value=True)
        self.autostart_var = tk.BooleanVar(value=True)
        self.launch_var = tk.BooleanVar(value=True)

        cb1 = tk.Checkbutton(
            content, text="Create Desktop Shortcut",
            variable=self.desktop_var, font=("Segoe UI", 9),
            bg="#18181b", fg="#d4d4d8", selectcolor="#27272a", activebackground="#18181b", activeforeground="#ffffff"
        )
        cb1.pack(anchor="w", pady=2)

        cb2 = tk.Checkbutton(
            content, text="Create Start Menu Shortcut",
            variable=self.startmenu_var, font=("Segoe UI", 9),
            bg="#18181b", fg="#d4d4d8", selectcolor="#27272a", activebackground="#18181b", activeforeground="#ffffff"
        )
        cb2.pack(anchor="w", pady=2)

        cb3 = tk.Checkbutton(
            content, text="Start automatically with Windows (runs 24/7 in background)",
            variable=self.autostart_var, font=("Segoe UI", 9),
            bg="#18181b", fg="#10b981", selectcolor="#27272a", activebackground="#18181b", activeforeground="#10b981"
        )
        cb3.pack(anchor="w", pady=2)

        cb4 = tk.Checkbutton(
            content, text="Launch Keyboard Sounds immediately after install",
            variable=self.launch_var, font=("Segoe UI", 9),
            bg="#18181b", fg="#d4d4d8", selectcolor="#27272a", activebackground="#18181b", activeforeground="#ffffff"
        )
        cb4.pack(anchor="w", pady=2)

        # Progress bar & status
        self.status_lbl = tk.Label(
            content,
            text="Ready to install.",
            font=("Segoe UI", 9),
            fg="#a1a1aa",
            bg="#18181b"
        )
        self.status_lbl.pack(anchor="w", pady=(16, 4))

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Green.Horizontal.TProgressbar", background="#10b981", troughcolor="#27272a", bordercolor="#18181b", thickness=12)

        self.progress = ttk.Progressbar(content, style="Green.Horizontal.TProgressbar", mode="determinate")
        self.progress.pack(fill=tk.X, pady=(0, 16))

        # Bottom Buttons Frame
        btn_frame = tk.Frame(self.root, bg="#27272a", height=60)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        btn_frame.pack_propagate(False)

        self.cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            command=self.root.destroy,
            font=("Segoe UI", 9),
            bg="#3f3f46",
            fg="#f4f4f5",
            relief=tk.FLAT,
            padx=16,
            pady=6,
            cursor="hand2"
        )
        self.cancel_btn.pack(side=tk.RIGHT, padx=(0, 24), pady=14)

        self.install_btn = tk.Button(
            btn_frame,
            text="Install",
            command=self.start_installation,
            font=("Segoe UI", 10, "bold"),
            bg="#10b981",
            fg="#ffffff",
            relief=tk.FLAT,
            padx=24,
            pady=6,
            cursor="hand2"
        )
        self.install_btn.pack(side=tk.RIGHT, padx=(0, 12), pady=14)

    def browse_folder(self):
        chosen = filedialog.askdirectory(initialdir=self.path_var.get())
        if chosen:
            self.path_var.set(os.path.join(chosen, "KeyboardSounds"))

    def update_progress(self, pct, message):
        def _update():
            self.progress["value"] = pct
            self.status_lbl.configure(text=message)
        self.root.after(0, _update)

    def on_finish(self, success, message):
        def _finish():
            if success:
                self.progress["value"] = 100
                self.status_lbl.configure(text="✔ " + message, fg="#10b981")
                self.install_btn.configure(text="Finish", command=self.root.destroy, bg="#10b981")
                self.cancel_btn.pack_forget()
                messagebox.showinfo(
                    "Setup Complete",
                    "Keyboard Sounds has been installed successfully!\n\n"
                    "Hotkeys:\n"
                    " • Ctrl + Alt + K : Open Sound Switcher\n"
                    " • Ctrl + Alt + M : Quick Mute / Unmute"
                )
            else:
                self.status_lbl.configure(text="❌ Error: " + message, fg="#ef4444")
                self.install_btn.configure(state=tk.NORMAL)
                messagebox.showerror("Installation Failed", message)
        self.root.after(0, _finish)

    def start_installation(self):
        target = self.path_var.get().strip()
        if not target:
            messagebox.showerror("Error", "Please choose a valid destination folder.")
            return

        self.install_btn.configure(state=tk.DISABLED)
        self.path_entry.configure(state=tk.DISABLED)

        t = threading.Thread(
            target=perform_install,
            args=(
                target,
                self.desktop_var.get(),
                self.startmenu_var.get(),
                self.autostart_var.get(),
                self.launch_var.get(),
                self.update_progress,
                self.on_finish,
            ),
            daemon=True
        )
        t.start()


def main():
    # Silent install mode
    if "/S" in sys.argv or "/SILENT" in sys.argv or "--silent" in sys.argv:
        target = get_default_install_dir()
        def dummy_progress(p, m): pass
        def dummy_finish(s, m):
            sys.exit(0 if s else 1)
        perform_install(target, True, True, True, True, dummy_progress, dummy_finish)
        return

    root = tk.Tk()
    app = InstallerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
