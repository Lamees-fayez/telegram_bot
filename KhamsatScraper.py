import re
import logging
from typing import List, Dict
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class KhamsatScraper:
    BASE_URL = "https://khamsat.com/community/requests"

    HEADERS = {
        "User-Agent": "Mozilla/5.0"
    }

    KEYWORDS = [
        "excel", "microsoft excel", "power bi", "dashboard", "داش بورد",
        "اكسل", "إكسل", "تحليل بيانات", "data analysis", "eda",
        "sql", "python", "automation", "scraping", "web scraping"
    ]

    def _normalize(self, text: str) -> str:
        text = (text or "").strip().lower()
        text = re.sub(r"\s+", " ", text)
        return text

    def _matches_keywords(self, title: str, desc: str = "") -> bool:
        haystack = self._normalize(f"{title} {desc}")
        return any(k.lower() in haystack for k in self.KEYWORDS)

    def _extract_job_id(self, url: str) -> str:
        match = re.search(r"/community/requests/(\d+)", url)
        return match.group(1) if match else ""

    def _canonicalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")

    def search_jobs(self) -> List[Dict]:
        jobs: List[Dict] = []

        try:
            logger.info("جلب صفحة خمسات...")

            response = requests.get(self.BASE_URL, headers=self.HEADERS, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            links = soup.select("a[href*='/community/requests/']")

            seen_ids = set()

            for link in links:
                href = link.get("href", "").strip()
                title = link.get_text(strip=True)

                if not href or not title:
                    continue

                if not href.startswith("http"):
                    href = "https://khamsat.com" + href

                href = self._canonicalize_url(href)
                job_id = self._extract_job_id(href)

                if not job_id or job_id in seen_ids:
                    continue

                seen_ids.add(job_id)

                # ✨ هنا خليته مرن شوية
                if not self._matches_keywords(title):
                    logger.info(f"not matched: {title}")
                    continue

                jobs.append({
                    "job_id": job_id,
                    "title": title,
                    "url": href,
                    "link": href,
                    "description": "",
                    "price": "",
                    "platform": "khamsat_requests"
                })

            logger.info(f"Khamsat jobs found = {len(jobs)}")

        except Exception as e:
            logger.error(f"Khamsat scraper error: {e}")

        return jobs
