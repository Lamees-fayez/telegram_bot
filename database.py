import sqlite3
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class JobsDatabase:
    def __init__(self, db_name="jobs.db"):
        self.db_name = db_name
        self.create_tables()

    def connect(self):
        conn = sqlite3.connect(self.db_name, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def create_tables(self):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT,
            title TEXT,
            url TEXT UNIQUE,
            price TEXT,
            description TEXT,
            posted_date TEXT,
            scraped_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        conn.close()
