# 🛍️ Shoplyst

**Shoplyst** is an all-in-one desktop application that seamlessly combines **social media** and **e-commerce** into a single platform. Built using **Python (Tkinter)** and **SQLite**, it delivers a smooth and user-friendly experience for communication, shopping, and administration.

---

## 🚀 Features

### 🌐 Social Media

* User registration & login system
* Friend requests and connections
* Real-time chat messaging
* Media sharing (public & private)
* Profile management (image, email, password)

### 🛒 E-Commerce

* Product browsing and search
* Add to cart & wishlist
* Order placement and tracking
* Payment simulation
* Product details view

### 🛠️ Admin Panel

* Add / update / delete products
* Manage users and roles
* View analytics (users, orders, revenue)

---

## 🖥️ Tech Stack

* **Frontend:** Tkinter (Python GUI)
* **Backend:** Python
* **Database:** SQLite
* **Packaging:** PyInstaller

---

## 📁 Project Structure

```
Shoplyst/
│
├── main.py                  # Main application entry point
├── Login.py                 # Login & Signup system
├── home_screen.py           # Social media home
├── profile_screen.py        # User profile
├── chat_gui.py              # Chat interface
├── sm_database.py           # Database operations
│
├── Ehome_screen.py          # E-commerce home
├── Ecart_screen.py          # Cart system
├── Eorders_screen.py        # Orders
├── Ewishlist_screen.py      # Wishlist
├── Epayment_screen.py       # Payment screen
├── Eadmin_panel.py          # Admin dashboard
├── Eproduct_details.py      # Product details
│
├── app.db                   # SQLite database
├── shoplyst.ico             # App icon
└── main.spec                # PyInstaller config
```

---

## ⚙️ Installation & Setup

### 🔹 1. Clone Repository

```bash
git clone https://github.com/your-username/shoplyst.git
cd shoplyst
```

### 🔹 2. Install Dependencies

```bash
pip install -r requirements.txt
```

*(If no requirements file, install manually)*

```bash
pip install pillow passlib
```

---

### 🔹 3. Run Application

```bash
python main.py
```

---

## 📦 Convert to EXE (Windows)

```bash
pyinstaller --onefile --windowed --icon=shoplyst.ico --add-data "shoplyst.ico;." --add-data "app.db;." main.py
```

👉 Output will be inside:

```
dist/main.exe
```

---

## 🗄️ Database Handling

* Uses **SQLite (`app.db`)**
* Automatically creates tables on first run
* For EXE:

  * Database is copied to:

  ```
  C:\Users\<User>\AppData\Local\Shoplyst\app.db
  ```
* Ensures persistent data storage

---

## 🔐 Security Features

* Password hashing using `passlib`
* Input validation (email, phone, password)
* Role-based access (user/admin)

---

## 🎯 Usage Flow

1. Launch application
2. Register or Login
3. Choose:

   * Social Media
   * E-Commerce
4. Explore features based on role

---

## 🧪 Admin Access

To test admin features:

* Promote a user to admin via database or code
* Admin users can access:

  * Product management
  * Analytics dashboard

---

## 📸 Screenshots (Optional)

*Add your screenshots here*

---

## 🔧 Future Enhancements

* Cloud database integration
* Online multiplayer chat (real-time sockets)
* Payment gateway integration
* Mobile version
* Auto-update system

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a new branch
3. Commit changes
4. Submit a Pull Request

---

## 📄 License

This project is licensed under the **MIT License**.

---

## 👨‍💻 Author

**Bharathkumar**

---

## ⭐ Support

If you like this project:

* ⭐ Star the repo
* 🍴 Fork it
* 📢 Share it

---
