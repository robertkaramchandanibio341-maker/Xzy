import os
import sys
import logging
import requests
import json
import random
import re
import asyncio
from datetime import datetime
from flask import Flask

# Flask app for health check
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# Bot token - YAHAN APNA TOKEN DAAL
BOT_TOKEN = "8685190437:AAEK8pmgDFwfS-CkfVTm3l1B_phegl5mkVM"

# Import telegram AFTER flask (avoid issues)
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging
logging.basicConfig(level=logging.INFO)

# Emojis
EMOJIS = ["✅", "😎", "💎", "❄️", "😭", "👍", "⭐", "🔥", "💀", "❤️"]

def random_emoji():
    return random.choice(EMOJIS)

def format_line(text):
    return f"{random_emoji()} {text} {random_emoji()}"

# OSINT API
def get_osint(number):
    try:
        url = f"https://pawan-osint.vercel.app/api?apikey=toxicadminn&number={number}"
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get("success") and data.get("result", {}).get("results"):
            rec = data["result"]["results"][0]
            name = rec.get("name", "N/A")
            fname = rec.get("fname", "N/A")
            alt = rec.get("alt", "N/A")
            aadhar = rec.get("aadhar", "N/A")
            email = rec.get("email", "N/A")
            circle = rec.get("circle", "N/A")
            address = rec.get("address", "").replace("!", " ")
            return f"""📱 NUMBER: +91{number}
👤 NAME: {name}
👨 FATHER: {fname}
📞 ALTERNATE: {alt}
🆔 AADHAAR: {aadhar}
📧 EMAIL: {email}
📡 CIRCLE: {circle}
🏠 ADDRESS: {address}""", address
        return f"❌ No data for +91{number}", ""
    except Exception as e:
        return f"⚠️ Error: {e}", ""

# Bot commands
async def start(update, context):
    user = update.effective_user
    msg = f"""WELCOME TO VENOM OSINT BOT

USER: {user.first_name}
ID: {user.id}

HOW TO USE:
Send any 10-digit mobile number

OWNER COMMANDS:
/owner - Admin panel
/users - List users
/ban <id> - Ban user
/unban <id> - Unban user

Developer: @iflexvenom"""
    
    lines = msg.split('\n')
    formatted = '\n'.join([format_line(l) if l.strip() else "" for l in lines])
    await update.message.reply_text(formatted)

async def handle_number(update, context):
    number = re.sub(r'\D', '', update.message.text.strip())
    if len(number) != 10:
        await update.message.reply_text("❌ Send valid 10-digit number")
        return
    
    await update.message.reply_text(f"{random_emoji()} Fetching +91{number}...")
    
    details, address = get_osint(number)
    
    # Send details without emoji on each line
    await update.message.reply_text(details)
    
    if address and len(address) > 5:
        map_url = f"https://www.google.com/maps?q={address.replace(' ', '+')}"
        await update.message.reply_text(f"📍 MAP:\n{address}\n{map_url}")

async def owner(update, context):
    if update.effective_user.id != 8586849798:
        await update.message.reply_text("❌ Access Denied")
        return
    await update.message.reply_text("👑 Owner Panel\n\n/users - List users\n/ban <id>\n/unban <id>")

async def users_cmd(update, context):
    if update.effective_user.id != 8586849798:
        await update.message.reply_text("❌ Access Denied")
        return
    await update.message.reply_text("Users list feature - working")

async def ban(update, context):
    if update.effective_user.id != 8586849798:
        await update.message.reply_text("❌ Access Denied")
        return
    await update.message.reply_text("Ban feature working")

async def unban(update, context):
    if update.effective_user.id != 8586849798:
        await update.message.reply_text("❌ Access Denied")
        return
    await update.message.reply_text("Unban feature working")

# Main function
def main():
    print("Starting bot...")
    
    # Delete webhook
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
        print("Webhook deleted")
    except:
        pass
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("owner", owner))
    application.add_handler(CommandHandler("users", users_cmd))
    application.add_handler(CommandHandler("ban", ban))
    application.add_handler(CommandHandler("unban", unban))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))
    
    print("Bot is running...")
    
    # Start polling
    application.run_polling()

if __name__ == "__main__":
    # Start Flask in background thread
    import threading
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Run bot
    main()
