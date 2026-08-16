import aiosqlite
from config import DATABASE_PATH

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    phone_number TEXT,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    category TEXT,
                    photo_file_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_premium BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    product_id INTEGER,
                    quantity INTEGER DEFAULT 1,
                    total_price REAL,
                    customer_name TEXT,
                    phone_number TEXT,
                    delivery_address TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cart (
                    user_id INTEGER,
                    product_id INTEGER,
                    quantity INTEGER DEFAULT 1,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, product_id)
                )
            """)
            await db.commit()

    async def register_user(self, user_id, username=None, first_name=None, last_name=None):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            """, (user_id, username, first_name, last_name))
            await db.commit()

    async def add_product(self, title, price, category, photo_file_id=None, description=None, is_premium=False):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO products (title, description, price, category, photo_file_id, is_premium)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, description, price, category, photo_file_id, is_premium))
            await db.commit()
            return cursor.lastrowid

    async def get_all_products(self, limit=None):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM products WHERE is_active = 1 ORDER BY created_at DESC"
            if limit:
                query += f" LIMIT {limit}"
            cursor = await db.execute(query)
            return [dict(row) for row in await cursor.fetchall()]

    async def get_product(self, product_id):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM products WHERE id = ? AND is_active = 1", (product_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_random_product(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM products WHERE is_active = 1 ORDER BY RANDOM() LIMIT 1")
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_products_by_category(self, category):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM products WHERE category = ? AND is_active = 1 ORDER BY created_at DESC", (category,))
            return [dict(row) for row in await cursor.fetchall()]

    async def get_premium_products(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM products WHERE is_premium = 1 AND is_active = 1 ORDER BY created_at DESC")
            return [dict(row) for row in await cursor.fetchall()]

    async def get_lowest_priced_products(self, limit=10):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM products WHERE is_active = 1 ORDER BY price ASC LIMIT ?", (limit,))
            return [dict(row) for row in await cursor.fetchall()]

    async def delete_product(self, product_id):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("UPDATE products SET is_active = 0 WHERE id = ?", (product_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def add_to_cart(self, user_id, product_id, quantity=1):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO cart (user_id, product_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, product_id) DO UPDATE SET quantity = quantity + ?
            """, (user_id, product_id, quantity, quantity))
            await db.commit()

    async def remove_from_cart(self, user_id, product_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
            await db.commit()

    async def get_cart(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT c.*, p.title, p.price, p.photo_file_id 
                FROM cart c JOIN products p ON c.product_id = p.id
                WHERE c.user_id = ? AND p.is_active = 1
            """, (user_id,))
            return [dict(row) for row in await cursor.fetchall()]

    async def clear_cart(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
            await db.commit()

    async def create_order(self, user_id, product_id, quantity, total_price, customer_name, phone_number, delivery_address):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO orders (user_id, product_id, quantity, total_price, customer_name, phone_number, delivery_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, product_id, quantity, total_price, customer_name, phone_number, delivery_address))
            await db.commit()
            return cursor.lastrowid

    async def get_all_orders(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT o.*, p.title as product_title, u.first_name, u.username
                FROM orders o
                JOIN products p ON o.product_id = p.id
                JOIN users u ON o.user_id = u.user_id
                ORDER BY o.created_at DESC
            """)
            return [dict(row) for row in await cursor.fetchall()]

    async def get_all_users(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT user_id, first_name, username FROM users")
            return [dict(row) for row in await cursor.fetchall()]

    async def get_user(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

db = Database()