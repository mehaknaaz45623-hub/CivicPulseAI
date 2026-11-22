import sqlite3
from pathlib import Path

DATABASE_NAME = Path(__file__).resolve().parent / "civicpulse.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_connection()

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                status TEXT DEFAULT 'Pending',
                severity TEXT DEFAULT 'Medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                hashed_password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'citizen',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add user_id to existing reports table if missing
        report_columns = connection.execute(
            "PRAGMA table_info(reports)"
        ).fetchall()

        report_column_names = [
            column["name"] for column in report_columns
        ]

        if "user_id" not in report_column_names:
            connection.execute("""
                ALTER TABLE reports
                ADD COLUMN user_id INTEGER REFERENCES users(id)
            """)

        # Add AI confidence to existing reports table if missing
        if "ai_confidence" not in report_column_names:
            connection.execute("""
                ALTER TABLE reports
                ADD COLUMN ai_confidence REAL DEFAULT 0
            """)

        connection.commit()
        print("CivicPulse AI database initialized successfully!")

    finally:
        connection.close()