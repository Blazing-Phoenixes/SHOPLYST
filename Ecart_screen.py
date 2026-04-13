# Ecart_screen.py - Shopping cart screen with item management and order placement
import tkinter as tk
from tkinter import messagebox
from sm_database import get_cart, place_order, add_to_cart

# ---------------- COLORS ----------------
BACKGROUND = "#0f172a"
CARD = "#1e293b"
TEXT = "#e2e8f0"
BUTTON = "#6366f1"
BUTTON_HOVER = "#4f46e5"
DANGER = "#ef4444"
DANGER_HOVER = "#dc2626"
PRICE = "#22c55e"

class CartScreen(tk.Frame):
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

        self.app.title("Your Cart")

        # 🔝 TOP BAR
        top = tk.Frame(self, bg=CARD, height=60)
        top.pack(fill="x", side="top")

        tk.Button(top, text="Back",
                  command=lambda: self.app.show_frame("HomeScreen"),
                  bg="gray", fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", padx=10, pady=5).pack(side="left", padx=10, pady=10)

        tk.Label(top, text="Shopping Cart",
                 bg=CARD, fg=TEXT,
                 font=("Segoe UI", 18, "bold")).pack(pady=10)

        # 🔽 SCROLL AREA
        self.canvas = tk.Canvas(self, bg=BACKGROUND, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, command=self.canvas.yview)
        self.frame = tk.Frame(self.canvas, bg=BACKGROUND)

        self.frame.bind("<Configure>", lambda e:
                        self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        window = self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfig(window, width=e.width))

        self.load_cart()

    # ---------------- LOAD CART ----------------
    def load_cart(self):
        for w in self.frame.winfo_children():
            w.destroy()

        if self.app.user_data:
            self.user_id = self.app.user_data[0] if self.app.user_data else None
        else:
            tk.Label(self.frame, text="Please login first",
                     bg=BACKGROUND, fg="red", font=("Segoe UI", 14)).pack(pady=20)
            return

        items = get_cart(self.user_id)

        if not items:
            tk.Label(self.frame, text="Cart is empty 🛒",
                     bg=BACKGROUND, fg=TEXT,
                     font=("Segoe UI", 16, "bold")).pack(pady=30)
            return

        total = 0

        for item in items:
            product_id, name, price, qty = item
            total += price * qty

            # ---------------- ITEM CARD ----------------
            card = tk.Frame(self.frame, bg=CARD, bd=1, relief="raised")
            card.pack(fill="x", padx=20, pady=10, ipady=5)

            tk.Label(card, text=name,
                     bg=CARD, fg=TEXT,
                     font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=15, pady=2)

            tk.Label(card, text=f"₹ {price} x {qty} = ₹ {price * qty}",
                     bg=CARD, fg=PRICE,
                     font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=2)

            # ---------------- BUTTON ROW ----------------
            btn_frame = tk.Frame(card, bg=CARD)
            btn_frame.pack(anchor="e", padx=10, pady=5)

            self.create_button(btn_frame, "+", lambda pid=product_id: self.increase_qty(pid), BUTTON, BUTTON_HOVER)
            self.create_button(btn_frame, "-", lambda pid=product_id: self.decrease_qty(pid), "gray", "darkgray")
            self.create_button(btn_frame, "Remove", lambda pid=product_id: self.remove_item(pid), DANGER, DANGER_HOVER)

        # ---------------- TOTAL & PLACE ORDER ----------------
        total_frame = tk.Frame(self.frame, bg=BACKGROUND)
        total_frame.pack(fill="x", padx=20, pady=20)

        tk.Label(total_frame, text=f"Total: ₹ {total}",
                 font=("Segoe UI", 18, "bold"),
                 bg=BACKGROUND, fg=PRICE).pack(side="left")

        self.create_button(total_frame, "Place Order", self.place_order, BUTTON, BUTTON_HOVER, font_size=14, pad_x=20, pad_y=8, side="right")

    # ---------------- BUTTON CREATOR ----------------
    def create_button(self, parent, text, command, bg, hover_bg, font_size=11, pad_x=5, pad_y=2, side="left"):
        btn = tk.Button(parent, text=text, command=command, bg=bg, fg="white",
                        font=("Segoe UI", font_size, "bold"), relief="flat",
                        padx=pad_x, pady=pad_y, cursor="hand2")
        btn.pack(side=side, padx=5, pady=2)
        btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        return btn

    # ---------------- ACTIONS ----------------
    def increase_qty(self, product_id):
        add_to_cart(self.user_id, product_id)
        self.load_cart()

    def decrease_qty(self, product_id):
        import sqlite3
        with sqlite3.connect("app.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE cart SET quantity = quantity - 1
            WHERE user_id=? AND product_id=? AND quantity > 1
            """, (self.user_id, product_id))
        self.load_cart()

    def remove_item(self, product_id):
        import sqlite3
        with sqlite3.connect("app.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
            DELETE FROM cart
            WHERE user_id=? AND product_id=?
            """, (self.user_id, product_id))
        self.load_cart()

    def place_order(self):
        msg = place_order(self.user_id)
        messagebox.showinfo("Order", msg)
        self.load_cart()

    # Mousewheel support
    def bind_mousewheel(self, widget):
        # Windows
        widget.bind_all("<MouseWheel>", lambda e: widget.yview_scroll(int(-1*(e.delta/120)), "units"))
        # Linux
        widget.bind_all("<Button-4>", lambda e: widget.yview_scroll(-1, "units"))
        widget.bind_all("<Button-5>", lambda e: widget.yview_scroll(1, "units"))
        
    # 🔄 Refresh when switching screens
    def refresh(self):
        self.build_ui()