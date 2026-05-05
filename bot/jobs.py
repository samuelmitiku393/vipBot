from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.ext import ContextTypes

from .config import ADMIN_ID, VIP_CHANNEL_ID
from . import database as db
from .utils import logger

# ---------------------
# EXPIRY & REMINDER CHECKER
# ---------------------
async def remove_expired_users(context: ContextTypes.DEFAULT_TYPE, test_mode=False):
    try:
        now = datetime.now(timezone.utc)
        users = db.get_approved_users()

        for telegram_id, username, approved_at, expiry_date, reminded_3d, reminded_1d in users:
            if not expiry_date:
                continue

            # Ensure expiry_date is timezone-aware
            if expiry_date.tzinfo is None:
                expiry_date = expiry_date.replace(tzinfo=timezone.utc)

            time_left = expiry_date - now

            # 1. Check for Expiry
            if time_left.total_seconds() <= 0:
                try:
                    # Try to remove from channel
                    try:
                        await context.bot.ban_chat_member(chat_id=VIP_CHANNEL_ID, user_id=telegram_id)
                        await context.bot.unban_chat_member(chat_id=VIP_CHANNEL_ID, user_id=telegram_id)
                    except Exception as e:
                        logger.error(f"Couldn't remove user {telegram_id} from channel: {e}")

                    # Notify user
                    try:
                        await context.bot.send_message(
                            chat_id=telegram_id,
                            text="⚠️ **Your VIP subscription has expired.**\n\nPlease renew your subscription to continue accessing the channel.",
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        logger.error(f"Couldn't notify user {telegram_id}: {e}")

                    # Update status
                    db.update_user_status(telegram_id, 'expired')
                    logger.info(f"User {telegram_id} expired.")

                except Exception as e:
                    logger.error(f"Error processing expired user {telegram_id}: {e}")
                continue

            # 2. Check for Reminders (Only if not in test mode)
            if not test_mode:
                days_left = time_left.days
                
                # 3-day reminder
                if days_left == 3 and not reminded_3d:
                    try:
                        await context.bot.send_message(
                            chat_id=telegram_id,
                            text="⏳ **Reminder:** Your VIP subscription will expire in **3 days**.",
                            parse_mode='Markdown'
                        )
                        db.update_reminder_status(telegram_id, 'reminded_3d')
                    except Exception as e:
                        logger.error(f"Failed to send 3d reminder to {telegram_id}: {e}")

                # 1-day reminder
                elif days_left == 1 and not reminded_1d:
                    try:
                        await context.bot.send_message(
                            chat_id=telegram_id,
                            text="🚨 **Final Reminder:** Your VIP subscription will expire in **24 hours**!",
                            parse_mode='Markdown'
                        )
                        db.update_reminder_status(telegram_id, 'reminded_1d')
                    except Exception as e:
                        logger.error(f"Failed to send 1d reminder to {telegram_id}: {e}")

    except Exception as e:
        logger.error(f"Error in expiry checker: {e}")

# ---------------------
# TEST EXPIRY
# ---------------------
async def test_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    await update.message.reply_text("⏳ Simulating 30-second expiry...")
    await remove_expired_users(context, test_mode=True)
