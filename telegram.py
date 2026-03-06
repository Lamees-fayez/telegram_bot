import requests
from bs4 import BeautifulSoup
import telegram
import time

# ضع توكن البوت و ID الشات هنا
TOKEN = "8322731519:AAG9qnGdud3cjvNGXk97yIMhlUJcJwicfAg"
CHAT_ID="8322731519"

bot = telegram.Bot(token=TOKEN)

# الكلمات المفتاحية التي يبحث عنها البوت
keywords = [
    "microsoft excel",
    "excel",
    "اكسل",
    "dashboard",
    "داش بورد",
    "eda",
    "تحليل بيانات",
    "data analysis",
    "EDA",
    "web scrapping",
    "سحب بيانات",
    "data entry",
    "ادخال بيانات"
]

# لتجنب تكرار إرسال نفس الوظيفة
sent_links = set()

headers = {
    "User-Agent": "Mozilla/5.0"
}

def send(title, link, site):
    msg = f"""
وظيفة جديدة 🔥

الموقع: {site}

العنوان:
{title}

الرابط:
{link}
"""
    bot.send_message(chat_id=CHAT_ID, text=msg)

# فحص موقع مستقل
def check_mostaql():
    url = "https://mostaql.com/projects"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "lxml")
    jobs = soup.find_all("a")
    for job in jobs:
        title = job.text.lower()
        if any(k in title for k in keywords):
            link = job.get("href")
            if link and link not in sent_links:
                link = "https://mostaql.com" + link
                send(title, link, "Mostaql")
                sent_links.add(link)

# فحص موقع نفذلي
def check_nafezly():
    url = "https://nafezly.com/projects"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "lxml")
    jobs = soup.find_all("a")
    for job in jobs:
        title = job.text.lower()
        if any(k in title for k in keywords):
            link = job.get("href")
            if link and link not in sent_links:
                send(title, link, "Nafezly")
                sent_links.add(link)

# فحص Upwork
def check_upwork():
    url = "https://www.upwork.com/nx/search/jobs/?q=data%20analysis"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "lxml")
    jobs = soup.find_all("a")
    for job in jobs:
        title = job.text.lower()
        if any(k in title for k in keywords):
            link = job.get("href")
            if link and link not in sent_links:
                link = "https://www.upwork.com" + link
                send(title, link, "Upwork")
                sent_links.add(link)

# فحص خمسات
def check_khamsat():
    url = "https://khamsat.com/community/requests"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "lxml")
    jobs = soup.find_all("a")
    for job in jobs:
        title = job.text.lower()
        if any(k in title for k in keywords):
            link = job.get("href")
            if link and link not in sent_links:
                link = "https://khamsat.com" + link
                send(title, link, "Khamsat")
                sent_links.add(link)

# الحلقة الرئيسية: فحص كل 30 ثانية
while True:
    try:
        check_mostaql()
        check_nafezly()
        check_upwork()
        check_khamsat()
    except:
        pass

    time.sleep(30)
