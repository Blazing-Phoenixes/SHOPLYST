# Eadmin_panel.py - FULL MERGED VERSION (NO LOGIC REMOVED)

import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import sqlite3
import os
from PIL import Image, ImageTk

from sm_database import add_product, assign_role, promote_to_admin

DB_NAME = "app.db"

# COLORS
BACKGROUND = "#0f172a"
CARD = "#1e293b"
TEXT = "#e2e8f0"
SUBTEXT = "#94a3b8"
BUTTON = "#6366f1"
BUTTON_HOVER = "#4f46e5"
SUCCESS = "#22c55e"
DANGER = "#ef4444"
INPUT = "#334155"
BORDER = "#475569"

FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_HEADER = ("Segoe UI", 14, "bold")
FONT = ("Segoe UI", 11)


class AdminPanel(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BACKGROUND)
        self.app = app

        self.selected_product_id = None
        self.image_path = None

        self.product_search_var = tk.StringVar()
        self.user_search_var = tk.StringVar()

        self.current_page = 0
        self.items_per_page = 5
        self.rows_options = [5, 10, 20, 50]

        self.images_cache = {}

        self.build_ui()

    # ================= MAIN UI =================
    def build_ui(self):
        for w in self.winfo_children():
            w.destroy()

        header = tk.Frame(self, bg=CARD)
        header.pack(fill="x", padx=10, pady=10)

        tk.Label(header, text="🛒 Admin Dashboard",
                 bg=CARD, fg=TEXT, font=FONT_TITLE).pack(side="left")

        tk.Button(header, text="Logout",
                  bg=DANGER, fg="white",
                  command=self.logout).pack(side="right")

        self.analytics_cards()

        # NOTEBOOK MERGE
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.product_tab = tk.Frame(self.notebook, bg=BACKGROUND)
        self.user_tab = tk.Frame(self.notebook, bg=BACKGROUND)
        self.order_tab = tk.Frame(self.notebook, bg=BACKGROUND)

        self.notebook.add(self.product_tab, text="Products")
        self.notebook.add(self.user_tab, text="Users")
        self.notebook.add(self.order_tab, text="Orders")

        # BUILD ALL SECTIONS INSIDE TABS
        self.build_product_tab(self.product_tab)
        self.user_section(self.user_tab)
        self.order_section(self.order_tab)

    # ================= ANALYTICS =================
    def analytics_cards(self):
        frame = tk.Frame(self, bg=BACKGROUND)
        frame.pack(fill="x")

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            products = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            orders = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]

        for text, value in [("Users", users), ("Products", products), ("Orders", orders)]:
            card = tk.Frame(frame, bg=CARD)
            card.pack(side="left", expand=True, fill="both", padx=5, pady=5)

            tk.Label(card, text=text, bg=CARD, fg=TEXT).pack()
            tk.Label(card, text=str(value), bg=CARD, fg=TEXT, font=FONT_HEADER).pack()

    # ================= SCROLL =================
    def create_scrollable(self, parent):
        canvas = tk.Canvas(parent, bg=BACKGROUND, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        frame = tk.Frame(canvas, bg=BACKGROUND)

        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.bind_mousewheel(canvas)

        return frame

    # ================= PRODUCT TAB =================
    def build_product_tab(self, parent):
        main = tk.Frame(parent, bg=BACKGROUND)
        main.pack(fill="both", expand=True)

        self.build_left_panel(main)
        self.build_product_panel(main)

    def build_left_panel(self, parent):
        left = tk.Frame(parent, bg=CARD, width=250)
        left.pack(side="left", fill="y", padx=10, pady=10)

        tk.Label(left, text="Add / Edit Product", bg=CARD, fg=TEXT, font=FONT_HEADER).pack(pady=10)

        self.name = tk.Entry(left, bg=INPUT, fg=TEXT)
        self.name.pack(fill="x", pady=5, padx=10)

        self.price = tk.Entry(left, bg=INPUT, fg=TEXT)
        self.price.pack(fill="x", pady=5, padx=10)

        self.category = tk.Entry(left, bg=INPUT, fg=TEXT)
        self.category.pack(fill="x", pady=5, padx=10)

        self.stock = tk.Entry(left, bg=INPUT, fg=TEXT)
        self.stock.pack(fill="x", pady=5, padx=10)

        tk.Button(left, text="Upload Image", command=self.choose_image).pack(fill="x", padx=10, pady=5)

        self.image_preview = tk.Label(left, bg=CARD)
        self.image_preview.pack(pady=5)

        tk.Button(left, text="Add Product", bg=SUCCESS, command=self.add_product).pack(fill="x", padx=10, pady=5)
        tk.Button(left, text="Update Product", bg=BUTTON, command=self.update_product).pack(fill="x", padx=10, pady=5)
        tk.Button(left, text="Delete Product", bg=DANGER, command=self.delete_product).pack(fill="x", padx=10, pady=5)

    def build_product_panel(self, parent):
        right = tk.Frame(parent, bg=BACKGROUND)
        right.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        top = tk.Frame(right, bg=BACKGROUND)
        top.pack(fill="x")

        tk.Entry(top, textvariable=self.product_search_var).pack(side="left", fill="x", expand=True)
        tk.Button(top, text="Search", command=self.load_products).pack(side="left", padx=5)

        self.product_frame = self.create_scrollable(right)
        self.load_products()

    def load_products(self):
        for w in self.product_frame.winfo_children():
            w.destroy()

        query = self.product_search_var.get().lower()

        with sqlite3.connect(DB_NAME) as conn:
            products = conn.execute("SELECT id, name, price, category, stock, image FROM products").fetchall()

        row = col = 0

        for pid, name, price, category, stock, img_path in products:
            if query and query not in name.lower():
                continue

            card = tk.Frame(self.product_frame, bg=CARD)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.product_frame.grid_columnconfigure(col, weight=1)

            if img_path and os.path.exists(img_path):
                img = Image.open(img_path).resize((100, 100))
                img = ImageTk.PhotoImage(img)
                lbl = tk.Label(card, image=img, bg=CARD)
                lbl.image = img
                lbl.pack()
            else:
                tk.Label(card, text="No Image", bg=CARD, fg=TEXT).pack()

            tk.Label(card, text=name, bg=CARD, fg=TEXT).pack()
            tk.Label(card, text=f"₹{price}", bg=CARD, fg=TEXT).pack()

            card.bind("<Button-1>", lambda e, pid=pid: self.select_product(pid))

            col += 1
            if col == 3:
                col = 0
                row += 1

    def select_product(self, pid):
        self.selected_product_id = pid

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT name, price, category, stock, image FROM products WHERE id=?", (pid,))
            product = c.fetchone()

        if product:
            name, price, category, stock, image = product

            self.name.delete(0, "end")
            self.name.insert(0, name)

            self.price.delete(0, "end")
            self.price.insert(0, price)

            self.category.delete(0, "end")
            self.category.insert(0, category)

            self.stock.delete(0, "end")
            self.stock.insert(0, stock)

            self.image_path = image
        self.bind_mousewheel(self.product_frame)

    def show_toast(self, title, msg, color="#22c55e"):
        if "Error" in title:
            color = "#ef4444"
        else:
            color = "#22c55e"

        toast = tk.Label(self, text=msg, bg=color, fg="white", padx=15, pady=8)
        toast.place(relx=0.5, rely=1.0, anchor="s")

        def slide_up(y):
            if y > 0.9:
                toast.place(relx=0.5, rely=y, anchor="s")
                self.after(10, lambda: slide_up(y - 0.01))
            else:
                self.after(2000, slide_down)

        def slide_down():
            y = 0.9
            def down():
                nonlocal y
                if y < 1.0:
                    y += 0.01
                    toast.place(relx=0.5, rely=y, anchor="s")
                    self.after(10, down)
                else:
                    toast.destroy()
            down()

        slide_up(1.0)

    # ================= CRUD =================
    def add_product(self):
        try:
            add_product(
                self.name.get(),
                float(self.price.get()),
                "",
                self.image_path,
                self.category.get(),
                int(self.stock.get())
            )
            self.show_toast("Success", "Product Added")
            self.clear_form()
            self.load_products()
        except Exception as e:
            self.show_toast("Error", str(e))

    def update_product(self):
        if not self.selected_product_id:
            return self.show_toast("Error", "Select product")

        with sqlite3.connect(DB_NAME) as conn:
            conn.execute("""
                UPDATE products 
                SET name=?, price=?, category=?, stock=?, image=? 
                WHERE id=?
            """, (
                self.name.get(),
                float(self.price.get()),
                self.category.get(),
                int(self.stock.get()),
                self.image_path,
                self.selected_product_id
            ))

        self.show_toast("Updated", "Product Updated")
        self.load_products()

    def delete_product(self):
        if not self.selected_product_id:
            return self.toast("Error", "Select product")

        with sqlite3.connect(DB_NAME) as conn:
            conn.execute("DELETE FROM products WHERE id=?",
                         (self.selected_product_id,))

        self.show_toast("Deleted", "Product Removed")
        self.load_products()

    # ================= USERS =================
    def user_section(self, parent):
        tk.Label(parent, text="User Management", fg=TEXT, bg=BACKGROUND,
                font=FONT_HEADER).pack(pady=5)

        self.search_var = tk.StringVar()

        top = tk.Frame(parent, bg=BACKGROUND)
        top.pack(fill="x", pady=5)

        search_entry = tk.Entry(top, textvariable=self.search_var, bg=INPUT, fg=TEXT)
        search_entry.pack(side="left", fill="x", expand=True, padx=5, ipady=3)

        tk.Button(top, text="Search", command=self.load_users,
                bg=BUTTON, fg="white").pack(side="left", padx=5)

        container = tk.Frame(parent, bg=BACKGROUND)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg=BACKGROUND, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)

        self.user_frame = tk.Frame(canvas, bg=BACKGROUND)

        self.user_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.user_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.bind_mousewheel(canvas)

        self.load_users()

    # ================= LOAD USERS =================
    def load_users(self):
        for w in self.user_frame.winfo_children():
            w.destroy()

        query = self.search_var.get().lower()
        current_user = self.app.current_user  # ✅ current logged-in user

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT id, username, role FROM users")
            users = c.fetchall()

        for uid, uname, role in users:
            if query and query not in uname.lower():
                continue

            row = tk.Frame(self.user_frame, bg=CARD)
            row.pack(fill="x", pady=3, padx=5)

            # 👑 SHOW CURRENT ADMIN BADGE
            label_text = f"{uname} ({role})"
            if uname == current_user and role == "admin":
                label_text += " 👑 (Current Admin)"

            tk.Label(row, text=label_text,
                    fg=TEXT, bg=CARD).pack(side="left")

            # Admin Button
            tk.Button(row, text="Admin",
                    command=lambda u=uname: self.make_admin(u),
                    bg=BUTTON).pack(side="right")

            # User Button (🚫 prevent self demotion)
            tk.Button(row, text="User",
                    command=lambda u=uname: self.make_user(u),
                    bg=BORDER).pack(side="right")

            # Delete Button (🔒 prevent self delete)
            tk.Button(row, text="Delete",
                    command=lambda u=uname: self.delete_user(u),
                    bg=DANGER).pack(side="right")

    # ================= ROLE MANAGEMENT =================
    def make_admin(self, username):
        promote_to_admin(username)
        self.show_toast("Success", f"{username} is now Admin")
        self.load_users()

    def make_user(self, username):
        current_user = self.app.current_user

        # 🚫 BLOCK SELF DEMOTION ONLY
        if username == current_user:
            messagebox.showerror("Access Denied", "You cannot change your own admin role!")
            return

        # ✅ ALLOW changing ANY other user (even admin → user)
        result = assign_role(current_user, username, "user")

        self.show_toast("Info", result)
        self.load_users()

    # ================= DELETE USER =================
    def delete_user(self, username):
        current_user = self.app.current_user

        # 🔒 BLOCK SELF DELETE ONLY
        if username == current_user:
            messagebox.showerror("Access Denied", "You cannot delete your own account!")
            return

        if not messagebox.askyesno("Confirm", f"Delete user '{username}'?"):
            return

        with sqlite3.connect(DB_NAME) as conn:
            conn.execute("DELETE FROM users WHERE username=?", (username,))

        self.show_toast("Deleted", f"{username} removed")
        self.load_users()

    # ================= ORDERS UI =================
    def order_section(self, parent):

        # ===== THEME =====
        BG = "#0f172a"
        CARD = "#1e293b"
        ACCENT = "#3b82f6"
        SUCCESS = "#22c55e"
        MUTED = "#94a3b8"

        parent.configure(bg=BG)

        # ===== HEADER =====
        header = tk.Frame(parent, bg=BG)
        header.pack(fill="x", pady=10)

        tk.Label(header,
                 text="📦 Order Management",
                 fg="white",
                 bg=BG,
                 font=("Segoe UI", 24, "bold")
                 ).pack(anchor="center")

        tk.Label(header,
                 text="Track and manage customer orders",
                 fg=MUTED,
                 bg=BG,
                 font=("Segoe UI", 11)
                 ).pack(anchor="center")

        # ===== FILTER BAR =====
        filter_card = tk.Frame(parent, bg=CARD)
        filter_card.pack(fill="x", padx=20, pady=10)

        inner = tk.Frame(filter_card, bg=CARD)
        inner.pack(padx=10, pady=10, fill="x")

        self.order_filter = tk.StringVar(value="All")

        ttk.Style().configure("Modern.TCombobox",
                              fieldbackground="#ffffff",
                              background="#ffffff",
                              padding=5)

        ttk.Combobox(inner,
                     textvariable=self.order_filter,
                     values=["All", "Pending", "Delivered"],
                     width=15).pack(side="left", padx=5)

        tk.Button(inner,
                  text="Apply",
                  bg=SUCCESS,
                  fg="black",
                  relief="flat",
                  padx=12,
                  command=self.load_orders).pack(side="left", padx=5)

        tk.Label(inner,
                 text="Rows:",
                 fg=MUTED,
                 bg=CARD).pack(side="left", padx=15)

        self.rows_per_page_var = tk.IntVar(value=self.items_per_page)

        ttk.Combobox(inner,
                     textvariable=self.rows_per_page_var,
                     values=self.rows_options,
                     width=5).pack(side="left")

        tk.Button(inner,
                  text="Set",
                  bg=ACCENT,
                  fg="white",
                  relief="flat",
                  padx=12,
                  command=self.update_rows_per_page).pack(side="left", padx=5)

        # ===== SCROLL AREA =====
        container = tk.Frame(parent, bg=BG)
        container.pack(fill="both", expand=True, padx=20, pady=10)

        canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)

        self.order_frame = tk.Frame(canvas, bg=BG)

        self.order_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=self.order_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.bind_mousewheel(canvas)

        # ===== PAGINATION =====
        nav = tk.Frame(parent, bg=BG)
        nav.pack(pady=10)

        tk.Button(nav, text="⬅ Prev",
                  command=self.prev_page,
                  bg="#1e293b",
                  fg="white",
                  relief="flat",
                  padx=20).pack(side="left", padx=10)

        tk.Button(nav, text="Next ➡",
                  command=self.next_page,
                  bg="#1e293b",
                  fg="white",
                  relief="flat",
                  padx=20).pack(side="left", padx=10)

        self.load_orders()

    # ================= LOAD ORDERS =================
    def load_orders(self):
        for w in self.order_frame.winfo_children():
            w.destroy()

        CARD = "#1e293b"
        SUCCESS = "#22c55e"
        WARNING = "#f59e0b"

        with sqlite3.connect(DB_NAME) as conn:
            orders = conn.execute("SELECT id, total, status FROM orders").fetchall()

        if self.order_filter.get() != "All":
            orders = [o for o in orders if o[2] == self.order_filter.get()]

        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        orders = orders[start:end]

        for oid, total, status in orders:

            status_color = SUCCESS if status == "Delivered" else WARNING

            row = tk.Frame(self.order_frame,
                           bg=CARD,
                           highlightthickness=1,
                           highlightbackground="#334155")
            row.pack(fill="x", pady=8, padx=5, ipady=8)

            def on_enter(e, r=row): r.configure(bg="#273549")
            def on_leave(e, r=row): r.configure(bg=CARD)

            row.bind("<Enter>", on_enter)
            row.bind("<Leave>", on_leave)

            left = tk.Frame(row, bg=row["bg"])
            left.pack(side="left", padx=15)

            tk.Label(left,
                     text=f"Order #{oid}",
                     fg="white",
                     bg=row["bg"],
                     font=("Segoe UI", 12, "bold")).pack(anchor="w")

            tk.Label(left,
                     text=f"₹{total}",
                     fg="#38bdf8",
                     bg=row["bg"]).pack(anchor="w")

            right = tk.Frame(row, bg=row["bg"])
            right.pack(side="right", padx=10)

            tk.Label(right,
                     text=status,
                     bg=status_color,
                     fg="black",
                     padx=10).pack(side="right", padx=5)

            if status != "Delivered":
                tk.Button(right,
                          text="Mark Delivered",
                          command=lambda o=oid: self.mark_delivered(o),
                          bg=SUCCESS,
                          fg="black",
                          relief="flat").pack(side="right", padx=5)

    # ================= PAGINATION =================
    def next_page(self):
        self.current_page += 1
        self.load_orders()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
        self.load_orders()

    # ================= ROW SETTINGS =================
    def update_rows_per_page(self):
        self.items_per_page = self.rows_per_page_var.get()
        self.current_page = 0
        self.load_orders()

    # ================= UPDATE STATUS =================
    def mark_delivered(self, order_id):
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute("UPDATE orders SET status='Delivered' WHERE id=?", (order_id,))

        self.show_toast("Success", f"Order {order_id} marked as Delivered")
        self.load_orders()

    # ================= COMMON =================
    def choose_image(self):
        path = filedialog.askopenfilename()
        if path:
            self.image_path = path
            img = Image.open(path).resize((100, 100))
            img = ImageTk.PhotoImage(img)
            self.image_preview.configure(image=img)
            self.image_preview.image = img

    # ================= SMOOTH MOUSE WHEEL (ALL-IN-ONE) =================
    def bind_mousewheel(self, canvas):
        self._scroll_velocity = 0
        self._scroll_job = None

        # Activate only when cursor is inside canvas
        canvas.bind("<Enter>", lambda e: self._bind_scroll(canvas))
        canvas.bind("<Leave>", lambda e: self._unbind_scroll())

    def _bind_scroll(self, canvas):
        # Windows + Touchpad
        canvas.bind_all("<MouseWheel>", lambda e: self._on_mousewheel(e, canvas))

        # Linux
        canvas.bind_all("<Button-4>", lambda e: self._on_mousewheel_linux(e, canvas, -1))
        canvas.bind_all("<Button-5>", lambda e: self._on_mousewheel_linux(e, canvas, 1))

    def _unbind_scroll(self):
        # Remove all bindings when mouse leaves
        for event in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            try:
                self.unbind_all(event)
            except Exception as e:
                print(f"Error occurred while unbinding scroll event: {e}")

    # ================= SCROLL HANDLER =================
    def _on_mousewheel(self, event, canvas):
        if not isinstance(canvas, tk.Canvas):
            return

        # Normalize delta (touchpad friendly)
        delta = event.delta / 120

        # Add velocity (momentum effect)
        self._scroll_velocity += -delta * 2

        self._start_smooth_scroll(canvas)

    def _on_mousewheel_linux(self, event, canvas, direction):
        if not isinstance(canvas, tk.Canvas):
            return

        self._scroll_velocity += direction * 2
        self._start_smooth_scroll(canvas)

    # ================= INERTIA ENGINE =================
    def _start_smooth_scroll(self, canvas):
        if self._scroll_job:
            canvas.after_cancel(self._scroll_job)

        self._smooth_scroll(canvas)

    def _smooth_scroll(self, canvas):
        # Stop condition
        if abs(self._scroll_velocity) < 0.1:
            self._scroll_velocity = 0
            return

        # Scroll
        canvas.yview_scroll(int(self._scroll_velocity), "units")

        # Friction (controls inertia feel)
        self._scroll_velocity *= 0.85

        # Loop (~60 FPS)
        self._scroll_job = canvas.after(16, lambda: self._smooth_scroll(canvas))

    def refresh(self):
        self.build_ui()

    # def clear_form(self):
    #     self.name.delete(0, "end")
    #     self.price.delete(0, "end")
    #     self.category.delete(0, "end")
    #     self.stock.delete(0, "end")
    #     self.image_path = None
    #     self.image_preview.configure(image="")

    def logout(self):
        self.app.show_frame("LoginSignupApp")
