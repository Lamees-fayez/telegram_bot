import os
import time
import logging

from database import JobsDatabase
from MostaqlScraper import MostaqlScraper
from khamsat_scraper import KhamsatScraper
from telegram_bot import TelegramBot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s:%(name)s:%(message)s"
)
logger = logging.getLogger(__name__)


def normalize_job(job: dict, source_name: str) -> dict:
    if not isinstance(job, dict):
        return {}

    normalized = {
        "job_id": str(job.get("job_id", "")).strip(),
        "title": str(job.get("title", "")).strip(),
        "url": str(job.get("url", "")).strip(),
        "link": str(job.get("link", "")).strip(),
        "source": str(job.get("source", source_name)).strip(),
        "price": str(job.get("price", "")).strip(),
        "description": str(job.get("description", "")).strip(),
        "posted_date": str(job.get("posted_date", "")).strip(),
    }

    if not normalized["link"] and normalized["url"]:
        normalized["link"] = normalized["url"]

    if not normalized["url"] and normalized["link"]:
        normalized["url"] = normalized["link"]

    return normalized


def send_jobs_one_by_one(telegram, jobs):
    for job in jobs:
        try:
            # لو telegram_bot.py عندك فيه send_job(chat_id, job)
            if hasattr(telegram, "send_job"):
                telegram.send_job(telegram.chat_id, job)
            # لو فيه send_jobs(jobs)
            elif hasattr(telegram, "send_jobs"):
                telegram.send_jobs([job])
            else:
                logger.error("❌ TelegramBot has no send_job or send_jobs method")
                return
        except Exception as e:
            logger.error(f"❌ Error sending Telegram message: {e}")


def run_bot():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is missing in environment variables")

    if not chat_id:
        raise ValueError("TELEGRAM_CHAT_ID is missing in environment variables")

    db = JobsDatabase()
    mostaql = MostaqlScraper()
    khamsat = KhamsatScraper()
    telegram = TelegramBot(token=bot_token, db=db)

    # بنخزن chat_id داخل الكائن لو telegram_bot.py محتاجه
    telegram.chat_id = chat_id

    while True:
        try:
            logger.info("🚀 Starting scraping...")

            mostaql_jobs_raw = mostaql.search_jobs()
            khamsat_jobs_raw = khamsat.search_jobs()

            mostaql_jobs = [normalize_job(job, "mostaql") for job in mostaql_jobs_raw]
            khamsat_jobs = [normalize_job(job, "khamsat") for job in khamsat_jobs_raw]

            all_jobs = [job for job in (mostaql_jobs + khamsat_jobs) if job.get("job_id")]

            logger.info(f"📊 Total collected: {len(all_jobs)}")

            new_jobs = db.get_new_jobs(all_jobs)

            logger.info(f"🔥 New jobs: {len(new_jobs)}")

            if new_jobs:
                send_jobs_one_by_one(telegram, new_jobs)

            logger.info("===== RUN END =====")

        except Exception as e:
            logger.error(f"❌ Main loop error: {e}", exc_info=True)

        logger.info("⏳ Waiting 60 seconds...")
        time.sleep(60)


if __name__ == "__main__":
    run_bot()
