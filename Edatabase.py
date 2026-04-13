# Ecommerce Database Module Edatabase.py
import sqlite3
import re
from passlib.hash import pbkdf2_sha256

DB_NAME = "app.db"

# -------------------- CONNECT DB --------------------
def connect_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        # USERS
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE,
            role TEXT DEFAULT 'user',  -- user / admin / super_admin
            profile_image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # PRODUCTS
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL CHECK(price >= 0),
            description TEXT,
            image TEXT,
            category TEXT,
            stock INTEGER DEFAULT 0 CHECK(stock >= 0)
        )
        """)

        # CART
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER DEFAULT 1 CHECK(quantity > 0),
            UNIQUE(user_id, product_id),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        )
        """)

        # ORDERS
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            total REAL,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)

        # ORDER ITEMS
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            price REAL,
            FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
        )
        """)

        # WISHLIST
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            UNIQUE(user_id, product_id),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        )
        """)

        conn.commit()


# ================= VALIDATION =================
def validate_username(username):
    return re.fullmatch(r"^[A-Za-z][A-Za-z0-9_]{3,19}$", username)

def validate_phone(phone):
    return re.fullmatch(r"[6-9]\d{9}$", phone)

def validate_email(email):
    return re.fullmatch(r"^[\w\.-]+@[\w\.-]+\.(com|net|org|edu|in)$", email)

def validate_password(password):
    return re.fullmatch(r"(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}", password)


# ================= AUTH =================
def add_user(username, phone, password, email=None):
    if not validate_username(username):
        return "Invalid username"

    if not validate_phone(phone):
        return "Invalid phone"

    if not validate_password(password):
        return "Weak password"

    if email and not validate_email(email):
        return "Invalid email"

    hashed = pbkdf2_sha256.hash(password)

    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            cursor.execute("""
            INSERT INTO users(username, phone, password, email)
            VALUES (?, ?, ?, ?)
            """, (username.lower(), phone, hashed, email))

        return "Account created successfully!"

    except sqlite3.IntegrityError as e:
        error_msg = str(e)

        if "username" in error_msg:
            return "Username already exists!"
        elif "phone" in error_msg:
            return "Phone number already registered!"
        elif "email" in error_msg:
            return "Email already registered!"
        else:
            return f"Database error: {error_msg}"

def login_user(user_input, password):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, username, password, role FROM users
        WHERE username=? OR phone=?
        """, (user_input.lower(), user_input))
        user = cursor.fetchone()

    if user and pbkdf2_sha256.verify(password, user[2]):
        return user
    return None


# ================= ROLE =================
def promote_to_admin(username):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("UPDATE users SET role='admin' WHERE username=?", (username,))
    return "Promoted to admin"


def assign_role(admin_id, target_username, new_role):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT role FROM users WHERE id=?", (admin_id,))
        role = cursor.fetchone()

        if not role or role[0] not in ("admin", "super_admin"):
            return "Access denied"

        cursor.execute("UPDATE users SET role=? WHERE username=?",
                       (new_role, target_username))
    return "Role updated"


# ================= PRODUCTS =================
def add_product(name, price, description, image, category, stock):
    image = image if image else "no_image.png"

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
        INSERT INTO products(name, price, description, image, category, stock)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (name, price, description, image, category, stock))


def get_products():
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("SELECT * FROM products").fetchall()


def search_products(query):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("""
        SELECT * FROM products
        WHERE name LIKE ? OR category LIKE ?
        """, (f"%{query}%", f"%{query}%")).fetchall()


# ================= CART =================
def add_to_cart(user_id, product_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT stock FROM products WHERE id=?", (product_id,))
        stock = cursor.fetchone()

        if not stock or stock[0] <= 0:
            return "Out of stock"
        cursor.execute("SELECT quantity FROM cart WHERE user_id=? AND product_id=?",
                       (user_id, product_id))
        item = cursor.fetchone()

        if item:
            cursor.execute("""
            UPDATE cart SET quantity = quantity + 1
            WHERE user_id=? AND product_id=?
            """, (user_id, product_id))
        else:
            cursor.execute("""
            INSERT OR IGNORE INTO cart(user_id, product_id, quantity)
                           VALUES (?, ?, 1)
            """, (user_id, product_id))


def remove_from_cart(user_id, product_id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM cart WHERE user_id=? AND product_id=?",
                     (user_id, product_id))


def update_cart_quantity(user_id, product_id, qty):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
        UPDATE cart SET quantity=?
        WHERE user_id=? AND product_id=?
        """, (qty, user_id, product_id))


def get_cart(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("""
        SELECT products.id, products.name, products.price, cart.quantity
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id=?
        """, (user_id,)).fetchall()


# ================= ORDERS =================
def place_order(user_id):
    cart_items = get_cart(user_id)
    if not cart_items:
        return "Cart empty"

    total = sum(i[2]*i[3] for i in cart_items)

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        cursor.execute("INSERT INTO orders(user_id,total) VALUES (?,?)",
                       (user_id, total))
        order_id = cursor.lastrowid

        for item in cart_items:
            cursor.execute("""
            INSERT INTO order_items(order_id, product_id, quantity, price)
            VALUES (?, ?, ?, ?)
            """, (order_id, item[0], item[3], item[2]))
            cursor.execute("""
            UPDATE products SET stock = stock - ?
            WHERE id=? AND stock >= ?
            """, (item[3], item[0], item[3]))

        cursor.execute("DELETE FROM cart WHERE user_id=?", (user_id,))

    return "Order placed"


def get_orders(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("""
        SELECT id,total,status,created_at FROM orders
        WHERE user_id=? ORDER BY created_at DESC
        """, (user_id,)).fetchall()


def get_order_items(order_id):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("""
        SELECT products.name, quantity, price
        FROM order_items
        JOIN products ON products.id=order_items.product_id
        WHERE order_id=?
        """, (order_id,)).fetchall()


# ================= WISHLIST =================
def add_to_wishlist(user_id, product_id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
        INSERT OR IGNORE INTO wishlist(user_id, product_id)
        VALUES (?, ?)
        """, (user_id, product_id))


def remove_from_wishlist(user_id, product_id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM wishlist WHERE user_id=? AND product_id=?",
                     (user_id, product_id))


def get_wishlist(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("""
        SELECT products.id, products.name, products.price
        FROM wishlist
        JOIN products ON wishlist.product_id = products.id
        WHERE wishlist.user_id=?
        """, (user_id,)).fetchall()


# ================= ANALYTICS =================
def get_admin_stats():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM orders")
        orders = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(total) FROM orders")
        revenue = cursor.fetchone()[0] or 0

    return users, orders, revenue


# ================= PROFILE =================
def update_profile_image(identifier, image_path):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE users SET profile_image=?
        WHERE LOWER(username)=LOWER(?) OR phone=?
        """, (image_path, identifier, identifier))


def update_password(identifier, new_password):
    hashed = pbkdf2_sha256.hash(new_password)
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
        UPDATE users SET password=?
        WHERE username=? OR phone=?
        """, (hashed, identifier.lower(), identifier))

# #  INIT
#  def init():
#      connect_db()

#  if __name__ == "__main__":
#      init()
#      print(" Secure E-Commerce Database Ready!")