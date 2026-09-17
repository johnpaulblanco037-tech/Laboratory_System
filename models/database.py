######database.py#########

import os
import sqlite3
from logger import logger


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DB_PATH = os.path.join(
    BASE_DIR,
    "hardware_inventory.db"
)


def get_connection(db_name=DB_PATH):
    conn = sqlite3.connect(db_name)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def add_column_if_missing(cursor, table, column, definition):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]

    if column not in columns:
        cursor.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )


def init_db(db_name=DB_PATH):
    try:
        conn = get_connection(db_name)
        cursor = conn.cursor()

        # =========================================================
        # USERS
        # =========================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                failed_attempts INTEGER DEFAULT 0,
                locked_until REAL DEFAULT 0,
                is_verified INTEGER DEFAULT 1,
                verification_code TEXT
            )
            """
        )

        add_column_if_missing(
            cursor,
            "users",
            "email",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "users",
            "role",
            "TEXT DEFAULT 'user'"
        )

        add_column_if_missing(
            cursor,
            "users",
            "failed_attempts",
            "INTEGER DEFAULT 0"
        )

        add_column_if_missing(
            cursor,
            "users",
            "locked_until",
            "REAL DEFAULT 0"
        )

        add_column_if_missing(
            cursor,
            "users",
            "is_verified",
            "INTEGER DEFAULT 1"
        )

        add_column_if_missing(
            cursor,
            "users",
            "verification_code",
            "TEXT"
        )

        cursor.execute(
            """
            UPDATE users
            SET role = 'user'
            WHERE role IS NULL OR role = ''
            """
        )

        # Existing accounts remain usable.
        cursor.execute(
            """
            UPDATE users
            SET is_verified = 1
            WHERE is_verified IS NULL
            """
        )

        # =========================================================
        # PASSWORD RESET
        # =========================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS password_reset_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                new_password_hash TEXT NOT NULL,
                status TEXT DEFAULT 'Pending',
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        add_column_if_missing(
            cursor,
            "password_reset_requests",
            "user_id",
            "INTEGER"
        )

        add_column_if_missing(
            cursor,
            "password_reset_requests",
            "email",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "password_reset_requests",
            "new_password_hash",
            "TEXT"
        )

        add_column_if_missing(
            cursor,
            "password_reset_requests",
            "status",
            "TEXT DEFAULT 'Pending'"
        )

        # =========================================================
        # HARDWARE / INVENTORY
        # =========================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS hardware (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                status TEXT NOT NULL
            )
            """
        )

        # =========================================================
        # RESERVATIONS
        # =========================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reservations (
                reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                asset_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                reservation_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                purpose TEXT NOT NULL,
                remarks TEXT,
                status TEXT DEFAULT 'Pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(asset_id) REFERENCES hardware(item_id)
            )
            """
        )

        # =========================================================
        # BORROWING / RETURN
        # =========================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS borrowings (
                borrowing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                reservation_id INTEGER NOT NULL,
                borrow_date TEXT,
                expected_return TEXT,
                actual_return TEXT,
                condition_on_return TEXT,
                remarks TEXT,
                status TEXT DEFAULT 'Borrowed',
                FOREIGN KEY(reservation_id)
                    REFERENCES reservations(reservation_id)
            )
            """
        )

        conn.commit()
        conn.close()

        logger.info("Database initialized successfully.")

    except sqlite3.Error as e:
        logger.error(f"Database setup error: {e}")
        raise


if __name__ == "__main__":
    init_db()
