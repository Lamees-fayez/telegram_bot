import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# =========================================================
# TELEGRAM CONFIG
# =========================================================

# يفضل توحيد الاسم (BOT_TOKEN أو TELEGRAM_TOKEN)
TELEGRAM_TOKEN = (
    os.getenv("TELEGRAM_TOKEN") or
    os.getenv("BOT_TOKEN") or
    ""
).strip()

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN is missing. Please set it in .env file")

# Optional (fallback لو مفيش subscribers)
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# =========================================================
# SCRAPING CONFIG
# =========================================================

# كل قد إيه السكرايبنج يشتغل (بالثواني)
SCRAPE_INTERVAL_SECONDS = int(os.getenv("SCRAPE_INTERVAL_SECONDS", "60"))

# عدد النتائج من كل موقع
MAX_RESULTS_PER_SITE = int(os.getenv("MAX_RESULTS_PER_SITE", "10"))

# تشغيل المتصفح بدون واجهة
HEADLESS = os.getenv("HEADLESS", "true").strip().lower() == "true"

# =========================================================
# KEYWORDS (FILTER)
# =========================================================

KEYWORDS = [
    "excel",
    "اكسل",
    "power bi",
    "powerbi",
    "dashboard",
    "dash board",
    "داشبورد",
    "داش بورد",
    "web scraping",
    "scraping",
    "scraper",
    "سحب بيانات",
    "استخراج بيانات",
    "data entry",
    "تنظيف بيانات",
    "cleaning data",
    "etl"
]

# =========================================================
# ENVIRONMENT FLAGS
# =========================================================

# لو شغالة على GitHub Actions
GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS", "false").lower() == "true"

# =========================================================
# DEBUG (اختياري)
# =========================================================

DEBUG = os.getenv("DEBUG", "true").lower() == "true"

if DEBUG:
    print("✅ Config Loaded Successfully")
    print(f"Token Loaded: {'YES' if TELEGRAM_TOKEN else 'NO'}")
    print(f"Scrape Interval: {SCRAPE_INTERVAL_SECONDS}s")
    print(f"Max Results/Site: {MAX_RESULTS_PER_SITE}")
    print(f"Headless Mode: {HEADLESS}")
