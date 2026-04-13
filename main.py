                        job["platform"] = name
                        key = self.build_key(name, job)

                        if not key:
                            continue

                        if key in self.sent_jobs:
                            continue

                        saved = self.db.save_job(name, job)

                        if saved:
                            self.sent_jobs.add(key)
                            self.save_state()
                            self.bot.notify_subscribers(job)
                            total += 1

                            logger.info(f"Sent: {job.get('title','')[:50]}")

                    except Exception as e:
                        logger.exception(f"Job error: {e}")

            except Exception as e:
                logger.exception(f"{name} scraper error: {e}")

        logger.info(f"New jobs: {total}")
        logger.info("===== RUN END =====")


if __name__ == "__main__":
    bot = JobsBot()

    while True:
        try:
            bot.run_once()
        except Exception as e:
            logger.exception(f"Main loop error: {e}")

        logger.info("Waiting 60 seconds...\n")
        time.sleep(60)
