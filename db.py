import os
import sqlite3
import tempfile

TEMP_DIR = tempfile.gettempdir()

DB_PATH = os.path.join(
    TEMP_DIR,
    "expenses.db"
)

def init_db():

    try:

        with sqlite3.connect(DB_PATH) as c:

            c.execute("PRAGMA journal_mode=WAL")

            # USERS TABLE

            c.execute("""
                CREATE TABLE IF NOT EXISTS users(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            """)

            # EXPENSES TABLE

            c.execute("""
                CREATE TABLE IF NOT EXISTS expenses(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT DEFAULT '',
                    note TEXT DEFAULT '',
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)

            print("Database initialized successfully")

    except Exception as e:

        print(f"Database initialization error: {e}")

        raise