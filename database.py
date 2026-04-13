import sqlite3
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class JobsDatabase:
    def __init__(self, db_name: str = "jobs_v3.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                title TEXT,
                url TEXT,
                link TEXT,
                source TEXT,
                price TEXT,
                description TEXT,
                posted_date TEXT
            )
        """)
        self.conn.commit()
        logger.info("✅ Database initialized")

    def _safe_str(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, (dict, list, tuple, set)):
            return str(value)
        return str(value)

    def job_exists(self, job_id: str) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT 1 FROM jobs WHERE job_id = ? LIMIT 1",
                (self._safe_str(job_id),)
            )
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"database:job_exists error: {e}")
            return False

    def add_job(self, job: Dict):
        try:
            cursor = self.conn.cursor()

            job_id = self._safe_str(job.get("job_id"))
            title = self._safe_str(job.get("title"))
            url = self._safe_str(job.get("url"))
            link = self._safe_str(job.get("link"))
            source = self._safe_str(job.get("source", ""))
            price = self._safe_str(job.get("price"))
            description = self._safe_str(job.get("description"))
            posted_date = self._safe_str(job.get("posted_date"))

            if not job_id:
                logger.warning(f"⚠️ Job skipped because job_id is empty: {job}")
                return

            cursor.execute("""
                INSERT OR IGNORE INTO jobs
                (job_id, title, url, link, source, price, description, posted_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                title,
                url,
                link,
                source,
                price,
                description,
                posted_date
            ))

            self.conn.commit()

        except Exception as e:
            logger.error(f"database:add_job error: {e}")
            logger.error(f"database:add_job payload: {job}")

    def get_new_jobs(self, jobs: List[Dict]) -> List[Dict]:
        new_jobs = []

        try:
            for job in jobs:
                if not isinstance(job, dict):
                    logger.warning(f"⚠️ Skipping non-dict job: {job}")
                    continue

                job_id = self._safe_str(job.get("job_id"))

                if not job_id:
                    logger.warning(f"⚠️ Skipping job with empty job_id: {job}")
                    continue

                if not self.job_exists(job_id):
                    self.add_job(job)
                    new_jobs.append(job)

        except Exception as e:
            logger.error(f"database:get_new_jobs error: {e}")

        return new_jobs

    def clear_all_jobs(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM jobs")
            self.conn.commit()
            logger.info("🗑️ All jobs deleted from database")
        except Exception as e:
            logger.error(f"database:clear_all_jobs error: {e}")

    def close(self):
        try:
            self.conn.close()
        except Exception as e:
            logger.error(f"database:close error: {e}")
