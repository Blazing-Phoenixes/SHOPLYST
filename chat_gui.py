# chat_gui.py
import tkinter as tk
from tkinter import scrolledtext, filedialog, Menu
from datetime import datetime
import os
import sys
import subprocess
from PIL import Image, ImageTk

from sm_database import send_message, get_conversation, mark_messages_as_read, save_user_image

# COLORS
BG_MAIN = "#0f172a"
CARD = "#111827"
PRIMARY = "#6366f1"
TEXT = "#e5e7eb"
SUBTEXT = "#9ca3af"
INPUT_BG = "#1f2937"
INPUT_BORDER = "#374151"

MY_MSG = "#4f46e5"
OTHER_MSG = "#374151"

TITLE_FONT = ("Segoe UI", 15, "bold")
TEXT_FONT = ("Segoe UI", 11)
ENTRY_FONT = ("Segoe UI", 12)


# ✅ BASE DIR (EXE + PY)
def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


class ChatFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_MAIN)
        self.app = app

        self.sender = None
        self.receiver = None
        self.refresh_interval_ms = 3000

        self.images_cache = []

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # HEADER
        header = tk.Frame(self, bg="#020617", height=60)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        self.avatar = tk.Label(header, text="👤",
                               bg="#020617", fg="white",
                               font=("Segoe UI", 18, "bold"))
        self.avatar.grid(row=0, column=0, padx=10)

        self.title_label = tk.Label(header, text="",
                                   font=TITLE_FONT,
                                   bg="#020617", fg=TEXT)
        self.title_label.grid(row=0, column=1, sticky="w")

        tk.Button(header, text="←",
                  bg=PRIMARY, fg="white",
                  font=("Segoe UI", 11, "bold"),
                  relief="flat",
                  command=lambda: self.app.show_frame("HomeFrame", user=self.sender))\
            .grid(row=0, column=2, padx=10)

        # CHAT AREA
        container = tk.Frame(self, bg=BG_MAIN)
        container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        self.chat_area = scrolledtext.ScrolledText(
            container,
            wrap=tk.WORD,
            font=TEXT_FONT,
            bg=CARD,
            fg=TEXT,
            relief="flat",
            padx=15,
            pady=10,
            insertbackground="white"
        )
        self.chat_area.pack(fill="both", expand=True)
        self.chat_area.config(state=tk.DISABLED)

        # MENU
        self.menu = Menu(self, tearoff=0)
        self.menu.add_command(label="❤️ React", command=lambda: self.react("❤️"))
        self.menu.add_command(label="👍 React", command=lambda: self.react("👍"))
        self.menu.add_command(label="😂 React", command=lambda: self.react("😂"))
        self.menu.add_separator()
        self.menu.add_command(label="🗑 Delete", command=self.delete_message)

        self.chat_area.bind("<Button-3>", self.show_menu)

        # INPUT
        bottom = tk.Frame(self, bg=BG_MAIN)
        bottom.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        bottom.grid_columnconfigure(0, weight=1)

        self.entry = tk.Entry(bottom, font=ENTRY_FONT,
                              bg=INPUT_BG, fg="white",
                              insertbackground="white",
                              relief="flat")
        self.entry.grid(row=0, column=0, sticky="ew", padx=5, ipady=10)

        self.entry.bind("<Return>", self.send_msg)

        tk.Button(bottom, text="Send",
                  bg=PRIMARY, fg="white",
                  command=self.send_msg)\
            .grid(row=0, column=1, padx=5)

        tk.Button(bottom, text="📎",
                  bg="#020617", fg="white",
                  command=self.send_file)\
            .grid(row=0, column=2, padx=5)

    # LOAD
    def load_data(self, sender=None, receiver=None):
        self.sender = sender
        self.receiver = receiver
        self.title_label.config(text=receiver)
        self.avatar.config(text=receiver[0].upper())
        self.load_messages()
        self.auto_refresh()

    # LOAD MESSAGES
    def load_messages(self):
        if not self.sender or not self.receiver:
            return

        mark_messages_as_read(self.receiver, self.sender)
        messages = get_conversation(self.sender, self.receiver)

        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.delete(1.0, tk.END)

        for sender, message, time in messages:
            is_me = sender == self.sender

            # ✅ FILE HANDLING
            if message.startswith("[File]|"):
                file_path = message.split("|", 1)[1].strip()
                self.insert_file_preview(file_path, is_me)
                continue

            time_fmt = datetime.strptime(time, "%Y-%m-%d %H:%M:%S").strftime("%I:%M %p")
            bubble = f"{message}\n{time_fmt}"

            if is_me:
                bubble += " ✓✓"

            self.insert_bubble(bubble, is_me)

        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.yview(tk.END)

    # ✅ FILE PREVIEW ENGINE
    def insert_file_preview(self, file_path, is_me):
        ext = file_path.lower()

        if ext.endswith((".png", ".jpg", ".jpeg", ".gif")):
            self.insert_image(file_path, is_me)

        elif ext.endswith(".pdf"):
            self.insert_clickable_file(file_path, "📄 PDF File", is_me)

        elif ext.endswith((".mp4", ".avi", ".mkv")):
            self.insert_clickable_file(file_path, "🎬 Video File", is_me)

        else:
            self.insert_clickable_file(file_path, "📁 File", is_me)

    # IMAGE
    def insert_image(self, file_path, is_me):
        try:
            full_path = os.path.join(get_base_dir(), file_path)

            if not os.path.exists(full_path):
                self.insert_bubble("[Image not found]", is_me)
                return

            img = Image.open(full_path)
            img.thumbnail((200, 200))
            img_tk = ImageTk.PhotoImage(img)

            self.images_cache.append(img_tk)

            self.chat_area.insert(tk.END, "\n")
            self.chat_area.image_create(tk.END, image=img_tk)
            self.chat_area.insert(tk.END, "\n")

            # click to open
            self.chat_area.insert(tk.END, "[Open Image]\n")
            self.make_last_line_clickable(lambda p=full_path: self.open_file(p))

        except Exception as e:
            self.insert_bubble(f"[Error loading image]\n{e}", is_me)

    # ✅ CLICKABLE FILE
    def insert_clickable_file(self, file_path, label, is_me):
        full_path = os.path.join(get_base_dir(), file_path)

        text = f"{label}\n{os.path.basename(file_path)}\n[Click to open]\n"
        self.insert_bubble(text, is_me)

        self.make_last_line_clickable(lambda p=full_path: self.open_file(p))

    # CLICK BIND
    def make_last_line_clickable(self, callback):
        start = self.chat_area.index("end-2l linestart")
        end = self.chat_area.index("end-1l lineend")

        tag = f"link_{start}"
        self.chat_area.tag_add(tag, start, end)
        self.chat_area.tag_config(tag, foreground="cyan", underline=1)
        self.chat_area.tag_bind(tag, "<Button-1>", lambda e: callback())

    # OPEN FILE
    def open_file(self, path):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            else:
                subprocess.call(["xdg-open", path])
        except Exception as e:
            print("Error opening file:", e)

    # BUBBLE
    def insert_bubble(self, text, is_me):
        tag = "me" if is_me else "them"

        self.chat_area.insert(tk.END, "\n")
        start = self.chat_area.index(tk.END)
        self.chat_area.insert(tk.END, text)
        end = self.chat_area.index(tk.END)

        self.chat_area.tag_add(tag, start, end)

        if is_me:
            self.chat_area.tag_config(tag, background=MY_MSG, lmargin1=120)
        else:
            self.chat_area.tag_config(tag, background=OTHER_MSG, lmargin1=10)

    # SEND
    def send_msg(self, event=None):
        msg = self.entry.get().strip()
        if msg:
            send_message(self.sender, self.receiver, msg)
            self.entry.delete(0, tk.END)
            self.load_messages()

    # FILE SEND
    def send_file(self):
        file_path = filedialog.askopenfilename()

        if file_path:
            saved_path = save_user_image(self.sender, file_path)
            msg = f"[File]|{saved_path}"

            send_message(self.sender, self.receiver, msg)
            self.load_messages()

    # MENU
    def show_menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)

    def react(self, emoji):
        self.chat_area.insert(tk.END, f" {emoji}")

    def delete_message(self):
        self.chat_area.insert(tk.END, "\n[Message deleted]\n")

    def auto_refresh(self):
        self.load_messages()
        self.after(self.refresh_interval_ms, self.auto_refresh)