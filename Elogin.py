# Elogin.py - Handles user login and signup with a modern UI ecommerce app
import tkinter as tk
from tkinter import messagebox, filedialog
from Ewishlist_screen import WishlistScreen
from Eorders_screen import OrdersScreen
from Ecart_screen import CartScreen
from Ehome_screen import HomeScreen
from Eadmin_panel import AdminPanel

from sm_database import (
    connect_db, add_user, login_user, update_profile_image,
    validate_email, update_password, validate_password, validate_phone, validate_username,
)

# Initialize DB
connect_db()

# ---------------- COLORS ----------------
BACKGROUND = "#0f172a"
CARD = "#1e293b"
INPUT = "#1f2a3a"
BUTTON = "#6366f1"
HOVER = "#4f46e5"
TEXT = "#e2e8f0"
SUBTEXT = "#94a3b8"
SUCCESS = "#22c55e"
ERROR = "#ef4444"
SHADOW = "#1a202c"

# ---------------- FONTS ----------------
TITLE_FONT = ("Segoe UI", 28, "bold")
ENTRY_FONT = ("Segoe UI", 13)
BTN_FONT = ("Segoe UI", 13, "bold")
SUB_FONT = ("Segoe UI", 10, "italic")

# ---------------- MAIN APP ----------------
class LoginSignupApp(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BACKGROUND)
        self.app = app
        self.profile_image_path = None

        # Center container
        self.center_frame = tk.Frame(self, bg=BACKGROUND)
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Card with shadow effect
        self.shadow_frame = tk.Frame(self.center_frame, bg=SHADOW, bd=0)
        self.shadow_frame.pack(padx=5, pady=5)
        self.inner_frame = tk.Frame(
            self.shadow_frame,
            bg=CARD,
            width=540,
            height=560
        )
        self.inner_frame.pack()
        self.inner_frame.pack_propagate(False)

        # Scroll setup
        self.canvas = tk.Canvas(self.inner_frame, bg=CARD, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.inner_frame, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=CARD)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.window, width=e.width))

        self.create_login_ui()

    # ---------------- UI HELPERS ----------------
    def clear(self):
        for w in self.scrollable_frame.winfo_children():
            w.destroy()
            
    def clear_inputs(self):
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        
    def entry(self, placeholder="", show=None):
        # Wrapper with rounded effect
        container = tk.Frame(self.scrollable_frame, bg=INPUT, bd=0)
        container.pack(padx=40, pady=8, fill="x", ipady=1)
        e = tk.Entry(
            container,
            font=ENTRY_FONT,
            bg=INPUT,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            show=show
        )
        e.pack(fill="x", ipady=10, padx=10)
        if placeholder:
            e.insert(0, placeholder)
            e.bind("<FocusIn>", lambda ev: self.clear_placeholder(ev, placeholder))
            e.bind("<FocusOut>", lambda ev: self.add_placeholder(ev, placeholder))
        return e

    def clear_placeholder(self, event, text):
        if event.widget.get() == text:
            event.widget.delete(0, "end")
            event.widget.config(fg=TEXT)

    def add_placeholder(self, event, text):
        if not event.widget.get():
            event.widget.insert(0, text)
            event.widget.config(fg=SUBTEXT)

    def button(self, text, cmd, color=BUTTON, hover=HOVER):
        b = tk.Button(
            self.scrollable_frame,
            text=text,
            command=cmd,
            bg=color,
            fg="white",
            font=BTN_FONT,
            relief="flat",
            cursor="hand2",
            bd=0,
            activebackground=hover
        )
        b.pack(padx=40, pady=10, fill="x", ipady=10)
        b.bind("<Enter>", lambda e: b.config(bg=hover))
        b.bind("<Leave>", lambda e: b.config(bg=color))
        return b

    def label(self, text, size=12, fg=TEXT, bold=False):
        font = ("Segoe UI", size, "bold" if bold else "normal")
        return tk.Label(self.scrollable_frame, text=text, bg=CARD, fg=fg, font=font)

    # ---------------- LOGIN UI ----------------
    def create_login_ui(self):
        self.clear()
        self.label("Login", 28, TEXT, True).pack(pady=20)
        self.label("Username or Phone Number", 11, SUBTEXT).pack()
        self.user_input = self.entry("Enter username or phone")
        self.label("Password", 11, SUBTEXT).pack()
        self.pass_input = self.entry("Enter password", show="●")
        self.button("Login", self.login)
        tk.Button(
            self.scrollable_frame, text="Create Account",
            command=self.create_signup_ui,
            bg=CARD, fg=BUTTON, borderwidth=0, font=SUB_FONT
        ).pack(pady=5)

    # ---------------- LOGIN LOGIC ----------------
    def login(self):
        user = self.user_input.get().strip()
        pwd = self.pass_input.get().strip()
        if not user or not pwd:
            return messagebox.showerror("Error", "Please enter all fields")

        user_data = login_user(user, pwd)
        if user_data:
            messagebox.showinfo("Success", f"Welcome {user_data[1]}")
            self.app.user_data = user_data
            user_id = user_data[0]
            username = user_data[1]
            role = user_data[3]

            # Load screens
            home = self.app.frames[HomeScreen]; home.user_id = user_id; home.username = username; home.load_products()
            cart = self.app.frames[CartScreen]; cart.user_id = user_id; hasattr(cart, "load_cart") and cart.load_cart()
            orders = self.app.frames[OrdersScreen]; orders.user_id = user_id
            wishlist = self.app.frames[WishlistScreen]; wishlist.user_id = user_id
            admin = self.app.frames[AdminPanel]; hasattr(admin, "refresh") and admin.refresh()

            self.app.show_frame(AdminPanel if role == "admin" else HomeScreen)
        else:
            messagebox.showerror("Error", "Invalid username or password")

    # ---------------- SIGNUP UI ----------------
    def create_signup_ui(self):
        self.clear()
        self.label("Create Account", 28, TEXT, True).pack(pady=20)
        self.label("Username", 11, SUBTEXT).pack()
        self.signup_user = self.entry("Enter username")
        self.label("Phone", 11, SUBTEXT).pack()
        self.signup_phone = self.entry("Enter phone number")
        self.label("Email", 11, SUBTEXT).pack()
        self.signup_email = self.entry("Enter email (optional)")
        self.label("Password", 11, SUBTEXT).pack()
        self.signup_pass = self.entry("Enter password", show="●")

        self.profile_image_path = None
        self.profile_preview = tk.Label(self.scrollable_frame, bg=CARD)
        self.profile_preview.pack(pady=5)
        tk.Button(self.scrollable_frame, text="Choose Profile Image", command=self.choose_image,
                  bg=INPUT, fg=TEXT).pack(pady=5)
        self.button("Signup", self.signup)
        tk.Button(self.scrollable_frame, text="Back to Login", command=self.create_login_ui,
                  bg=CARD, fg=BUTTON, borderwidth=0, font=SUB_FONT).pack(pady=5)

    def choose_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png *.jpeg")])
        if path:
            self.profile_image_path = path
            # Show preview
            img = tk.PhotoImage(file=path)
            img = img.subsample(max(1, img.width()//100))
            self.profile_preview.configure(image=img)
            self.profile_preview.image = img

    # ---------------- SIGNUP LOGIC ----------------
    def signup(self):
        user = self.signup_user.get().strip()
        phone = self.signup_phone.get().strip()
        email = self.signup_email.get().strip()
        pwd = self.signup_pass.get().strip()

        if not validate_username(user):
            return messagebox.showerror("Error", "Invalid username")
        if not validate_phone(phone):
            return messagebox.showerror("Error", "Invalid phone")
        if email and not validate_email(email):
            return messagebox.showerror("Error", "Invalid email")
        if not validate_password(pwd):
            return messagebox.showerror("Error", "Weak password")

        msg = add_user(user, phone, pwd, email)
        if msg == "Account created successfully!":
            if self.profile_image_path:
                update_profile_image(user, self.profile_image_path)
            messagebox.showinfo("Success", msg)
            self.create_login_ui()
        else:
            messagebox.showerror("Error", msg)

    # ---------------- RESET PASSWORD ----------------
    def reset_password(self, identifier, new_pwd):
        result = update_password(identifier, new_pwd)
        messagebox.showinfo("Info", result)

    # ---------------- MOUSEWHEEL SUPPORT ----------------
    def bind_mousewheel(self, widget):
        widget.bind_all("<MouseWheel>", lambda e: widget.yview_scroll(int(-1*(e.delta/120)), "units"))
        widget.bind_all("<Button-4>", lambda e: widget.yview_scroll(-1, "units"))
        widget.bind_all("<Button-5>", lambda e: widget.yview_scroll(1, "units"))