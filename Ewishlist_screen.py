# Ewishlist_screen.py - Wishlist screen showing user's saved products with options to add to cart or remove from wishlist
import tkinter as tk
from tkinter import messagebox
from sm_database import get_wishlist, add_to_cart

# ---------------- COLORS ----------------
BACKGROUND = "#0f172a"
CARD = "#1e293b"
TEXT = "#e2e8f0"
BUTTON = "#6366f1"
DANGER = "#ef4444"
HOVER = "#4f46e5"
SHADOW = "#111827"

class WishlistScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BACKGROUND)
        self.app = app
        self.user_id = None

        self.build_ui()

    # ---------------- UI BUILD ----------------
    def build_ui(self):
        for w in self.winfo_children():
            w.destroy()

        self.app.title("Wishlist")

        # Update user_id
        self.user_id = self.app.user_data[0] if self.app.user_data else None

        # BACK BUTTON
        back_btn = tk.Button(
            self, text="← Back",
            command=lambda: self.app.show_frame("HomeScreen"),
            bg="gray", fg="white", relief="flat", padx=10, pady=5
        )
        back_btn.pack(anchor="nw", padx=10, pady=10)

        # TITLE
        tk.Label(
            self, text="My Wishlist ❤️",
            bg=BACKGROUND, fg=TEXT,
            font=("Segoe UI", 20, "bold")
        ).pack(pady=(0, 10))

        # SCROLLABLE CANVAS
        self.canvas = tk.Canvas(self, bg=BACKGROUND, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scroll_frame = tk.Frame(self.canvas, bg=BACKGROUND)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        # LOAD WISHLIST
        self.load_wishlist()

        # ENABLE MOUSE WHEEL SCROLLING
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    # ---------------- SCROLL FUNCTION ----------------
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ---------------- LOAD WISHLIST ----------------
    def load_wishlist(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        if not self.app.user_data:
            tk.Label(self.scroll_frame, text="Login required",
                     bg=BACKGROUND, fg="red", font=("Segoe UI", 14, "bold")).pack(pady=20)
            return

        self.user_id = self.app.user_data[0] if self.app.user_data else None
        items = get_wishlist(self.user_id)

        if not items:
            tk.Label(
                self.scroll_frame,
                text="Your Wishlist is empty 💔",
                bg=BACKGROUND, fg=TEXT,
                font=("Segoe UI", 16)
            ).pack(pady=30)
            return

        for item in items:
            pid, name, price = item

            # CARD FRAME WITH SHADOW
            shadow = tk.Frame(self.scroll_frame, bg=SHADOW)
            shadow.pack(fill="x", padx=20, pady=(10, 0))
            card = tk.Frame(shadow, bg=CARD, highlightthickness=0)
            card.pack(fill="x", padx=2, pady=2)

            # PRODUCT NAME
            tk.Label(
                card, text=name, bg=CARD, fg=TEXT,
                font=("Segoe UI", 14, "bold")
            ).pack(anchor="w", padx=10, pady=(10, 0))

            # PRICE
            tk.Label(
                card, text=f"₹ {price}", bg=CARD, fg="#22c55e",
                font=("Segoe UI", 12, "bold")
            ).pack(anchor="w", padx=10, pady=(0, 10))

            # BUTTONS FRAME
            btn_frame = tk.Frame(card, bg=CARD)
            btn_frame.pack(anchor="e", padx=10, pady=(0, 10))

            # ADD TO CART BUTTON
            add_btn = tk.Button(
                btn_frame, text="Add to Cart",
                bg=BUTTON, fg="white", relief="flat", padx=10, pady=5,
                command=lambda p=pid: self.add_to_cart(p)
            )
            add_btn.pack(side="left", padx=5)
            add_btn.bind("<Enter>", lambda e, b=add_btn: b.config(bg=HOVER))
            add_btn.bind("<Leave>", lambda e, b=add_btn: b.config(bg=BUTTON))

            # REMOVE BUTTON
            remove_btn = tk.Button(
                btn_frame, text="Remove",
                bg=DANGER, fg="white", relief="flat", padx=10, pady=5,
                command=lambda p=pid: self.remove_item(p)
            )
            remove_btn.pack(side="left", padx=5)
            remove_btn.bind("<Enter>", lambda e, b=remove_btn: b.config(bg="#dc2626"))
            remove_btn.bind("<Leave>", lambda e, b=remove_btn: b.config(bg=DANGER))

    # ---------------- ACTIONS ----------------
    def add_to_cart(self, product_id):
        add_to_cart(self.user_id, product_id)
        messagebox.showinfo("Success", "Added to cart!")
        self.load_wishlist()

    def remove_item(self, product_id):
        import sqlite3
        with sqlite3.connect("app.db") as conn:
            conn.execute("DELETE FROM wishlist WHERE user_id=? AND product_id=?", (self.user_id, product_id))

        messagebox.showinfo("Removed", "Item removed")
        self.load_wishlist()

    # Mousewheel support
    def bind_mousewheel(self, widget):
        # Windows
        widget.bind_all("<MouseWheel>", lambda e: widget.yview_scroll(int(-1*(e.delta/120)), "units"))
        # Linux
        widget.bind_all("<Button-4>", lambda e: widget.yview_scroll(-1, "units"))
        widget.bind_all("<Button-5>", lambda e: widget.yview_scroll(1, "units"))
        
    def refresh(self):
        self.build_ui()