import os
import json
import asyncio
from datetime import datetime
from fastapi import FastAPI
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "5557283805"))
DEFAULT_INTERVAL_HOURS = 25
DEFAULT_MESSAGE = "/like ind 6535092553"

UID_FILE = "uids.json"
GROUP_FILE = "groups.json"
TIME_FILE = "time.json"

# ---------------- FastAPI ----------------
app = FastAPI()

@app.get("/")
async def home():
    return {"status": "ok", "time": str(datetime.now())}

@app.get("/favicon.ico")
async def favicon():
    return {}

# ---------------- Helpers ----------------
def load_json(file, default=None):
    if not os.path.exists(file):
        return default if default is not None else []
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

# ---------------- Command Checks ----------------
def owner_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != OWNER_ID:
            return await update.message.reply_text("❌ You are not allowed.")
        return await func(update, context)
    return wrapper

# ---------------- Commands ----------------
@owner_only
async def add_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        return await update.message.reply_text("Usage: /add <uid>")
    uid = context.args[0]
    uids = load_json(UID_FILE, [])
    if uid in uids:
        return await update.message.reply_text(f"✅ {uid} already exists.")
    uids.append(uid)
    save_json(UID_FILE, uids)
    await update.message.reply_text(f"✅ Added UID {uid}")

@owner_only
async def remove_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        return await update.message.reply_text("Usage: /remove <uid>")
    uid = context.args[0]
    uids = load_json(UID_FILE, [])
    if uid not in uids:
        return await update.message.reply_text("❌ UID not found.")
    uids.remove(uid)
    save_json(UID_FILE, uids)
    await update.message.reply_text(f"✅ Removed UID {uid}")

@owner_only
async def list_uids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uids = load_json(UID_FILE, [])
    if not uids:
        return await update.message.reply_text("No UIDs saved.")
    await update.message.reply_text("Saved UIDs:\n" + "\n".join(uids))

@owner_only
async def allow_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        return await update.message.reply_text("Usage: /allow <group_id>")
    group_id = context.args[0]
    groups = load_json(GROUP_FILE, [])
    if group_id in groups:
        return await update.message.reply_text(f"✅ Group {group_id} already allowed.")
    groups.append(group_id)
    save_json(GROUP_FILE, groups)
    await update.message.reply_text(f"✅ Group {group_id} allowed.")

@owner_only
async def check_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is working currently.")

@owner_only
async def type_uids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uids = load_json(UID_FILE, [])
    groups = load_json(GROUP_FILE, [])
    if not uids or not groups:
        return await update.message.reply_text("❌ No UIDs or allowed groups found.")
    for uid in uids:
        text = f"/like ind {uid}"
        for group_id in groups:
            try:
                await context.bot.send_message(chat_id=int(group_id), text=text)
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Error sending {uid} to {group_id}: {e}")
    await update.message.reply_text("✅ /type completed.")

@owner_only
async def change_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        return await update.message.reply_text('Usage: /time <hours> "<message>"')
    try:
        hours = float(context.args[0])
        message = " ".join(context.args[1:]).strip('"')
    except:
        return await update.message.reply_text('❌ Invalid format.')
    save_json(TIME_FILE, {"hours": hours, "message": message})
    await update.message.reply_text(f"✅ Interval updated to {hours} hours with message: {message}")

# ---------------- Scheduler ----------------
async def scheduled_task(application: Application):
    groups = load_json(GROUP_FILE, [])
    if not groups:
        return
    time_data = load_json(TIME_FILE, {"hours": DEFAULT_INTERVAL_HOURS, "message": DEFAULT_MESSAGE})
    message = time_data.get("message", DEFAULT_MESSAGE)
    for group_id in groups:
        try:
            await application.bot.send_message(chat_id=int(group_id), text=message)
            print(f"{datetime.now()} → Sent scheduled message to {group_id}")
        except Exception as e:
            print(f"Error sending scheduled message to {group_id}: {e}")

# ---------------- Main ----------------
async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("add", add_uid))
    application.add_handler(CommandHandler("remove", remove_uid))
    application.add_handler(CommandHandler("list", list_uids))
    application.add_handler(CommandHandler("allow", allow_group))
    application.add_handler(CommandHandler("check", check_bot))
    application.add_handler(CommandHandler("type", type_uids))
    application.add_handler(CommandHandler("time", change_time))

    # Scheduler
    scheduler = AsyncIOScheduler()
    time_data = load_json(TIME_FILE, {"hours": DEFAULT_INTERVAL_HOURS, "message": DEFAULT_MESSAGE})
    scheduler.add_job(lambda: asyncio.create_task(scheduled_task(application)), "interval", hours=time_data["hours"])
    scheduler.start()

    print("🤖 Bot running on Python 3.11...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
