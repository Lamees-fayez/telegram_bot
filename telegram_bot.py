def run(self):
    if not self.polling_enabled or not self.updater:
        print("Polling disabled")
        return

    print("🔥 BOT STARTED POLLING...")
    self.updater.start_polling()
    self.updater.idle()
