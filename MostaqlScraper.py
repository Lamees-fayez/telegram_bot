import requests
from bs4 import BeautifulSoup
import re
import time
import random
import logging
from typing import List, Dict
from urllib.parse import urljoin, quote

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
            "dashboard", "dash board", "داشبورد", "داش بورد",
            "تحليل بيانات", "تحليل", "بيانات",
            "data analysis", "data analyst",
            "web scraping", "scraping", "scraper", "سحب بيانات",
            "data entry", "تنظيف بيانات", "cleaning data"
        ]

    def normalize_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r"\s+", " ", text)
        return text

    def is_relevant(self, text: str) -> bool:
        text = self.normalize_text(text)
        return any(k.lower() in text for k in self.keywords)

    def fix_url(self, href: str) -> str:
        if not href:
            return self.PROJECTS_URL
        return urljoin(self.BASE_URL, href)

    def extract_project_id(self, href: str) -> int:
        match = re.search(r"/project/(\d+)", href or "")
        return int(match.group(1)) if match else 0

    def extract_price_from_text(self, text: str) -> str:
        if not text:
            return "غير محدد"

        patterns = [
            r'(\d[\d,\.]*\s*-\s*\d[\d,\.]*\s*\$)',
            r'(\d[\d,\.]*\s*\$)',
            r'(\$\s*\d[\d,\.]*\s*-\s*\d[\d,\.]*)',
            r'(\$\s*\d[\d,\.]*)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return "غير محدد"

    def extract_price_from_card(self, card) -> str:
        try:
            return self.extract_price_from_text(card.get_text(" ", strip=True))
        except Exception:
            return "غير محدد"

    def get_project_details(self, url: str) -> Dict:
        result = {
            "description": "",
            "price": "غير محدد"
        }

        try:
            time.sleep(random.uniform(0.8, 1.5))
            response = self.session.get(url, timeout=20)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(" ", strip=True)

            result["price"] = self.extract_price_from_text(text)

            # محاولة التقاط وصف مفيد
            blocks = soup.find_all(["p", "div", "section"])
            best_text = ""
            for block in blocks:
                block_text = block.get_text(" ", strip=True)
                if len(block_text) > len(best_text):
                    best_text = block_text

            if best_text:
                result["description"] = best_text[:1200]

        except Exception as e:
            logger.warning(f"تعذر قراءة تفاصيل المشروع: {url} | {e}")

        return result

    def collect_projects_from_page(self, page_url: str) -> List[Dict]:
        projects = []

        try:
            response = self.session.get(page_url, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            links = soup.find_all("a", href=re.compile(r"^/project/\d+"))
            seen = set()

            for link in links:
                href = link.get("href", "").strip()
                if not href:
                    continue

                full_url = self.fix_url(href)
                if full_url in seen:
                    continue
                seen.add(full_url)

                title = (
                    link.get_text(" ", strip=True)
                    or link.get("title", "")
                    or link.get("aria-label", "")
                    or ""
                ).strip()

                if len(title) < 5:
                    continue

                project_id = self.extract_project_id(href)
                card = link.find_parent(["div", "article", "li", "section"])
                card_text = card.get_text(" ", strip=True) if card else ""
                card_price = self.extract_price_from_card(card) if card else "غير محدد"

                projects.append({
                    "id": project_id,
                    "title": title,
                    "url": full_url,
                    "card_text": card_text,
                    "card_price": card_price
                })

        except Exception as e:
            logger.error(f"خطأ أثناء قراءة صفحة مستقل: {page_url} | {e}")

        return projects

    def search_jobs(self) -> List[Dict]:
        logger.info("🔍 البحث في مستقل عن آخر المشاريع المطابقة...")
        collected = []

        # أول 3 صفحات من المشاريع لزيادة فرصة الوصول لأحدث 10 مطابقين
        page_urls = [
            self.PROJECTS_URL,
            f"{self.PROJECTS_URL}?page=2",
            f"{self.PROJECTS_URL}?page=3",
        ]

        for page_url in page_urls:
            logger.info(f"📄 قراءة: {page_url}")
            page_projects = self.collect_projects_from_page(page_url)
            logger.info(f"📌 تم العثور على {len(page_projects)} مشروع مبدئي")
            collected.extend(page_projects)
            time.sleep(random.uniform(1, 2))

        # إزالة التكرار
        unique_map = {}
        for item in collected:
            if item["url"] not in unique_map:
                unique_map[item["url"]] = item

        all_projects = list(unique_map.values())

        # ترتيب بالأحدث
        all_projects.sort(key=lambda x: x["id"], reverse=True)

        matched_jobs = []

        for item in all_projects:
            try:
                # مطابقة أولية من العنوان أو نص الكارد
                initial_text = f"{item['title']} {item.get('card_text', '')}"
                needs_deep_check = self.is_relevant(initial_text)

                details = {"description": "", "price": item.get("card_price", "غير محدد")}

                # لو مفيش تطابق في العنوان/الكارد، ندخل الصفحة نفسها
                if not needs_deep_check:
                    details = self.get_project_details(item["url"])
                    full_text = f"{item['title']} {details.get('description', '')}"
                    if not self.is_relevant(full_text):
                        continue
                else:
                    # حتى لو مطابق، ندخل الصفحة لتحسين الوصف والسعر
                    details = self.get_project_details(item["url"])

                price = details.get("price") or item.get("card_price") or "غير محدد"
                description = details.get("description", "")

                job = {
                    "title": f"🆕 مشروع مستقل: {item['title'][:120]}",
                    "url": item["url"],
                    "price": price,
                    "description": description[:500],
                    "posted_date": time.strftime("%Y-%m-%d %H:%M")
                }

                matched_jobs.append(job)
                logger.info(f"✅ مطابق: {item['title'][:70]}")

                if len(matched_jobs) >= 10:
                    break

            except Exception as e:
                logger.warning(f"تخطي مشروع أثناء المطابقة: {e}")
                continue

        logger.info(f"🎯 تم جلب {len(matched_jobs)} مشروع من مستقل (آخر 10 مطابقين)")
        return matched_jobs
