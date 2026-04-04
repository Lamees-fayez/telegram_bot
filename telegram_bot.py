import logging
from typing import Dict, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

from database import JobsDatabase

logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self, token: str, db: JobsDatabase):
        self.token = token
        self.db = db
        self.updater = Updater(token=token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.setup_handlers()

    def setup_handlers(self):
        self.dispatcher.add_handler(CommandHandler("start", self.start_command))
        self.dispatcher.add_handler(CommandHandler("jobs", self.get_jobs))
        self.dispatcher.add_handler(CommandHandler("help", self.help_command))
        self.dispatcher.add_handler(CallbackQueryHandler(self.button_callback))

    def start_command(self, update: Update, context: CallbackContext):
        chat_id = update.effective_chat.id
        self.db.add_subscriber(chat_id)

        text = """
🎉 بوت فرص Excel & Power BI

تم تفعيل الإشعارات التلقائية عند نزول فرص جديدة ✅

الأوامر:
/jobs - آخر 8 فرص
/help - مساعدة
        """
        update.message.reply_text(text)

    def get_jobs(self, update: Update, context: CallbackContext):
        jobs = self.db.get_new_jobs()

        if not jobs:
            update.message.reply_text("📭 لا توجد فرص جديدة")
            return

        recent = jobs[:8]
        message_lines = [f"📊 آخر {len(recent)} فرصة:\n"]

        for i, job in enumerate(recent, 1):
            url = job.get("url", "")
            title = job.get("title", "بدون عنوان")
            price = job.get("price", "غير محدد")
            platform = job.get("platform", "unknown").replace("_", " ").title()
            posted_date = job.get("posted_date", job.get("scraped_date", ""))[:16]

            line1 = f"{i}. {title}"
            if "طلب" in title or "🆕" in title:
                line1 = f"🆕 {i}. {title}"

            message_lines.extend([
                line1,
                f"💰 {price}",
                f"🌐 {platform}",
                f"🔗 {url}",
                f"📅 {posted_date}",
                ""
            ])

        message = "\n".join(message_lines)

        keyboard = [[InlineKeyboardButton("🔄 تحديث", callback_data="refresh_jobs")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text(
            message,
            reply_markup=reply_markup,
            disable_web_page_preview=False
        )

    def button_callback(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()

        if query.data == "refresh_jobs":
            jobs = self.db.get_new_jobs()

            if not jobs:
                query.edit_message_text("📭 لا توجد فرص جديدة")
                return

            recent = jobs[:8]
            lines = [f"📊 محدث - {len(recent)} فرصة:\n"]

            for i, job in enumerate(recent, 1):
                title = job.get("title", "بدون عنوان")
                price = job.get("price", "غير محدد")
                platform = job.get("platform", "unknown").replace("_", " ").title()
                url = job.get("url", "")

                lines.extend([
                    f"{i}. {title}",
                    f"💰 {price}",
                    f"🌐 {platform}",
                    f"🔗 {url}",
                    ""
                ])

            keyboard = [[InlineKeyboardButton("🔄 تحديث", callback_data="refresh_jobs")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            query.edit_message_text(
                text="\n".join(lines),
                reply_markup=reply_markup,
                disable_web_page_preview=False
            )

    def help_command(self, update: Update, context: CallbackContext):
        help_text = """
🤖 البوت يبحث في:
- مستقل
- خمسات
- Upwork

المهارات:
✅ Excel / اكسل
✅ Power BI / داشبورد
✅ تحليل بيانات
✅ Web Scraping / سحب بيانات

/jobs - آخر الفرص
/start - تفعيل الإشعارات التلقائية
        """
        update.message.reply_text(help_text)

    def format_job_message(self, job: Dict) -> str:
        title = job.get("title", "فرصة جديدة")
        url = job.get("url", "")
        price = job.get("price", "غير محدد")
        platform = job.get("platform", "unknown").replace("_", " ").title()

        return (
            f"🚨 فرصة جديدة نزلت!\n\n"
            f"📌 {title}\n"
            f"💰 {price}\n"
            f"🌐 {platform}\n"
            f"🔗 {url}"
        )

    def notify_subscribers(self, job: Dict):
        subscribers = self.db.get_subscribers()
        if not subscribers:
            logger.info("لا يوجد مشتركين حالياً لتلقي الإشعارات")
            return

        msg = self.format_job_message(job)

        for chat_id in subscribers:
            try:
                self.updater.bot.send_message(
                    chat_id=chat_id,
                    text=msg,
                    disable_web_page_preview=False
                )
                logger.info(f"📨 تم إرسال إشعار إلى {chat_id}")
            except Exception as e:
                logger.error(f"فشل إرسال الإشعار إلى {chat_id}: {e}")

    def run(self):
        logger.info("Starting Telegram bot...")
        self.updater.start_polling()
        self.updater.idle()
