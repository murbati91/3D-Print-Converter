#!/usr/bin/env python3
"""
3D Print Converter - EXE Builder
Creates a standalone executable using PyInstaller
"""

import os
import sys
import subprocess
import shutil

def main():
    print("=" * 50)
    print("  3D Print Converter - EXE Builder")
    print("=" * 50)
    print()

    # Check PyInstaller
    try:
        import PyInstaller
        print("[OK] PyInstaller found")
    except ImportError:
        print("[!] Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    server_dir = os.path.join(project_dir, "software")
    output_dir = os.path.join(project_dir, "dist")

    # Create the main launcher script
    launcher_path = os.path.join(script_dir, "launcher.py")

    print(f"[1/4] Creating launcher script...")

    with open(launcher_path, "w") as f:
        f.write('''
import os
import sys
import threading
import webbrowser
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import urllib.request
import json

# Add the bundled server to path
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, os.path.join(base_path, 'server'))

class ConverterApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("3D Print Converter")
        self.root.geometry("600x400")
        self.root.configure(bg="#1a1a2e")

        self.server_running = False
        self.server_thread = None

        self.setup_ui()

    def setup_ui(self):
        # Title
        title = tk.Label(
            self.root,
            text="3D Print Converter",
            font=("Segoe UI", 24, "bold"),
            fg="#00d4ff",
            bg="#1a1a2e"
        )
        title.pack(pady=20)

        # Status
        self.status_frame = tk.Frame(self.root, bg="#1a1a2e")
        self.status_frame.pack(pady=10)

        self.status_dot = tk.Label(
            self.status_frame,
            text="●",
            font=("Segoe UI", 16),
            fg="#ff4444",
            bg="#1a1a2e"
        )
        self.status_dot.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(
            self.status_frame,
            text="Server Stopped",
            font=("Segoe UI", 12),
            fg="#888888",
            bg="#1a1a2e"
        )
        self.status_label.pack(side=tk.LEFT)

        # Buttons
        btn_frame = tk.Frame(self.root, bg="#1a1a2e")
        btn_frame.pack(pady=30)

        self.start_btn = tk.Button(
            btn_frame,
            text="Start Server",
            font=("Segoe UI", 12, "bold"),
            fg="#000000",
            bg="#00ff88",
            activebackground="#00cc66",
            width=15,
            height=2,
            command=self.start_server
        )
        self.start_btn.pack(side=tk.LEFT, padx=10)

        self.open_btn = tk.Button(
            btn_frame,
            text="Open Web App",
            font=("Segoe UI", 12, "bold"),
            fg="#000000",
            bg="#00d4ff",
            activebackground="#00aacc",
            width=15,
            height=2,
            command=self.open_webapp,
            state=tk.DISABLED
        )
        self.open_btn.pack(side=tk.LEFT, padx=10)

        # Info
        info = tk.Label(
            self.root,
            text="Convert PDF, DWG, DXF, SVG files to G-code",
            font=("Segoe UI", 10),
            fg="#666666",
            bg="#1a1a2e"
        )
        info.pack(pady=20)

        # Server URL
        url_frame = tk.Frame(self.root, bg="#1a1a2e")
        url_frame.pack(pady=10)

        tk.Label(
            url_frame,
            text="Server URL:",
            font=("Segoe UI", 10),
            fg="#888888",
            bg="#1a1a2e"
        ).pack(side=tk.LEFT)

        self.url_label = tk.Label(
            url_frame,
            text="http://localhost:8000",
            font=("Segoe UI", 10, "underline"),
            fg="#00d4ff",
            bg="#1a1a2e",
            cursor="hand2"
        )
        self.url_label.pack(side=tk.LEFT, padx=5)
        self.url_label.bind("<Button-1>", lambda e: self.open_webapp())

    def start_server(self):
        if self.server_running:
            return

        self.status_label.config(text="Starting server...")
        self.root.update()

        def run_server():
            try:
                import uvicorn
                from server import app
                uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
            except Exception as e:
                print(f"Server error: {e}")

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

        # Wait for server to start
        time.sleep(2)

        self.server_running = True
        self.status_dot.config(fg="#00ff88")
        self.status_label.config(text="Server Running")
        self.start_btn.config(state=tk.DISABLED, bg="#666666")
        self.open_btn.config(state=tk.NORMAL)

    def open_webapp(self):
        webbrowser.open("http://localhost:8000/docs")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ConverterApp()
    app.run()
''')

    print(f"[2/4] Copying server files...")

    # Create server package in build dir
    build_server_dir = os.path.join(script_dir, "server")
    os.makedirs(build_server_dir, exist_ok=True)

    # Copy server files
    shutil.copy(os.path.join(server_dir, "server.py"), build_server_dir)
    shutil.copy(os.path.join(server_dir, "converter_engine.py"), build_server_dir)

    # Create __init__.py
    with open(os.path.join(build_server_dir, "__init__.py"), "w") as f:
        f.write("from .server import app\n")

    print(f"[3/4] Building EXE with PyInstaller...")

    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "3D-Print-Converter",
        "--add-data", f"{build_server_dir};server",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        "--distpath", output_dir,
        "--workpath", os.path.join(script_dir, "build"),
        "--specpath", script_dir,
        launcher_path
    ]

    subprocess.run(cmd, check=True, cwd=script_dir)

    print(f"[4/4] Cleaning up...")

    # Copy HTML app to dist
    html_src = os.path.join(project_dir, "3D-Converter-App.html")
    if os.path.exists(html_src):
        shutil.copy(html_src, output_dir)

    print()
    print("=" * 50)
    print("  BUILD COMPLETE!")
    print("=" * 50)
    print(f"  EXE location: {os.path.join(output_dir, '3D-Print-Converter.exe')}")
    print()

if __name__ == "__main__":
    main()
