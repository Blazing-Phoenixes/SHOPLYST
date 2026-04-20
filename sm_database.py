# Login_database.py
import sqlite3
import re
import os
from passlib.hash import pbkdf2_sha256
from datetime import datetime
import shutil
import sys

DB_NAME = "app.db"

# DATABASE INITIALIZATION
def connect_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # User table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE,
            role TEXT DEFAULT 'user',  -- user / admin / super_admin
            profile_image BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Friend requests
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS friend_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                receiver TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Chat messages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                receiver TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                is_read INTEGER DEFAULT 0
            )
        ''')
        # Media uploads
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                username TEXT,
                file_path BLOB,
                file_type TEXT,
                visibility TEXT CHECK (visibility IN ('public', 'private')),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Likes
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS media_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id INTEGER,
            username TEXT
        )
        """)

        # Comments
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS media_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id INTEGER,
            username TEXT,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Caption
        # SAFE ADD COLUMN (no crash)
        cursor.execute("PRAGMA table_info(media)")
        columns = [col[1] for col in cursor.fetchall()]

        if "caption" not in columns:
            cursor.execute("ALTER TABLE media ADD COLUMN caption TEXT")

        #PRODUCTS
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL CHECK(price >= 0),
            description TEXT,
            image BLOB,
            category TEXT,
            stock INTEGER DEFAULT 0 CHECK(stock >= 0)
        )
        """)
        #CART
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
        #ORDERS
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
        #ORDER ITEMS
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
        #WISHLIST
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

# VALIDATION HELPERS
def validate_password(password):
    return (len(password) >= 8 and
            re.search(r"[A-Z]", password) and
            re.search(r"[a-z]", password) and
            re.search(r"[0-9]", password) and
            re.search(r"[!@#$%^&*(),.?\":{}|<>]", password))

def validate_username(username):
    return re.fullmatch(r'[A-Za-z0-9_]+', username)

def validate_phone(phone):
    return phone.isdigit() and len(phone) == 10

def validate_email(email):
    return re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email)

# USER REGISTRATION
def add_user(username, phone, password, email=None):
    if not validate_username(username):
        return "Username must contain only letters, numbers, and underscores."
    if not validate_phone(phone):
        return "Phone number must contain exactly 10 digits."
    if not validate_password(password):
        return "Password must include uppercase, lowercase, digit, and special character."
    if email and not validate_email(email):
        return "Invalid email format."

    hashed_password = pbkdf2_sha256.hash(password)
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, phone, password, email, profile_image)
                VALUES (?, ?, ?, ?, ?)
            """, (username.lower(), phone, hashed_password, email, None))
            return "Account created successfully!"
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return "Username already exists!"
        elif "phone" in str(e):
            return "Phone number already exists!"
        elif "email" in str(e):
            return "Email already in use!"
        return "Account creation failed!"

# USER LOGIN
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

# ROLE
def promote_to_admin(username):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("UPDATE users SET role='admin' WHERE username=?", (username,))
    return "Promoted to admin"

def get_user_role(username):
    import sqlite3
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE username=?", (username,))
        result = c.fetchone()
        return result[0] if result else "user"
    
def assign_role(current_user, target_user, new_role):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()#Get current user's role
        c.execute("SELECT role FROM users WHERE username=?", (current_user,))
        current = c.fetchone()

        if not current or current[0] != "admin":
            return "Only admin can change roles"# Prevent self role change (already handled in UI but keep safe)
        if current_user == target_user:
            return "You cannot change your own role"# ALLOW admin → user (even if target is admin)
        c.execute("UPDATE users SET role=? WHERE username=?", (new_role, target_user))
        conn.commit()

        return f"{target_user} updated to {new_role}"

# PRODUCTS
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


# CART
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


# ORDERS
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


# WISHLIST
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


# ANALYTICS
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

# PROFILE FUNCTIONS
def get_user_details(identifier):
    identifier = str(identifier).lower()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, phone, email, profile_image 
            FROM users 
            WHERE LOWER(username)=? OR phone=?
        """, (identifier, identifier))
        return cursor.fetchone()

def get_profile_image_path(identifier):
    identifier = str(identifier).lower()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT profile_image FROM users WHERE LOWER(username)=? OR phone=?", 
                       (identifier, identifier))
        result = cursor.fetchone()
        return result[0] if result else None

def update_profile_image(identifier, image_path):
    identifier = str(identifier).lower()
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users 
                SET profile_image=? 
                WHERE LOWER(username)=? OR phone=?
            """, (image_path, identifier, identifier))
        return "Profile Picture Saved!"
    except sqlite3.IntegrityError:
        return "Can't save profile picture."

def update_email(identifier, new_email):
    if not validate_email(new_email):
        return "Invalid email format."
    identifier = str(identifier).lower()
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users 
                SET email=? 
                WHERE LOWER(username)=? OR phone=?
            """, (new_email, identifier, identifier))
            return "Email updated successfully!"
    except sqlite3.IntegrityError:
        return "Email already in use!"

# PASSWORD MANAGEMENT
def verify_password(identifier, input_password):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username=? OR phone=?", 
                       (identifier.lower(), identifier))
        result = cursor.fetchone()
    return result and pbkdf2_sha256.verify(input_password, result[0])

def update_password(identifier, new_password):
    if not validate_password(new_password):
        return "Password must include uppercase, lowercase, digit, and special character."
    hashed = pbkdf2_sha256.hash(new_password)
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password=? WHERE username=? OR phone=?", 
                       (hashed, identifier.lower(), identifier))
    return "Password updated successfully!"

# DELETE ACCOUNT
def delete_user(identifier):
    identifier = str(identifier).lower()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM friend_requests WHERE sender=? OR receiver=?", (identifier, identifier))
        cursor.execute("DELETE FROM chat_messages WHERE sender=? OR receiver=?", (identifier, identifier))
        cursor.execute("DELETE FROM media WHERE user_id=?", (identifier,))
        cursor.execute("DELETE FROM users WHERE username=? OR phone=?", (identifier, identifier))
    return "User deleted successfully!"

# FRIEND SYSTEM
def search_users(query):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, phone FROM users WHERE username LIKE ? OR phone LIKE ?",
                       (f"%{query}%", f"%{query}%"))
        return cursor.fetchall()

def send_friend_request(sender, receiver):
    if sender == receiver:
        return "You cannot send a request to yourself."
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username=? OR phone=?", (receiver.lower(), receiver))
        if not cursor.fetchone():
            return "Receiver does not exist."

        cursor.execute("""
            SELECT 1 FROM friend_requests 
            WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) 
        """, (sender, receiver, receiver, sender))
        if cursor.fetchone():
            return "Friend request already exists."

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO friend_requests (sender, receiver, timestamp) VALUES (?, ?, ?)",
                       (sender, receiver, timestamp))
    return "Request sent successfully!"

def get_friend_requests(receiver):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sender, timestamp 
            FROM friend_requests 
            WHERE receiver=? AND status='pending'
            ORDER BY timestamp DESC
        """, (receiver,))
        return cursor.fetchall()

def update_request_status(sender, receiver, action):
    if action not in ("accepted", "rejected"):
        return "Invalid action."
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        #  If accepted → add to friends table
        cursor.execute("UPDATE friend_requests SET status=? WHERE sender=? AND receiver=?", 
                           (action, sender, receiver))
        if action == "rejected":
        #  Delete request ONLY after action
            cursor.execute(
            "DELETE FROM friend_requests WHERE sender=? AND receiver=?",
            (sender, receiver)
        )

    return f"Request {action}!"

def get_friends_list(user):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT CASE 
                     WHEN sender=? THEN receiver 
                     ELSE sender 
                   END AS friend
            FROM friend_requests 
            WHERE (sender=? OR receiver=?) AND status='accepted'
        """, (user, user, user))
        return [row[0] for row in cursor.fetchall()]

def unfriend_user(user1, user2):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM friend_requests
            WHERE ((sender=? AND receiver=?) OR (sender=? AND receiver=?))
            AND status='accepted'
        """, (user1, user2, user2, user1))
        return cursor.rowcount > 0

# CHAT FUNCTIONS
def send_message(sender, receiver, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_messages (sender, receiver, message, timestamp)
            VALUES (?, ?, ?, ?)
        """, (sender, receiver, message, timestamp))

def get_conversation(user1, user2, limit=100):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sender, message, timestamp FROM chat_messages
            WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
            ORDER BY timestamp DESC LIMIT ?
        """, (user1, user2, user2, user1, limit))
        return cursor.fetchall()[::-1]

def mark_messages_as_read(sender, receiver):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE chat_messages SET is_read=1
            WHERE sender=? AND receiver=? AND is_read=0
        """, (sender, receiver))

def get_unread_count(user):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sender, COUNT(*) FROM chat_messages
            WHERE receiver=? AND is_read=0 GROUP BY sender
        """, (user,))
        return dict(cursor.fetchall())

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
MEDIA_DIR = os.path.join(BASE_DIR, "media")

def save_user_image(user_id, source_path):
    user_folder = os.path.join(MEDIA_DIR, f"user_{user_id}")
    os.makedirs(user_folder, exist_ok=True)

    file_name = os.path.basename(source_path)
    dest_path = os.path.join(user_folder, file_name)

    shutil.copy(source_path, dest_path)

    # 🔥 Convert to RELATIVE path before saving
    relative_path = os.path.relpath(dest_path, BASE_DIR)

    return relative_path

# MEDIA FUNCTIONS
def post_media(user_id, username, file_path, file_type, visibility, caption=""):
    if os.path.getsize(file_path) > 500 * 1024 * 1024:
        return "File size exceeds 500MB"

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO media (user_id, username, file_path, file_type, visibility, caption)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, username, file_path, file_type, visibility, caption))
        return "Posted"

def get_public_media():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM media WHERE visibility='public' ORDER BY timestamp DESC")
        return cursor.fetchall()

def get_private_media_for_user(user_id, friends_ids):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        if not friends_ids:
            cursor.execute("""
                SELECT * FROM media 
                WHERE visibility='private' AND user_id=?
                ORDER BY timestamp DESC
            """, (user_id,))
            return cursor.fetchall()

        format_ids = ','.join(['?'] * len(friends_ids))

        query = f"""
        SELECT * FROM media 
        WHERE visibility='private'
        AND (user_id=? OR user_id IN ({format_ids}))
        ORDER BY timestamp DESC
        """

        cursor.execute(query, [user_id] + friends_ids)
        return cursor.fetchall()
    
def delete_media(media_id, user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM media WHERE id=? AND user_id=?", (media_id, user_id))

def update_media(media_id, new_file_path, new_visibility, user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE media SET file_path=?, visibility=?
            WHERE id=? AND user_id=?
        """, (new_file_path, new_visibility, media_id, user_id))

def toggle_like(media_id, username):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 1 FROM media_likes
            WHERE media_id=? AND username=?
        """, (media_id, username))

        if cursor.fetchone():
            cursor.execute("""
                DELETE FROM media_likes
                WHERE media_id=? AND username=?
            """, (media_id, username))
            return "unliked"
        else:
            cursor.execute("""
                INSERT INTO media_likes (media_id, username)
                VALUES (?, ?)
            """, (media_id, username))
            return "liked"
        
def get_like_count(media_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM media_likes WHERE media_id=?
        """, (media_id,))
        return cursor.fetchone()[0]

def get_liked_users(media_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username FROM media_likes WHERE media_id=?
        """, (media_id,))
        return [row[0] for row in cursor.fetchall()]
    
def add_comment(media_id, username, comment):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO media_comments (media_id, username, comment)
            VALUES (?, ?, ?)
        """, (media_id, username, comment))

def get_comments(media_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, comment, created_at
            FROM media_comments
            WHERE media_id=?
            ORDER BY created_at ASC
        """, (media_id,))
        return cursor.fetchall()
    
def share_post_to_chat(sender, receiver, media_path, caption=""):
    message = f"[File]|{media_path}|{caption}"
    send_message(sender, receiver, message)