import os
import json
import logging
from dotenv import load_dotenv

from config import TELEGRAM_TOKEN
from database import JobsDatabase
from telegram_bot import TelegramBot
from MostaqlScraper import MostaqlScraper
from KhamsatScraper import KhamsatScraper

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobsBot:
    def __init__(self):
        self.db = JobsDatabase()

        self.bot = TelegramBot(
            TELEGRAM_TOKEN,
            self.db
        )

        self.scrapers = {
            "mostaql": MostaqlScraper(),
            "khamsat": KhamsatScraper(),
        }

        self.state_file = "jobs_state.json"
        self.sent_jobs = self.load_state()

    def load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except:
                pass
        return set()

    def save_state(self):
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(list(self.sent_jobs), f)

    def build_key(self, platform, job):
        return job.get("url") or job.get("link") or ""

    def run(self):
        if not TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_TOKEN missing")

        total = 0

        for name, scraper in self.scrapers.items():
            try:
                jobs = scraper.search_jobs()

                for job in jobs:
                    job["platform"] = name

                    key = self.build_key(name, job)

                    if not key or key in self.sent_jobs:
                        continue

                    saved = self.db.save_job(name, job)

                    if saved:
                        self.sent_jobs.add(key)
                        self.save_state()

                        self.bot.notify_subscribers(job)
                        total += 1

            except Exception as e:
                logger.error(f"{name} error: {e}")

        logger.info(f"done. new jobs: {total}")


if __name__ == "__main__":
    bot = JobsBot()
    bot.run()
