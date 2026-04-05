import sqlite3
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class JobsDatabase:
    def __init__(self, db_name="jobs.db"):
        self.db_name = db_name
        self.create_tables()

    def connect(self):
        return sqlite3.connect(self.db_name, timeout=30)

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

    def save_job(self, platform: str, job: Dict) -> bool:
        conn = None
        try:
            conn = self.connect()
            cur = conn.cursor()

            cur.execute("""
            INSERT INTO jobs (platform, title, url, price, description, posted_date)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                platform,
                job.get("title", ""),
                job.get("url", ""),
                job.get("price", ""),
                job.get("description", ""),
                job.get("posted_date", "")
            ))

            conn.commit()
            return True

        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            logger.error(f"save_job error: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_new_jobs(self, limit: int = 20) -> List[Dict]:
        conn = None
        try:
            conn = self.connect()
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("""
            SELECT platform, title, url, price, description, posted_date, scraped_date
            FROM jobs
            ORDER BY id DESC
            LIMIT ?
            """, (limit,))

            rows = cur.fetchall()
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"get_new_jobs error: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def add_subscriber(self, chat_id: int):
        conn = None
        try:
            conn = self.connect()
            cur = conn.cursor()

            cur.execute("""
            INSERT OR IGNORE INTO subscribers (chat_id)
            VALUES (?)
            """, (str(chat_id),))

            conn.commit()
            logger.info(f"✅ تم حفظ المشترك: {chat_id}")

        except Exception as e:
            logger.error(f"add_subscriber error: {e}")
        finally:
            if conn:
                conn.close()

    def get_subscribers(self) -> List[int]:
        conn = None
        try:
            conn = self.connect()
            cur = conn.cursor()

            cur.execute("SELECT chat_id FROM subscribers")
            rows = cur.fetchall()

            return [int(row[0]) for row in rows]

        except Exception as e:
            logger.error(f"get_subscribers error: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def count_jobs(self) -> int:
        conn = None
        try:
            conn = self.connect()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM jobs")
            count = cur.fetchone()[0]
            return count
        except Exception as e:
            logger.error(f"count_jobs error: {e}")
            return 0
        finally:
            if conn:
                conn.close()

    def clear_jobs(self):
        conn = None
        try:
            conn = self.connect()
            cur = conn.cursor()
            cur.execute("DELETE FROM jobs")
            conn.commit()
            logger.info("🗑️ تم مسح كل الوظائف من قاعدة البيانات")
        except Exception as e:
            logger.error(f"clear_jobs error: {e}")
        finally:
            if conn:
                conn.close()
