import datetime as dt
from datetime import timezone
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
from datetime import timezone
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)

from bot.config import BOT_TOKEN
from bot.database import init_db
from bot.utils import setup_logging
from bot import handlers
from bot import jobs

# Set up logging early
logger = setup_logging()

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def start_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    logger.info(f"Started dummy web server on port {port}")
    server.serve_forever()

def main():
    # Start the dummy server in a background thread
    threading.Thread(target=start_dummy_server, daemon=True).start()

    # Initialize database with verification
    try:
        init_db()
        logger.info("Database verified successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        exit(1)

    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        # Add handlers
        app.add_handler(CommandHandler("start", handlers.start))
        app.add_handler(CommandHandler("getid", handlers.get_chat_id))
        app.add_handler(CommandHandler("testexpiry", jobs.test_expiry))
        app.add_handler(CommandHandler("members", handlers.list_members))
        app.add_handler(CommandHandler("broadcast", handlers.broadcast))

        app.add_handler(CallbackQueryHandler(handlers.handle_approval, pattern="^(approve_|reject_)"))
        app.add_handler(CallbackQueryHandler(handlers.handle_plan_selection, pattern="^plan_"))
        app.add_handler(CallbackQueryHandler(handlers.handle_payment_method, pattern="^pay_"))
        app.add_handler(MessageHandler(filters.PHOTO | (filters.TEXT & ~filters.COMMAND), handlers.handle_receipt))

        # Schedule daily expiry check at midnight UTC
        app.job_queue.run_daily(
            jobs.remove_expired_users,
            time=dt.time(hour=0, minute=0, tzinfo=timezone.utc),
            name="daily_expiry_check"
        )

        logger.info("Bot is starting...")
        app.run_polling()
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")

if __name__ == "__main__":
    main()
