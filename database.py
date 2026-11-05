
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

# Database file will be created inside the HOSTELMATE folder
DB_PATH = Path(__file__).resolve().parent / "hostelmate.db"


class Database:
    """Small compatibility wrapper for existing PostgreSQL-style queries."""

    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

    def execute(self, query, params=()):
        # Convert PostgreSQL placeholders to SQLite placeholders
        query = query.replace("%s", "?")
        return self.conn.execute(query, params)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


def get_db():
    return Database()


def init_db():
    db = get_db()

    try:
        statements = [
            """CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student',
                room TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",

            """CREATE TABLE IF NOT EXISTS resources(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL REFERENCES users(id),
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                kind TEXT NOT NULL DEFAULT 'Borrow',
                status TEXT NOT NULL DEFAULT 'Available',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",

            """CREATE TABLE IF NOT EXISTS resource_requests(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id INTEGER NOT NULL REFERENCES resources(id),
                requester_id INTEGER NOT NULL REFERENCES users(id),
                message TEXT,
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(resource_id, requester_id)
            )""",

            """CREATE TABLE IF NOT EXISTS complaints(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'Normal',
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",

            """CREATE TABLE IF NOT EXISTS lost_found(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                title TEXT NOT NULL,
                kind TEXT NOT NULL,
                location TEXT NOT NULL,
                description TEXT,
                contact TEXT,
                status TEXT NOT NULL DEFAULT 'Open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",

            """CREATE TABLE IF NOT EXISTS mess_menu(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day TEXT NOT NULL,
                breakfast TEXT NOT NULL,
                lunch TEXT NOT NULL,
                dinner TEXT NOT NULL,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",

            """CREATE TABLE IF NOT EXISTS mess_feedback(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                rating INTEGER NOT NULL,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",

            """CREATE TABLE IF NOT EXISTS notices(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                created_by INTEGER NOT NULL REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        ]

        for statement in statements:
            db.execute(statement)

        # Default accounts
        accounts = [
            ('Hostel Admin', 'admin@hostelmate.com',
             'Admin@123', 'admin'),
            ('Hostel Warden', 'warden@hostelmate.com',
             'Warden@123', 'warden')
        ]

        for name, email, password, role in accounts:
            exists = db.execute(
                'SELECT id FROM users WHERE email=%s',
                (email,)
            ).fetchone()

            if not exists:
                db.execute(
                    """INSERT INTO users
                    (name, email, password_hash, role, room)
                    VALUES (%s, %s, %s, %s, %s)""",
                    (name, email, generate_password_hash(password),
                     role, '')
                )

        db.commit()
        print("SQLite database initialized successfully!")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
