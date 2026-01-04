#!/usr/bin/env python3
"""
3D Print Converter - Desktop Application
A standalone GUI app for converting CAD files to G-code
"""

import os
import sys
import threading
import webbrowser
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess

class ConverterApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("3D Print Converter")
        self.root.geometry("500x350")
        self.root.resizable(False, False)

        # Dark theme colors
        self.bg_color = "#1a1a2e"
        self.fg_color = "#e0e0e0"
        self.accent = "#00d4ff"
        self.success = "#00ff88"
        self.error = "#ff4444"

        self.root.configure(bg=self.bg_color)

        self.server_process = None
        self.server_running = False

        self.setup_ui()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        # Title
        title_frame = tk.Frame(self.root, bg=self.bg_color)
        title_frame.pack(pady=20)

        tk.Label(
            title_frame,
            text="⚙",
            font=("Segoe UI", 32),
            fg=self.accent,
            bg=self.bg_color
        ).pack(side=tk.LEFT)

        tk.Label(
            title_frame,
            text=" 3D Print Converter",
            font=("Segoe UI", 20, "bold"),
            fg=self.accent,
            bg=self.bg_color
        ).pack(side=tk.LEFT)

        # Status indicator
        status_frame = tk.Frame(self.root, bg=self.bg_color)
        status_frame.pack(pady=10)

        self.status_dot = tk.Label(
            status_frame,
            text="●",
            font=("Segoe UI", 14),
            fg=self.error,
            bg=self.bg_color
        )
        self.status_dot.pack(side=tk.LEFT, padx=5)

        self.status_text = tk.Label(
            status_frame,
            text="Server Stopped",
            font=("Segoe UI", 11),
            fg="#888888",
            bg=self.bg_color
        )
        self.status_text.pack(side=tk.LEFT)

        # Buttons
        btn_frame = tk.Frame(self.root, bg=self.bg_color)
        btn_frame.pack(pady=25)

        self.start_btn = tk.Button(
            btn_frame,
            text="▶ Start Server",
            font=("Segoe UI", 11, "bold"),
            fg="#000000",
            bg=self.success,
            activebackground="#00cc66",
            width=14,
            height=2,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.toggle_server
        )
        self.start_btn.pack(side=tk.LEFT, padx=8)

        self.open_btn = tk.Button(
            btn_frame,
            text="🌐 Open App",
            font=("Segoe UI", 11, "bold"),
            fg="#000000",
            bg=self.accent,
            activebackground="#00aacc",
            width=14,
            height=2,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.open_webapp,
            state=tk.DISABLED
        )
        self.open_btn.pack(side=tk.LEFT, padx=8)

        # URL display
        url_frame = tk.Frame(self.root, bg="#0d0d1a", padx=15, pady=10)
        url_frame.pack(pady=15, padx=30, fill=tk.X)

        tk.Label(
            url_frame,
            text="Server URL:",
            font=("Segoe UI", 9),
            fg="#888888",
            bg="#0d0d1a"
        ).pack(side=tk.LEFT)

        self.url_entry = tk.Entry(
            url_frame,
            font=("Consolas", 10),
            fg=self.accent,
            bg="#0d0d1a",
            relief=tk.FLAT,
            width=30,
            state="readonly"
        )
        self.url_entry.pack(side=tk.LEFT, padx=10)
        self.url_entry.configure(readonlybackground="#0d0d1a")

        # Set URL
        self.url_entry.configure(state="normal")
        self.url_entry.insert(0, "http://localhost:8000")
        self.url_entry.configure(state="readonly")

        # Info text
        tk.Label(
            self.root,
            text="Convert PDF, DWG, DXF, SVG to G-code for 3D printing",
            font=("Segoe UI", 9),
            fg="#666666",
            bg=self.bg_color
        ).pack(pady=5)

        # Footer
        tk.Label(
            self.root,
            text="Tech Sierra Solutions",
            font=("Segoe UI", 8),
            fg="#444444",
            bg=self.bg_color
        ).pack(side=tk.BOTTOM, pady=10)

    def toggle_server(self):
        if self.server_running:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        self.status_text.config(text="Starting server...")
        self.root.update()

        # Find server.py
        if getattr(sys, 'frozen', False):
            # Running as EXE
            base_path = os.path.dirname(sys.executable)
        else:
            # Running as script
            base_path = os.path.dirname(os.path.abspath(__file__))

        server_path = os.path.join(base_path, "server", "server.py")

        if not os.path.exists(server_path):
            # Try parent directory
            server_path = os.path.join(os.path.dirname(base_path), "software", "server.py")

        if not os.path.exists(server_path):
            messagebox.showerror("Error", f"Server not found at:\n{server_path}")
            self.status_text.config(text="Server not found")
            return

        try:
            # Start server as subprocess
            self.server_process = subprocess.Popen(
                [sys.executable, server_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            # Wait a bit for server to start
            time.sleep(2)

            if self.server_process.poll() is None:
                self.server_running = True
                self.status_dot.config(fg=self.success)
                self.status_text.config(text="Server Running on port 8000")
                self.start_btn.config(text="■ Stop Server", bg="#ff6666")
                self.open_btn.config(state=tk.NORMAL)
            else:
                raise Exception("Server failed to start")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server:\n{e}")
            self.status_text.config(text="Failed to start")

    def stop_server(self):
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None

        self.server_running = False
        self.status_dot.config(fg=self.error)
        self.status_text.config(text="Server Stopped")
        self.start_btn.config(text="▶ Start Server", bg=self.success)
        self.open_btn.config(state=tk.DISABLED)

    def open_webapp(self):
        # First try the HTML app
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        html_path = os.path.join(base_path, "3D-Converter-App.html")

        if not os.path.exists(html_path):
            html_path = os.path.join(os.path.dirname(base_path), "3D-Converter-App.html")

        if os.path.exists(html_path):
            webbrowser.open(f"file:///{html_path}")
        else:
            # Fall back to API docs
            webbrowser.open("http://localhost:8000/docs")

    def on_close(self):
        if self.server_running:
            if messagebox.askyesno("Confirm Exit", "Stop server and exit?"):
                self.stop_server()
                self.root.destroy()
        else:
            self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ConverterApp()
    app.run()
