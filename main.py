import tkinter as tk

# ================= SOCIAL MEDIA =================
from Login import LoginSignupApp
from home_screen import HomeFrame
from profile_screen import ProfileFrame
from chat_gui import ChatFrame

# ================= ECOMMERCE =================
from Ehome_screen import HomeScreen
from Ecart_screen import CartScreen
from Eorders_screen import OrdersScreen
from Ewishlist_screen import WishlistScreen
from Epayment_screen import PaymentScreen
from Eadmin_panel import AdminPanel
from Eproduct_details import ProductDetailsScreen

from sm_database import get_user_details, get_user_role, resource_path


# ================= APP SELECTOR =================
class AppSelectorScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#0f172a")
        self.app = app
        self.build_ui()

    def build_ui(self):
        for w in self.winfo_children():
            w.destroy()

        container = tk.Frame(self, bg="#1e293b")
        container.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(container, text="SUPER APP",
                 font=("Segoe UI", 34, "bold"),
                 fg="white", bg="#1e293b").pack(pady=(30, 10))

        tk.Label(container, text="Choose Your App",
                 font=("Segoe UI", 14),
                 fg="#94a3b8", bg="#1e293b").pack(pady=(0, 25))

        def create_btn(text, color, hover, command):
            btn = tk.Button(container, text=text,
                            font=("Segoe UI", 15, "bold"),
                            bg=color,
                            fg="white",
                            activebackground=hover,
                            width=22, height=2,
                            bd=0, cursor="hand2",
                            command=command)

            btn.bind("<Enter>", lambda e: btn.config(bg=hover))
            btn.bind("<Leave>", lambda e: btn.config(bg=color))
            btn.pack(pady=12)

        create_btn("Social Media", "#6366f1", "#4f46e5", self.app.open_social)
        create_btn("E-Commerce", "#22c55e", "#16a34a", self.app.open_ecommerce)

        tk.Label(container, text="Select an app to continue",
                 font=("Segoe UI", 10),
                 fg="#64748b", bg="#1e293b").pack(pady=(20, 30))


# ================= MAIN APP =================
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # ✅ App Icon (IMPORTANT)
        try:
            self.iconbitmap(resource_path("shoplyst.ico"))
        except Exception as e:
            print("Icon not found or failed to load:", e)
        self.title("Shoplyst")
        self.state("zoomed")
        self.configure(bg="#0f172a")

        # ---------------- USER STATE ----------------
        self.current_user = None
        self.user_data = None

        # ---------------- NAVIGATION ----------------
        self.history = []
        self.current_frame = None

        # ---------------- MAIN CONTAINER ----------------
        self.container = tk.Frame(self, bg="#0f172a")
        self.container.pack(fill="both", expand=True)

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        # ---------------- REGISTER FRAMES ----------------
        self.register_frames()

        # Start app
        self.show_frame("LoginSignupApp")

    # ================= REGISTER =================
    def register_frames(self):
        frame_classes = [
            LoginSignupApp,
            AppSelectorScreen,

            # SOCIAL
            HomeFrame,
            ProfileFrame,
            ChatFrame,

            # ECOMMERCE
            HomeScreen,
            CartScreen,
            OrdersScreen,
            WishlistScreen,
            PaymentScreen,
            AdminPanel,
            ProductDetailsScreen
        ]

        for F in frame_classes:
            try:
                frame = F(self.container, self)
                self.frames[F.__name__] = frame
                frame.grid(row=0, column=0, sticky="nsew")
            except Exception as e:
                print(f"[ERROR] Loading {F.__name__}: {e}")

    # ================= NAVIGATION =================
    def show_frame(self, name, **kwargs):
        frame = self.frames.get(name)

        if not frame:
            print(f"[ERROR] Frame {name} not found!")
            return

        # Save history
        if self.current_frame:
            self.history.append(self.current_frame)

        self.current_frame = name

        # Refresh safely
        if hasattr(frame, "refresh"):
            try:
                frame.refresh()
            except Exception as e:
                print(f"[ERROR] Refresh {name}: {e}")

        # Load data if exists
        if hasattr(frame, "load_data"):
            try:
                frame.load_data(**kwargs)
            except Exception as e:
                print(f"[ERROR] Load data {name}: {e}")

        frame.tkraise()

    def go_back(self):
        if self.history:
            last = self.history.pop()
            self.show_frame(last)

    # ================= LOGIN SUCCESS =================
    def login_success(self, user):
        self.current_user = user

        # 🔥 IMPORTANT FIX: always refresh user_data
        try:
            self.user_data = get_user_details(user)
            # print("USER DATA:", self.user_data)  # DEBUG
        except Exception as e:
            print("Error fetching user:", e)
            self.user_data = None

        self.history.clear()
        self.show_frame("AppSelectorScreen")

    # ================= LOGOUT =================
    def logout(self):
        self.current_user = None
        self.user_data = None
        self.history.clear()
        self.show_frame("LoginSignupApp")

    # ================= SOCIAL =================
    def open_social(self):
        if not self.current_user:
            self.show_frame("LoginSignupApp")
            return
        
        print("Opening Social Media...")
        self.show_frame("HomeFrame", user=self.current_user)

    # ================= ECOMMERCE =================
    def open_ecommerce(self):
        if not self.current_user:
            self.show_frame("LoginSignupApp")
            return

        role = get_user_role(self.current_user)
        # print("ROLE:", role)  # DEBUG

        if role.lower() == "admin":
            print("Opening Admin Panel...")
            self.frames["AdminPanel"].refresh()
            self.show_frame("AdminPanel")
        else:
            print("Opening User Ecommerce...")
            self.show_frame("HomeScreen", user=self.user_data)

# ================= RUN =================
if __name__ == "__main__":
    app = MainApp()
    app.mainloop()