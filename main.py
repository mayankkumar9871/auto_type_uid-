import os
import json
import asyncio
from datetime import datetime
from fastapi import FastAPI
from telegram import Bot, Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ⚡ ENV Vars (Render dashboard pe set karo)
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "5557283805"))  # Sirf aapka user ID
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "-1002835701093"))  # jis GC me bhejna hai

# Data file
DATA_FILE = "uids.json"

# ✅ FastAPI app (Render ke liye)
app = FastAPI()

@app.get("/")
async def home():
    return {"status": "ok", "time": str(datetime.now())}

@app.get("/favicon.ico")
async def favicon():
    return {}

# ✅ Load / Save functions
def load_uids():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_uids(uids):
    with open(DATA_FILE, "w") as f:
        json.dump(uids, f, indent=2)

# ✅ Commands
async def add_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ You are not allowed.")

    if len(context.args) < 1:
        return await update.message.reply_text("Usage: /add <uid>")

    uid = context.args[0]
    uids = load_uids()
    if uid in uids:
        return await update.message.reply_text(f"✅ {uid} already exists.")

    uids.append(uid)
    save_uids(uids)
    await update.message.reply_text(f"✅ Added UID {uid}")

async def remove_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ You are not allowed.")

    if len(context.args) < 1:
        return await update.message.reply_text("Usage: /remove <uid>")

    uid = context.args[0]
    uids = load_uids()
    if uid not in uids:
        return await update.message.reply_text("❌ UID not found.")

    uids.remove(uid)
    save_uids(uids)
    await update.message.reply_text(f"✅ Removed UID {uid}")

async def list_uids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ You are not allowed.")

    uids = load_uids()
    if not uids:
        return await update.message.reply_text("No UIDs saved.")
    await update.message.reply_text("Saved UIDs:\n" + "\n".join(uids))

# ✅ Function to send scheduled message
async def send_likes(application: Application):
    uids = load_uids()
    bot = application.bot
    for uid in uids:
        text = f"/like ind {uid}"
        try:
            await bot.send_message(chat_id=GROUP_CHAT_ID, text=text)
            print(f"{datetime.now()} → Sent: {text}")
        except Exception as e:
            print(f"Error sending to {uid}: {e}")

# ✅ Start bot
async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("add", add_uid))
    application.add_handler(CommandHandler("remove", remove_uid))
    application.add_handler(CommandHandler("list", list_uids))

    # Scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(send_likes(application)), "interval", hours=25)
    scheduler.start()

    # Run
    await application.initialize()
    await application.start()
    print("Bot running...")

    await application.updater.start_polling()
    await application.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
