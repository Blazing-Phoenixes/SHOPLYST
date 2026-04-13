import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageOps
import os

# 🎨 COLORS
BACKGROUND = "#0f172a"
CARD = "#1e293b"
TEXT = "#e2e8f0"
SUBTEXT = "#94a3b8"
ACCENT = "#22c55e"
BUTTON = "#6366f1"
BUTTON_HOVER = "#4f46e5"
SHADOW = "#020617"

# FONTS
FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_SUBTITLE = ("Segoe UI", 16, "bold")
FONT_TEXT = ("Segoe UI", 13)


class HoverButton(tk.Button):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.default_bg = kwargs.get("bg", BUTTON)
        self.hover_bg = kwargs.get("activebackground", BUTTON_HOVER)

        self.bind("<Enter>", lambda e: self.config(bg=self.hover_bg))
        self.bind("<Leave>", lambda e: self.config(bg=self.default_bg))


class ProductDetailsScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BACKGROUND)
        self.app = app

        # SCROLL SETUP
        self.canvas = tk.Canvas(self, bg=BACKGROUND, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)

        self.scrollable_frame = tk.Frame(self.canvas, bg=BACKGROUND)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.bind("<Configure>", self.on_resize)

        # ✅ Enable scroll
        self.bind_mousewheel(self.canvas)

    # ---------------- RESPONSIVE WIDTH ----------------
    def on_resize(self, event):
        self.canvas.itemconfig(self.window, width=event.width)

    # ---------------- SCROLL FIX ----------------
    def bind_mousewheel(self, widget):
        def _on_mousewheel(event):
            widget.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind(event):
            widget.bind_all("<MouseWheel>", _on_mousewheel)
            widget.bind_all("<Button-4>", lambda e: widget.yview_scroll(-1, "units"))
            widget.bind_all("<Button-5>", lambda e: widget.yview_scroll(1, "units"))

        def _unbind(event):
            widget.unbind_all("<MouseWheel>")
            widget.unbind_all("<Button-4>")
            widget.unbind_all("<Button-5>")

        widget.bind("<Enter>", _bind)
        widget.bind("<Leave>", _unbind)

    # ---------------- LOAD PRODUCT ----------------
    def load_product(self, product):

        for w in self.scrollable_frame.winfo_children():
            w.destroy()

        # 🔥 MAIN CONTAINER (CENTERED)
        container = tk.Frame(self.scrollable_frame, bg=BACKGROUND)
        container.pack(fill="both", expand=True)

        content = tk.Frame(container, bg=BACKGROUND)
        content.pack(pady=20)

        # BACK BUTTON
        HoverButton(
            content,
            text="← Back",
            command=lambda: self.app.show_frame("HomeScreen"),
            bg=BUTTON, fg="white",
            font=FONT_TEXT,
            relief="flat", padx=12, pady=6
        ).pack(anchor="w", pady=(0, 15))

        # 🔲 CARD
        card = tk.Frame(content, bg=CARD, padx=30, pady=25)
        card.pack()

        # TITLE
        tk.Label(
            card, text=product[1],
            font=FONT_TITLE, bg=CARD, fg=TEXT,
            wraplength=700, justify="left"
        ).pack(anchor="w", pady=(0, 10))

        # PRICE
        tk.Label(
            card, text=f"₹ {product[2]:,.2f}",
            font=("Segoe UI", 20, "bold"),
            fg=ACCENT, bg=CARD
        ).pack(anchor="w", pady=(0, 10))

        # CATEGORY
        tk.Label(
            card, text=f"Category: {product[5]}",
            font=FONT_TEXT, fg=SUBTEXT, bg=CARD
        ).pack(anchor="w", pady=(0, 15))

        # IMAGE
        if len(product) > 4 and product[4] and os.path.exists(product[4]):
            try:
                img = Image.open(product[4])
                img = ImageOps.contain(img, (400, 400))
                self.img_tk = ImageTk.PhotoImage(img)

                img_label = tk.Label(card, image=self.img_tk, bg=CARD)
                img_label.pack(pady=10)   # ✅ FIXED
            except tk.TclError:
                tk.Label(card, text="Image cannot be loaded",
                         bg=CARD, fg=SUBTEXT).pack()

        # DIVIDER
        tk.Frame(card, bg="#334155", height=1).pack(fill="x", pady=15)

        # DESCRIPTION TITLE
        tk.Label(
            card, text="Description",
            font=FONT_SUBTITLE, bg=CARD, fg=TEXT
        ).pack(anchor="w")

        # DESCRIPTION BOX
        desc_box = tk.Frame(card, bg="#0f172a", padx=15, pady=15)
        desc_box.pack(fill="x", pady=10)

        tk.Label(
            desc_box,
            text=product[3] or "No description available.",
            wraplength=650,
            justify="left",
            font=FONT_TEXT,
            bg="#0f172a",
            fg=TEXT
        ).pack(anchor="w")

        # ACTION BUTTONS
        btn_frame = tk.Frame(card, bg=CARD)
        btn_frame.pack(pady=20)

        HoverButton(
            btn_frame,
            text="Add to Cart",
            command=lambda: self.app.frames["HomeScreen"].add_cart(product),
            bg=BUTTON, fg="white",
            font=FONT_TEXT,
            padx=20, pady=8
        ).pack(side="left", padx=10)

        HoverButton(
            btn_frame,
            text="Buy Now",
            command=lambda: self.app.frames["HomeScreen"].buy_now(product),
            bg=ACCENT, fg="black",
            font=FONT_TEXT,
            padx=20, pady=8
        ).pack(side="left", padx=10)

        # SHADOW EFFECT
        tk.Frame(self.scrollable_frame, height=15, bg=SHADOW).pack(fill="x")