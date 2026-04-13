# Ehome_screen.py - Main shopping screen with product listing, search, and navigation
import tkinter as tk
# from Login import LoginSignupApp
from tkinter import messagebox
from PIL import Image, ImageTk
import os

from Eproduct_details import ProductDetailsScreen
# from Epayment_screen import PaymentScreen
from sm_database import get_products, add_to_cart, add_to_wishlist

# COLORS
BACKGROUND = "#0f172a"
CARD = "#1e293b"
TEXT = "#e2e8f0"
SUBTEXT = "#94a3b8"
BUTTON = "#6366f1"
HOVER = "#4f46e5"
SUCCESS = "#22c55e"


class HomeScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BACKGROUND)
        self.app = app

        self.user_id = None
        self.username = ""

        self.products = []
        self._resize_after_id = None

        self.create_ui()

        # ✅ IMPORTANT FIX
        self.bind("<Visibility>", lambda e: [self.refresh(), self.load_products()])

        self.refresh()
        self.load_products()

        self.bind("<Configure>", self.on_resize)

    # ---------------- RESIZE FIX ----------------
    def on_resize(self, event):
        if self._resize_after_id:
            self.after_cancel(self._resize_after_id)

        self._resize_after_id = self.after(150, self.load_products)

    # ---------------- UI ----------------
    def create_ui(self):

        # 🔝 TOP BAR
        top = tk.Frame(self, bg=CARD, height=60)
        top.pack(fill="x")
        top.pack_propagate(False)

        back_btn = tk.Button(
            top,
            text="⬅ Back",
            bg="#64748b",
            fg="white",
            relief="flat",
            padx=12,
            cursor="hand2",
            command=lambda: self.app.show_frame("AppSelectorScreen")
        )
        back_btn.pack(side="left", padx=10)

        back_btn.bind("<Enter>", lambda e: back_btn.config(bg="#475569"))
        back_btn.bind("<Leave>", lambda e: back_btn.config(bg="#64748b"))

        # USER LABEL
        self.user_label = tk.Label(
            top,
            text=f"Welcome, {self.username}",
            bg=CARD, fg=TEXT,
            font=("Segoe UI", 14, "bold")
        )
        self.user_label.pack(side="left", padx=20)

        # 🔍 SEARCH
        self.search_var = tk.StringVar()

        search_frame = tk.Frame(top, bg="#334155", bd=1)
        search_frame.pack(side="left", padx=20)

        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            bg="#334155", fg=TEXT,
            font=("Segoe UI", 12),
            relief="flat",
            insertbackground="white"
        )
        search_entry.pack(side="left", ipady=6, ipadx=120, padx=5)

        tk.Button(search_frame, text="Search",
                  command=self.search_products,
                  bg=BUTTON, fg="white",
                  relief="flat", padx=10).pack(side="right")

        # BUTTON STYLE
        def styled_btn(parent, text, cmd):
            btn = tk.Button(parent, text=text, command=cmd,
                            bg=BUTTON, fg="white",
                            relief="flat", padx=12, pady=4)
            btn.pack(side="right", padx=6)

            btn.bind("<Enter>", lambda e: btn.config(bg=HOVER))
            btn.bind("<Leave>", lambda e: btn.config(bg=BUTTON))
            return btn

        styled_btn(top, "Logout",
                   lambda: self.app.show_frame("LoginSignupApp"))
        styled_btn(top, "Cart", self.open_cart)
        styled_btn(top, "Orders", self.open_orders)
        styled_btn(top, "Wishlist", self.open_wishlist)

        # 📦 SCROLL AREA
        self.canvas = tk.Canvas(self, bg=BACKGROUND, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, command=self.canvas.yview)

        self.frame = tk.Frame(self.canvas, bg=BACKGROUND)

        self.frame.bind("<Configure>", lambda e:
                        self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    # ---------------- LOAD PRODUCTS ----------------
    def load_products(self, products=None):
        for widget in self.frame.winfo_children():
            widget.destroy()

        if products is None:
            self.products = get_products()
        else:
            self.products = products

        width = self.winfo_width() or 900
        cols = max(2, width // 260)

        row = col = 0

        for product in self.products:
            card = tk.Frame(self.frame, bg=CARD, width=240, height=360, bd=1)
            card.grid(row=row, column=col, padx=12, pady=12)
            card.pack_propagate(False)

            # IMAGE
            img_label = tk.Label(card, bg=CARD)
            img_label.pack(pady=8)

            if product[4] and os.path.exists(product[4]):
                try:
                    img = Image.open(product[4]).resize((130, 130))
                    img = ImageTk.PhotoImage(img)
                    img_label.config(image=img)
                    img_label.image = img
                except Exception:
                    img_label.config(text="No Image", fg=SUBTEXT)
            else:
                img_label.config(text="No Image", fg=SUBTEXT)

            # NAME
            tk.Label(card, text=product[1],
                     bg=CARD, fg=TEXT,
                     wraplength=200,
                     font=("Segoe UI", 11, "bold")).pack()

            # PRICE
            tk.Label(card, text=f"₹ {product[2]}",
                     bg=CARD, fg=SUCCESS,
                     font=("Segoe UI", 12, "bold")).pack()

            # STOCK
            stock = product[6] if len(product) > 6 else 0
            stock_text = f"Stock: {stock}" if stock else "Out of Stock"

            tk.Label(card,
                     text=stock_text,
                     bg=CARD,
                     fg="#facc15" if stock else "#ef4444"
                     ).pack()

            # BUTTON STYLE
            def btn_style(btn):
                btn.bind("<Enter>", lambda e: btn.config(bg=HOVER))
                btn.bind("<Leave>", lambda e: btn.config(bg=BUTTON))

            # READ MORE
            tk.Button(card, text="Read More",
                      command=lambda p=product: self.open_details(p),
                      bg="#475569", fg="white").pack(pady=2)

            # CART
            cart_btn = tk.Button(card, text="Add to Cart",
                                 command=lambda p=product: self.add_cart(p),
                                 bg=BUTTON, fg="white")
            cart_btn.pack(pady=3)
            btn_style(cart_btn)

            # WISHLIST
            tk.Button(card, text="Wishlist",
                      command=lambda p=product: self.add_wishlist(p),
                      bg="gray", fg="white").pack(pady=3)

            # BUY NOW
            buy_btn = tk.Button(card, text="Buy Now",
                                command=lambda p=product: self.buy_now(p),
                                bg=SUCCESS, fg="black")
            buy_btn.pack(pady=3)

            if not stock:
                buy_btn.config(state="disabled", bg="gray")

            col += 1
            if col >= cols:
                col = 0
                row += 1

    # ---------------- DETAILS ----------------
    def open_details(self, product):
        self.app.selected_product = product

        if "ProductDetailsScreen" not in self.app.frames:
            frame = ProductDetailsScreen(self.app.container, self.app)
            self.app.frames["ProductDetailsScreen"] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.app.frames["ProductDetailsScreen"].load_product(product)
        self.app.show_frame("ProductDetailsScreen")

    # ---------------- SEARCH ----------------
    def search_products(self):
        query = self.search_var.get().lower().strip()

        if not query:
            self.load_products()
            return

        filtered = [
            p for p in get_products()
            if query in p[1].lower() or (p[5] and query in p[5].lower())
        ]

        self.load_products(filtered)

    # ---------------- CART ----------------
    def add_cart(self, product):
        if not self.user_id:
            return messagebox.showerror("Error", "Login required")

        add_to_cart(self.user_id, product[0])
        messagebox.showinfo("Success", "Added to cart!")

    # ---------------- WISHLIST ----------------
    def add_wishlist(self, product):
        if not self.user_id:
            return messagebox.showerror("Error", "Login required")

        add_to_wishlist(self.user_id, product[0])
        messagebox.showinfo("Success", "Added to wishlist!")

    # ---------------- BUY NOW ----------------
    def buy_now(self, product):
        if not self.user_id:
            return messagebox.showerror("Error", "Login required")

        self.app.selected_product = product
        self.app.direct_buy = True
        self.app.show_frame("PaymentScreen")

    # ---------------- NAVIGATION ----------------
    def open_cart(self):
        if "CartScreen" in self.app.frames:
            self.app.frames["CartScreen"].load_cart()
            self.app.show_frame("CartScreen")

    def open_wishlist(self):
        if "WishlistScreen" in self.app.frames:
            self.app.frames["WishlistScreen"].refresh()
            self.app.show_frame("WishlistScreen")

    def open_orders(self):
        if "OrdersScreen" in self.app.frames:
            self.app.frames["OrdersScreen"].refresh()
            self.app.show_frame("OrdersScreen")

    # ---------------- USER FIX ----------------
    def refresh(self):
        if self.app.user_data:
            self.user_id = self.app.user_data[0] if self.app.user_data else None
            self.username = self.app.user_data[1] if len(self.app.user_data) > 1 else "User"
        else:
            self.user_id = None
            self.username = "Guest"

        self.user_label.config(text=f"Welcome, {self.username}")

    # Mousewheel support
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