from datetime import datetime, timedelta, timezone
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes
import psycopg2

from .config import ADMIN_ID, VIP_CHANNEL_ID, BANK_INFO, CRYPTO_INFO
from . import database as db
from .utils import logger

# ---------------------
# START COMMAND
# ---------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        welcome_message = (
            f"👋 Welcome {user.first_name}!\n\n"
            """To join the 4-3-3 XAUUSD VIP Channel, please choose a payment method below:"""
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🏦 Bank Payment", callback_data="pay_bank"),
                InlineKeyboardButton("💸 Crypto Payment", callback_data="pay_crypto")
            ]
        ])

        await update.message.reply_text(welcome_message, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text("⚠️ An error occurred. Please try again.")

# ---------------------
# PAYMENT METHOD HANDLER
# ---------------------
async def handle_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        if query.data == "pay_bank":
            await query.edit_message_text("🏦 Bank Payment Selected:")
            await context.bot.send_message(chat_id=query.from_user.id, text=BANK_INFO)
        elif query.data == "pay_crypto":
            await query.edit_message_text("💸 Crypto Payment Selected:")
            await context.bot.send_message(chat_id=query.from_user.id, text=CRYPTO_INFO)
    except Exception as e:
        logger.error(f"Error in payment method handler: {e}")
        await query.edit_message_text("⚠️ An error occurred. Please try again.")

# ---------------------
# GET CHAT ID COMMAND
# ---------------------
async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    await update.message.reply_text(f"Chat ID: {chat.id}")

# ---------------------
# RECEIPT HANDLER
# ---------------------
async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.message.from_user
        telegram_id = user.id
        username = user.username or f"user_{telegram_id}"

        status = db.get_user_status(telegram_id)

        if status == 'pending':
            await update.message.reply_text("⏳ Your previous receipt is still pending review.")
            return
        elif status == 'approved':
            await update.message.reply_text("✅ You're already approved! Check your previous messages for the invite link.")
            return

        db.upsert_user_pending(telegram_id, username)

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{telegram_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{telegram_id}")
        ]])

        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=file_id,
                caption=f"🧾 New receipt from @{username} (ID: {telegram_id})",
                reply_markup=keyboard
            )
        else:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🧾 New receipt from @{username} (ID: {telegram_id}):\n\n{update.message.text}",
                reply_markup=keyboard
            )

        await update.message.reply_text("✅ Receipt received! We will verify and notify you shortly.")

    except psycopg2.IntegrityError as e:
        logger.error(f"Database integrity error in receipt handler: {e}")
        await update.message.reply_text("⚠️ There was a problem with your submission. Please try again.")
    except Exception as e:
        logger.error(f"Error handling receipt: {e}")
        await update.message.reply_text("⚠️ An error occurred while processing your receipt. Please try again.")

# ---------------------
# APPROVAL / REJECTION HANDLER
# ---------------------
async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        parts = query.data.split("_")
        if len(parts) != 2:
            raise ValueError("Invalid callback data format")

        action, telegram_id = parts
        telegram_id = int(telegram_id)

        user_data = db.get_user_by_id(telegram_id)
        if not user_data:
            raise ValueError("User not found in database")

        username = user_data[0] or f"user_{telegram_id}"

        if action == "approve":
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("1 Month", callback_data=f"plan_1m_{telegram_id}"),
                    InlineKeyboardButton("3 Months", callback_data=f"plan_3m_{telegram_id}"),
                    InlineKeyboardButton("1 Year", callback_data=f"plan_1y_{telegram_id}")
                ]
            ])
            msg = f"Choose subscription plan for @{username} (ID: {telegram_id}):"
            if query.message.photo:
                await query.edit_message_caption(caption=msg, reply_markup=keyboard)
            else:
                await query.edit_message_text(text=msg, reply_markup=keyboard)
            return

        elif action == "reject":
            db.update_user_status(telegram_id, 'rejected')

            await context.bot.send_message(
                chat_id=telegram_id,
                text="❌ Your payment receipt was rejected by the admin. Please contact support via @Tradesupport_433"
            )

            if query.message.photo:
                await query.edit_message_caption(f"❌ User @{username} (ID: {telegram_id}) has been rejected.")
            else:
                await query.edit_message_text(f"❌ User @{username} (ID: {telegram_id}) has been rejected.")

    except ValueError as e:
        logger.error(f"Validation error in approval handler: {e}")
        await query.edit_message_text(f"⚠️ Error: {str(e)}")
    except Exception as e:
        logger.error(f"Error in approval handler: {e}")
        await query.edit_message_text("⚠️ Failed to process approval. Please try again.")

