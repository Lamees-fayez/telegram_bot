def scrape_all(self):
    logger.info("=" * 70)
    logger.info("🔍 بدء البحث في كل المواقع...")
    total_new = 0

    subs = self.db.get_subscribers()
    logger.info(f"👥 عدد المشتركين الحالي = {len(subs)}")

    for name, scraper in self.scrapers.items():
        try:
            logger.info(f"🌐 فحص المصدر: {name}")
            jobs = scraper.search_jobs() or []

            logger.info(f"📡 {name}: عدد النتائج الراجعة من السكريبر = {len(jobs)}")

            for job in jobs:
                try:
                    job["platform"] = name
                    saved = self.db.save_job(name, job)

                    if saved:
                        total_new += 1
                        logger.info(f"✅ تم حفظ مشروع جديد من {name}: {job.get('title', '')[:60]}")
                        self.bot.notify_subscribers(job)
                    else:
                        logger.info(f"⏭️ مشروع مكرر أو لم يتم حفظه: {job.get('title', '')[:60]}")

                except Exception as e:
                    logger.error(f"❌ خطأ أثناء حفظ/إشعار مشروع من {name}: {e}")

        except Exception as e:
            logger.error(f"❌ خطأ أثناء تشغيل scraper {name}: {e}")

    logger.info(f"✅ إجمالي المشاريع الجديدة المحفوظة = {total_new}")
    self.show_db_status()
