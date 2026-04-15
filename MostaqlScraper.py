import requests
from bs4 import BeautifulSoup
import re

KEYWORDS = [
    "excel", "power bi", "dashboard",
    "اكسل", "داشبورد", "تحليل بيانات",
    "sql", "python", "scraping","سحب بيانات","web scrapping","Excel","data analysis"
]


class MostaqlScraper:
    URL = "https://mostaql.com/projects"

    def search_jobs(self):
        jobs = []

        res = requests.get(self.URL)
        soup = BeautifulSoup(res.text, "html.parser")

        links = soup.find_all("a", href=re.compile(r"/project/\d+"))

        seen = set()

        for link in links:
            title = link.get_text(strip=True)
            href = link.get("href")

            if not title or not href:
                continue

            full_url = "https://mostaql.com" + href

            job_id = re.search(r"/project/(\d+)", href)
            if not job_id:
                continue

            job_id = job_id.group(1)

            if job_id in seen:
                continue

            seen.add(job_id)

            text = title.lower()

            if not any(k in text for k in KEYWORDS):
                continue

            jobs.append({
                "job_id": job_id,
                "title": title,
                "url": full_url,
                "platform": "mostaql"
            })

        return jobs
