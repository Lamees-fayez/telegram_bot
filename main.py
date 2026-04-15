import os
import time
import logging
from dotenv import load_dotenv

from database import JobsDatabase
from telegram_bot import TelegramBot
from MostaqlScraper import MostaqlScraper
from KhamsatScraper import KhamsatScraper


load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 60))


def collect_jobs():
    all_jobs = []

    scrapers = [
        ("مستقل", MostaqlScraper()),
        ("خمسات", KhamsatScraper()),
        ("نفذلي", NafethlyScraper()),
    ]

    for site_name, scraper in scrapers:
        try:
            logger.info(f"بدأ فحص {site_name}")
            jobs = scraper.search_jobs()
            logger.info(f"{site_name}: تم العثور على {len(jobs)} مشروع")
            all_jobs.extend(jobs)
        except Exception as e:
            logger.exception(f"خطأ أثناء فحص {site_name}: {e}")

    return all_jobs


def main():
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not token:
        raise ValueError("BOT_TOKEN غير موجود في ملف البيئة")
    if not chat_id:
        raise ValueError("CHAT_ID غير موجود في ملف البيئة")

    db = JobsDatabase()
    bot = TelegramBot(token=token, db=db, polling_enabled=False)

    logger.info("البوت بدأ التشغيل")

    try:
        bot.send_message("تم تشغيل البوت بنجاح وهو الآن يراقب المشاريع الجديدة")
    except Exception as e:
        logger.exception(f"تعذر إرسال رسالة البداية: {e}")

    while True:
        try:
            jobs = collect_jobs()
            new_jobs = []

            for job in jobs:
                job_url = job.get("url", "").strip()

                if not job_url:
                    continue

                if not db.job_exists(job_url):
                    db.add_job(job)
                    new_jobs.append(job)

            if new_jobs:
                logger.info(f"تم العثور على {len(new_jobs)} مشروع جديد")
                for job in new_jobs:
                    try:
                        bot.send_new_job(job)
                        time.sleep(2)
                    except Exception as e:
                        logger.exception(f"فشل إرسال مشروع: {e}")
            else:
                logger.info("لا يوجد مشاريع جديدة حالياً")

        except Exception as e:
            logger.exception(f"خطأ في اللوب الرئيسية: {e}")

        logger.info(f"انتظار {CHECK_INTERVAL} ثانية قبل الفحص التالي")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
