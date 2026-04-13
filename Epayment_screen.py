# Epayment_screen.py - Payment processing screen with multiple payment options and validation
import tkinter as tk
from tkinter import messagebox
import re

from sm_database import place_order

# ---------------- COLORS ----------------
BACKGROUND = "#0f172a"
CARD = "#1e293b"
TEXT = "#e2e8f0"
BUTTON = "#6366f1"
INPUT = "#1e293b"
HOVER = "#4f46e5"
STATUS = "#facc15"

# ---------------- PAYMENT SCREEN ----------------
class PaymentScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BACKGROUND)
        self.app = app

        self.user_id = None
        self.method = tk.StringVar(value="COD")

        self.build_ui()

    # ---------------- UI ----------------
    def build_ui(self):
        for w in self.winfo_children():
            w.destroy()

        self.app.title("Payment")

        # ensure user is updated
        if getattr(self.app, "user_data", None):
            self.user_id = self.app.user_data[0] if self.app.user_data else None

        # ---------------- BACK BUTTON ----------------
        back_btn = tk.Button(self, text="Back",
                             command=lambda: self.app.show_frame("CartScreen"),
                             bg="gray", fg="white", font=("Segoe UI", 10, "bold"),
                             relief="flat", activebackground="#6b7280")
        back_btn.pack(anchor="nw", padx=15, pady=15)

        # ---------------- TITLE ----------------
        tk.Label(self, text="Select Payment Method",
                 bg=BACKGROUND, fg=TEXT,
                 font=("Segoe UI", 20, "bold")).pack(pady=10)

        # ---------------- PAYMENT OPTIONS ----------------
        options_frame = tk.Frame(self, bg=BACKGROUND)
        options_frame.pack(pady=10, padx=20, anchor="w", fill="x")

        options = ["COD", "UPI", "Card"]
        for opt in options:
            tk.Radiobutton(options_frame, text=opt,
                           variable=self.method, value=opt,
                           bg=BACKGROUND, fg=TEXT,
                           font=("Segoe UI", 12),
                           selectcolor=CARD,
                           command=self.render_fields).pack(anchor="w", pady=5)

        # ---------------- DYNAMIC AREA ----------------
        self.dynamic_frame = tk.Frame(self, bg=BACKGROUND)
        self.dynamic_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # ---------------- SCROLLABLE AREA ----------------
        self.canvas = tk.Canvas(self.dynamic_frame, bg=BACKGROUND, highlightthickness=0)
        self.scroll_frame = tk.Frame(self.canvas, bg=BACKGROUND)
        self.scrollbar = tk.Scrollbar(self.dynamic_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")

        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.render_fields()

        # ---------------- STATUS LABEL ----------------
        self.status_label = tk.Label(self, text="",
                                     bg=BACKGROUND, fg=STATUS,
                                     font=("Segoe UI", 10, "italic"))
        self.status_label.pack(pady=5)

        # ---------------- PAY BUTTON ----------------
        self.pay_btn = tk.Button(self, text="Pay Now",
                                 command=self.pay,
                                 bg=BUTTON, fg="white",
                                 font=("Segoe UI", 14, "bold"),
                                 relief="flat", activebackground=HOVER,
                                 padx=15, pady=10)
        self.pay_btn.pack(pady=20)

        # Hover effect
        self.pay_btn.bind("<Enter>", lambda e: self.pay_btn.config(bg=HOVER))
        self.pay_btn.bind("<Leave>", lambda e: self.pay_btn.config(bg=BUTTON))

    # ---------------- DYNAMIC INPUTS ----------------
    def render_fields(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        method = self.method.get()

        if method == "UPI":
            tk.Label(self.scroll_frame, text="Enter UPI ID (example@bank)",
                     bg=BACKGROUND, fg=TEXT, font=("Segoe UI", 12)).pack(anchor="w", pady=5)
            self.upi_entry = tk.Entry(self.scroll_frame, bg=INPUT, fg=TEXT, font=("Segoe UI", 12))
            self.upi_entry.pack(fill="x", pady=5)

        elif method == "Card":
            tk.Label(self.scroll_frame, text="Card Number (16 digits)",
                     bg=BACKGROUND, fg=TEXT, font=("Segoe UI", 12)).pack(anchor="w", pady=5)
            self.card_number = tk.Entry(self.scroll_frame, bg=INPUT, fg=TEXT, font=("Segoe UI", 12))
            self.card_number.pack(fill="x", pady=5)

            tk.Label(self.scroll_frame, text="CVV (3 digits)",
                     bg=BACKGROUND, fg=TEXT, font=("Segoe UI", 12)).pack(anchor="w", pady=5)
            self.cvv = tk.Entry(self.scroll_frame, bg=INPUT, fg=TEXT, show="*", font=("Segoe UI", 12))
            self.cvv.pack(fill="x", pady=5)

    # ---------------- VALIDATION ----------------
    def validate_payment(self):
        method = self.method.get()

        if method == "UPI":
            upi = self.upi_entry.get().strip()
            if not upi:
                return "UPI ID required"
            if not re.match(r"^[\w\.-]+@[\w]+$", upi):
                return "Invalid UPI ID format"

        elif method == "Card":
            card = self.card_number.get().strip()
            cvv = self.cvv.get().strip()
            if not card or not cvv:
                return "Card details required"
            if not (card.isdigit() and len(card) == 16):
                return "Card number must be 16 digits"
            if not (cvv.isdigit() and len(cvv) == 3):
                return "CVV must be 3 digits"

        return None  # valid

    # ---------------- PAYMENT ----------------
    def pay(self):
        if getattr(self.app, "user_data", None):
            self.user_id = self.app.user_data[0] if self.app.user_data else None

        if not self.user_id:
            return messagebox.showerror("Error", "Login required")

        validation_msg = self.validate_payment()
        if validation_msg:
            return messagebox.showwarning("Validation Error", validation_msg)

        self.pay_btn.config(state="disabled")
        self.status_label.config(text="Processing payment...")

        # DIRECT BUY
        if getattr(self.app, "direct_buy", False):
            product = self.app.selected_product
            from Edatabase import add_to_cart
            add_to_cart(self.user_id, product[0])
            msg = place_order(self.user_id)
            self.app.direct_buy = False
        else:
            msg = place_order(self.user_id)

        self.status_label.config(text="")
        messagebox.showinfo("Payment", f"{msg}\nMethod: {self.method.get()}")

        self.app.frames["OrdersScreen"].refresh()
        self.app.show_frame("OrdersScreen")
        self.pay_btn.config(state="normal")

    # ---------------- REFRESH ----------------
    def refresh(self):
        self.build_ui()
        
    # Mousewheel support
    def bind_mousewheel(self, widget):
        # Windows
        widget.bind_all("<MouseWheel>", lambda e: widget.yview_scroll(int(-1*(e.delta/120)), "units"))
        # Linux
        widget.bind_all("<Button-4>", lambda e: widget.yview_scroll(-1, "units"))
        widget.bind_all("<Button-5>", lambda e: widget.yview_scroll(1, "units"))