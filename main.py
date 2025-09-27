import os
import json
import time
from datetime import datetime
from fastapi import FastAPI
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler
from apscheduler.schedulers.background import BackgroundScheduler

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
def home():
    return {"status": "ok", "time": str(datetime.now())}

@app.get("/favicon.ico")
def favicon():
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

def owner_only(func):
    def wrapper(update, context):
        if update.effective_user.id != OWNER_ID:
            update.message.reply_text("❌ You are not allowed.")
            return
        return func(update, context)
    return wrapper

# ---------------- Commands ----------------
@owner_only
def add_uid(update, context):
    if len(context.args) < 1:
        update.message.reply_text("Usage: /add <uid>")
        return
    uid = context.args[0]
    uids = load_json(UID_FILE, [])
    if uid in uids:
        update.message.reply_text(f"✅ {uid} already exists.")
        return
    uids.append(uid)
    save_json(UID_FILE, uids)
    update.message.reply_text(f"✅ Added UID {uid}")

@owner_only
def remove_uid(update, context):
    if len(context.args) < 1:
        update.message.reply_text("Usage: /remove <uid>")
        return
    uid = context.args[0]
    uids = load_json(UID_FILE, [])
    if uid not in uids:
        update.message.reply_text("❌ UID not found.")
        return
    uids.remove(uid)
    save_json(UID_FILE, uids)
    update.message.reply_text(f"✅ Removed UID {uid}")

@owner_only
def list_uids(update, context):
    uids = load_json(UID_FILE, [])
    if not uids:
        update.message.reply_text("No UIDs saved.")
        return
    update.message.reply_text("Saved UIDs:\n" + "\n".join(uids))

@owner_only
def allow_group(update, context):
    if len(context.args) < 1:
        update.message.reply_text("Usage: /allow <group_id>")
        return
    group_id = context.args[0]
    groups = load_json(GROUP_FILE, [])
    if group_id in groups:
        update.message.reply_text(f"✅ Group {group_id} already allowed.")
        return
    groups.append(group_id)
    save_json(GROUP_FILE, groups)
    update.message.reply_text(f"✅ Group {group_id} allowed.")

@owner_only
def check_bot(update, context):
    update.message.reply_text("✅ Bot is working currently.")

@owner_only
def type_uids(update, context):
    uids = load_json(UID_FILE, [])
    groups = load_json(GROUP_FILE, [])
    if not uids or not groups:
        update.message.reply_text("❌ No UIDs or allowed groups found.")
        return
    for uid in uids:
        text = f"/like ind {uid}"
        for group_id in groups:
            try:
                context.bot.send_message(chat_id=int(group_id), text=text)
                time.sleep(1)
            except Exception as e:
                print(f"Error sending {uid} to {group_id}: {e}")
    update.message.reply_text("✅ /type completed.")

@owner_only
def change_time(update, context):
    if len(context.args) < 2:
        update.message.reply_text('Usage: /time <hours> "<message>"')
        return
    try:
        hours = float(context.args[0])
        message = " ".join(context.args[1:]).strip('"')
    except:
        update.message.reply_text('❌ Invalid format.')
        return
    save_json(TIME_FILE, {"hours": hours, "message": message})
    update.message.reply_text(f"✅ Interval updated to {hours} hours with message: {message}")

# ---------------- Scheduler ----------------
def scheduled_task(bot):
    groups = load_json(GROUP_FILE, [])
    if not groups:
        return
    time_data = load_json(TIME_FILE, {"hours": DEFAULT_INTERVAL_HOURS, "message": DEFAULT_MESSAGE})
    message = time_data.get("message", DEFAULT_MESSAGE)
    for group_id in groups:
        try:
            bot.send_message(chat_id=int(group_id), text=message)
            print(f"{datetime.now()} → Sent scheduled message to {group_id}")
        except Exception as e:
            print(f"Error sending scheduled message to {group_id}: {e}")

# ---------------- Main ----------------
def main():
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Handlers
    dp.add_handler(CommandHandler("add", add_uid))
    dp.add_handler(CommandHandler("remove", remove_uid))
    dp.add_handler(CommandHandler("list", list_uids))
    dp.add_handler(CommandHandler("allow", allow_group))
    dp.add_handler(CommandHandler("check", check_bot))
    dp.add_handler(CommandHandler("type", type_uids))
    dp.add_handler(CommandHandler("time", change_time))

    # Scheduler
    scheduler = BackgroundScheduler()
    time_data = load_json(TIME_FILE, {"hours": DEFAULT_INTERVAL_HOURS, "message": DEFAULT_MESSAGE})
    scheduler.add_job(lambda: scheduled_task(updater.bot), "interval", hours=time_data["hours"])
    scheduler.start()

    print("🤖 Bot running on Python 3.13 (Free instance)...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