# ---------------------
# PLAN SELECTION HANDLER
# ---------------------
async def handle_plan_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        # format: plan_1m_TELEGRAMID
        parts = query.data.split("_")
        if len(parts) != 3:
            raise ValueError("Invalid plan selection format")

        _, plan_type, telegram_id = parts
        telegram_id = int(telegram_id)

        user_data = db.get_user_by_id(telegram_id)
        if not user_data:
            raise ValueError("User not found")
        username = user_data[0] or f"user_{telegram_id}"

        # Calculate expiry
        now = datetime.now(timezone.utc)
        if plan_type == "1m":
            days = 30
            plan_name = "1 Month"
        elif plan_type == "3m":
            days = 90
            plan_name = "3 Months"
        elif plan_type == "1y":
            days = 365
            plan_name = "1 Year"
        else:
            raise ValueError("Unknown plan type")

        expiry_date = now + timedelta(days=days)
        approved_at = now.isoformat()

        db.update_user_status(telegram_id, 'approved', approved_at, expiry_date, plan_name)

        # Generate invite link
        invite_link_obj = await context.bot.create_chat_invite_link(
            chat_id=VIP_CHANNEL_ID,
            member_limit=1,
            expire_date=now + timedelta(hours=24),
            creates_join_request=False
        )
        invite_link = invite_link_obj.invite_link

        await context.bot.send_message(
            chat_id=telegram_id,
            text=(
                f"🎉 Congratulations @{username}!\n\n"
                f"Your payment has been verified for the **{plan_name}** plan.\n\n"
                f"👉 Click here to join: {invite_link}\n\n"
                f"⚠️ This link can be used only once and will expire in 24 hours."
            )
        )

        success_msg = f"✅ User @{username} (ID: {telegram_id}) approved for {plan_name}."
        if query.message.photo:
            await query.edit_message_caption(caption=success_msg)
        else:
            await query.edit_message_text(text=success_msg)

    except Exception as e:
        logger.error(f"Error in plan selection: {e}")
        await query.edit_message_text(f"⚠️ Error: {str(e)}")

# ---------------------
# LIST MEMBERS
# ---------------------
async def list_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return

        now = datetime.now(timezone.utc)
        users = db.get_approved_users()

        if not users:
            await update.message.reply_text("📭 No approved users found.")
            return

        message_lines = ["📊 VIP Members Status:"]

        for telegram_id, username, approved_at, expiry_date, r3d, r1d in users:
            if not expiry_date:
                continue
            try:
                # Ensure expiry_date is timezone-aware
                if expiry_date.tzinfo is None:
                    expiry_date = expiry_date.replace(tzinfo=timezone.utc)
                
                time_left = expiry_date - now

                if time_left.total_seconds() <= 0:
                    status = "❌ EXPIRED"
                else:
                    days_left = time_left.days
                    hours_left = time_left.seconds // 3600
                    status = f"⏳ {days_left}d {hours_left}h left"

                message_lines.append(
                    f"\n👤 @{username} (ID: {telegram_id})\n"
                    f"🕒 Approved: {approved_at[:16].replace('T', ' ')}\n"
                    f"📅 Expires: {expiry_date.strftime('%Y-%m-%d %H:%M')}\n"
                    f"🔹 Status: {status}\n"
                    f"{'-'*30}"
                )
            except Exception as e:
                logger.error(f"Error processing user {telegram_id}: {e}")
                continue

        full_message = "\n".join(message_lines)
        if len(full_message) > 4000:
            parts = [full_message[i:i+4000] for i in range(0, len(full_message), 4000)]
            for part in parts:
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(full_message)

    except Exception as e:
        logger.error(f"Error in list_members: {e}")
        await update.message.reply_text("⚠️ An error occurred while fetching member list.")

# ---------------------
# BROADCAST COMMAND
# ---------------------
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("❌ Unauthorized.")
            return

        if not context.args:
            await update.message.reply_text("📝 Usage: `/broadcast your message here`", parse_mode='Markdown')
            return

        message = " ".join(context.args)
        user_ids = db.get_active_users()

        if not user_ids:
            await update.message.reply_text("📭 No active users to broadcast to.")
            return

        sent_count = 0
        for user_id in user_ids:
            try:
                await context.bot.send_message(chat_id=user_id, text=f"📢 **Announcement:**\n\n{message}", parse_mode='Markdown')
                sent_count += 1
            except Exception as e:
                logger.error(f"Could not send broadcast to {user_id}: {e}")

        await update.message.reply_text(f"✅ Broadcast sent to {sent_count} users.")
    except Exception as e:
        logger.error(f"Error in broadcast: {e}")
        await update.message.reply_text("⚠️ Broadcast failed.")
