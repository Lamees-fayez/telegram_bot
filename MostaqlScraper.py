import requests
from bs4 import BeautifulSoup
import re
import time
import random
import logging
from typing import List, Dict
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class MostaqlScraper:
    BASE_URL = "https://mostaql.com"
    PROJECTS_URL = "https://mostaql.com/projects"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
            "Referer": "https://mostaql.com/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })

        self.keywords = [
            "excel", "اكسل",
            "power bi", "powerbi",
            "dashboard", "داشبورد", "داش بورد",
            "تحليل بيانات", "تحليل", "بيانات",
            "data analysis", "data analyst",
            "web scraping", "scraping", "scraper", "سحب بيانات"
        ]

    def normalize_text(self, text: str) -> str:
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip().lower()

    def is_relevant(self, text: str) -> bool:
        text = self.normalize_text(text)
        return any(kw.lower() in text for kw in self.keywords)

    def fix_url(self, href: str) -> str:
        if not href:
            return self.PROJECTS_URL
        return urljoin(self.BASE_URL, href)

    def extract_price_from_card(self, card) -> str:
        try:
            text = card.get_text(" ", strip=True)

            patterns = [
                r'(\d+\s*-\s*\d+\s*\$)',
                r'(\d+\s*\$)',
                r'(\$\s*\d+\s*-\s*\d+)',
                r'(\$\s*\d+)'
            ]

            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1).strip()

        except Exception:
            pass

        return "غير محدد"

    def extract_price_from_project_page(self, url: str) -> str:
        try:
            time.sleep(random.uniform(1, 2))
            response = self.session.get(url, timeout=20)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            page_text = soup.get_text(" ", strip=True)

            price_patterns = [
                r'ميزانية المشروع[^0-9$]*([\d\.,]+\s*-\s*[\d\.,]+\s*\$)',
                r'ميزانية المشروع[^0-9$]*([\d\.,]+\s*\$)',
                r'Budget[^0-9$]*([\d\.,]+\s*-\s*[\d\.,]+\s*\$)',
                r'Budget[^0-9$]*([\d\.,]+\s*\$)',
            ]

            for pattern in price_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

        except Exception as e:
            logger.warning(f"تعذر استخراج السعر من صفحة المشروع: {url} | {e}")

        return "غير محدد"

    def search_jobs(self) -> List[Dict]:
        jobs = []

        try:
            logger.info("🔍 البحث في مستقل (أحدث المشاريع المطابقة)...")

            response = self.session.get(self.PROJECTS_URL, timeout=20)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            project_links = soup.find_all("a", href=re.compile(r"^/project/\d+"))
            logger.info(f"📌 تم العثور على {len(project_links)} رابط مشروع مبدئي")

            temp_jobs = []
            seen_urls = set()

            for link in project_links:
                try:
                    href = link.get("href", "").strip()
                    if not href:
                        continue

                    full_url = self.fix_url(href)

                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)

                    match = re.search(r'/project/(\d+)', href)
                    project_id = int(match.group(1)) if match else 0

                    title = (
                        link.get_text(" ", strip=True)
                        or link.get("title", "")
                        or link.get("aria-label", "")
                    ).strip()

                    if not title or len(title) < 5:
                        continue

                    if not self.is_relevant(title):
                        continue

                    temp_jobs.append({
                        "id": project_id,
                        "title": title,
                        "url": full_url,
                        "link_elem": link
                    })

                except Exception as e:
                    logger.warning(f"تخطي عنصر أثناء قراءة مشروع من مستقل: {e}")
                    continue

            # ترتيب من الأحدث إلى الأقدم
            temp_jobs.sort(key=lambda x: x["id"], reverse=True)

            # آخر 10 مشاريع مطابقة
            latest_jobs = temp_jobs[:10]

            for item in latest_jobs:
                try:
                    link = item["link_elem"]
                    card = link.find_parent(["div", "article", "li", "section"])

                    price = "غير محدد"
                    if card:
                        price = self.extract_price_from_card(card)

                    if price == "غير محدد":
                        price = self.extract_price_from_project_page(item["url"])

                    job = {
                        "title": f"🆕 مشروع مستقل: {item['title'][:120]}",
                        "url": item["url"],
                        "price": price,
                        "description": "",
                        "posted_date": time.strftime("%Y-%m-%d %H:%M")
                    }

                    jobs.append(job)
                    logger.info(f"✅ {item['title'][:60]} -> {item['url']}")

                except Exception as e:
                    logger.warning(f"تعذر تجهيز مشروع من مستقل: {e}")
                    continue

        except Exception as e:
            logger.error(f"❌ خطأ في سحب مستقل: {e}")

        logger.info(f"🎯 تم جلب {len(jobs)} مشروع من مستقل (أحدث 10 مطابقين)")
        return jobs
