import os
import sqlite3
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class JobsDatabase:
    def __init__(self, db_name=None):
        self.db_name = db_name or os.getenv("DB_NAME", "jobs.db")
        self.create_tables()

    def connect(self):
        conn = sqlite3.connect(self.db_name, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def create_tables(self):
        conn = None
        try:
            conn = self.connect()
            cur = conn.cursor()

            cur.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                title TEXT,
                url TEXT NOT NULL UNIQUE,
                price TEXT,
                description TEXT,
                posted_date TEXT,
                scraped_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_platform ON jobs(platform)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_scraped_date ON jobs(scraped_date DESC)")

            conn.commit()

        except Exception as e:
            logger.error(f"create_tables error: {e}")
        finally:
            if conn:
                conn.close()

    def save_job(self, platform: str, job: Dict) -> bool:
        conn = None
        try:
            conn = self.connect()
            cur = conn.cursor()

            url = (job.get("url") or job.get("link") or "").strip()
            title = (job.get("title") or "").strip()
            price = (job.get("price") or "").strip()
            description = (job.get("description") or "").strip()
            posted_date = (job.get("posted_date") or "").strip()

            if not url:
                logger.warning(f"تم تخطي وظيفة بدون url: {title[:60]}")
                return False

            cur.execute("""
            INSERT INTO jobs (platform, title, url, price, description, posted_date)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                platform,
                title,
                url,
                price,
                description,
                posted_date
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

    def job_exists(self, url: str) -> bool:
        conn = None
        try:
            conn = self.connect()
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM jobs WHERE url = ? LIMIT 1", (url,))
            return cur.fetchone() is not None
        except Exception as e:
            logger.error(f"job_exists error: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_new_jobs(self, limit: int = 20) -> List[Dict]:
        conn = None
        try:
            conn = self.connect()
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

        except Exception as e:
            logger.error(f"add_subscriber error: {e}")
        finally:
            if conn:
                conn.close()

    def remove_subscriber(self, chat_id: int):
        conn = None
        try:
            conn = self.connect()
            cur = conn.cursor()

            cur.execute("DELETE FROM subscribers WHERE chat_id = ?", (str(chat_id),))
            conn.commit()

        except Exception as e:
            logger.error(f"remove_subscriber error: {e}")
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

            return [int(row["chat_id"]) for row in rows]

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
            cur.execute("SELECT COUNT(*) AS total FROM jobs")
            row = cur.fetchone()
            return row["total"] if row else 0
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
            logger.info("تم مسح كل الوظائف من قاعدة البيانات")
        except Exception as e:
            logger.error(f"clear_jobs error: {e}")
        finally:
            if conn:
                conn.close()
