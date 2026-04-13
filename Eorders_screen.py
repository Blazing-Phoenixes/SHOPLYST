# Eorders_screen.py - Displays user's past orders in a scrollable list with details
import tkinter as tk
from tkinter import ttk
from sm_database import get_orders

# 🎨 COLORS
BACKGROUND = "#0f172a"
CARD = "#1e293b"
TEXT = "#e2e8f0"
SUBTEXT = "#94a3b8"
SUCCESS = "#22c55e"
WARNING = "orange"
BUTTON_BG = "#6366f1"
BUTTON_HOVER = "#4f46e5"
BUTTON_FG = "white"
ORDER_NUMBER_BG = "#2563eb"
ORDER_NUMBER_FG = "white"

FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_CARD_HEADER = ("Segoe UI", 13, "bold")
FONT_CARD_BODY = ("Segoe UI", 12)
FONT_CARD_SUB = ("Segoe UI", 10)
FONT_ORDER_NUMBER = ("Segoe UI", 14, "bold")

class OrdersScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BACKGROUND)
        self.app = app
        self.user_id = None
        self.build_ui()

    # ---------------- UI ----------------
    def build_ui(self):
        # Clear previous widgets
        for w in self.winfo_children():
            w.destroy()

        self.app.title("My Orders")

        # ✅ ALWAYS UPDATE USER_ID
        self.user_id = self.app.user_data[0] if self.app.user_data else None

        # TOP NAV
        top = tk.Frame(self, bg=CARD, height=70)
        top.pack(fill="x")

        back_btn = tk.Button(
            top, text="← Back",
            command=lambda: self.app.show_frame("HomeScreen"),
            bg=BUTTON_BG, fg=BUTTON_FG, relief="flat",
            padx=20, pady=8, font=("Segoe UI", 11, "bold"), cursor="hand2"
        )
        back_btn.pack(side="left", padx=20, pady=15)
        self.add_hover_effect(back_btn, BUTTON_BG, BUTTON_HOVER)

        tk.Label(
            top, text="My Orders",
            bg=CARD, fg=TEXT,
            font=FONT_TITLE
        ).pack(pady=15)

        # SCROLLABLE FRAME
        self.canvas = tk.Canvas(self, bg=BACKGROUND, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.frame = tk.Frame(self.canvas, bg=BACKGROUND)

        # Bind configure to resize scroll region
        self.frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Window inside canvas
        window = self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Resize canvas window width dynamically
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(window, width=e.width))
        self.bind_mousewheel(self.canvas)

        self.load_orders()

    # ---------------- LOAD ORDERS ----------------
    def load_orders(self):
        for w in self.frame.winfo_children():
            w.destroy()

        if not self.app.user_data:
            tk.Label(
                self.frame, text="Please login first",
                bg=BACKGROUND, fg="red",
                font=FONT_CARD_BODY
            ).pack(pady=20)
            return

        self.user_id = self.app.user_data[0]

        orders = get_orders(self.user_id)

        if not orders:
            tk.Label(
                self.frame,
                text="No orders yet",
                bg=BACKGROUND, fg=TEXT,
                font=FONT_TITLE
            ).pack(pady=30)
            return

        for order in orders:
            oid, total, status, date = order

            # Card Frame
            card = tk.Frame(
                self.frame, bg=CARD, bd=0, relief="raised",
                highlightthickness=1, highlightbackground="#334155", padx=20, pady=15
            )
            card.pack(fill="x", padx=25, pady=12, ipady=5)

            # Unique Order Number Label (toplevel look)
            order_num = tk.Label(
                card, text=f"Order #{oid}",
                bg=ORDER_NUMBER_BG, fg=ORDER_NUMBER_FG,
                font=FONT_ORDER_NUMBER, padx=10, pady=5, relief="raised", bd=2
            )
            order_num.pack(anchor="w", pady=(0, 8))

            # Card Content
            tk.Label(
                card, text=f"Total: ₹ {total}",
                bg=CARD, fg=SUCCESS,
                font=FONT_CARD_BODY
            ).pack(anchor="w", pady=2)

            tk.Label(
                card, text=f"Status: {status}",
                bg=CARD, fg=WARNING,
                font=FONT_CARD_BODY
            ).pack(anchor="w", pady=2)

            tk.Label(
                card, text=f"Date: {date}",
                bg=CARD, fg=SUBTEXT,
                font=FONT_CARD_SUB
            ).pack(anchor="w", pady=2)

    # ---------------- UTILITIES ----------------
    def refresh(self):
        self.build_ui()

    # Mousewheel support
    def bind_mousewheel(self, widget):
        # Windows
        widget.bind_all("<MouseWheel>", lambda e: widget.yview_scroll(int(-1*(e.delta/120)), "units"))
        # Linux
        widget.bind_all("<Button-4>", lambda e: widget.yview_scroll(-1, "units"))
        widget.bind_all("<Button-5>", lambda e: widget.yview_scroll(1, "units"))

    # Hover effect for buttons
    def add_hover_effect(self, widget, bg_color, hover_color):
        def on_enter(e):
            widget['background'] = hover_color

        def on_leave(e):
            widget['background'] = bg_color

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)