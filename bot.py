import os
import logging
import requests
import json
import random
import re
import asyncio
import threading
from datetime import datetime
from flask import Flask

# ========== FLASK ==========
flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/health')
def health():
    return "✅ Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ========== TELEGRAM IMPORTS ==========
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ========== CONFIG ==========
BOT_TOKEN = "8685190437:AAEK8pmgDFwfS-CkfVTm3l1B_phegl5mkVM"
OWNER_ID = 8586849798
DEVELOPER = "@iflexvenom"
WELCOME_IMAGE = "https://i.ibb.co/rR2HG0CT/file-148.jpg"
USERS_FILE = "users.json"
BANNED_FILE = "banned.json"
OSINT_API = "https://pawan-osint.vercel.app/api?apikey=toxicadminn&number={}"

# ========== PREMIUM EMOJIS (TUNE JO DIYE THE - YE USE HO RAHE HAIN) ==========
PREMIUM_EMOJIS = {
    "verified": "✅", "flex": "😎", "blue_verification": "💎", "frozen": "❄️",
    "crying": "😭", "smiling": "🙂", "seeing_up": "😋", "teeth": "😁",
    "done": "👍", "blue_badge": "🟫", "black_badge": "🔸", "busy_tag": "🟧",
    "instagram": "🌐", "telegram": "🌐", "whatsapp": "🌐", "india": "🇮🇳",
    "dollar": "💵", "top": "🔝", "bro": "🤝", "yes": "👌", "lock": "🔓",
    "good": "👍", "sigma": "🥃", "don": "🍂", "skills": "💀", "heart": "❤️‍🔥",
    "stars": "⭐", "github": "📱", "motion": "💠"
}

EMOJI_LIST = list(PREMIUM_EMOJIS.values())  # [✅, 😎, 💎, ❄️, 😭, ...]

def random_emoji():
    return random.choice(EMOJI_LIST)

def format_with_emojis(text):
    """Har line ke AAGE aur PICCHE premium emoji (tune diye hue)"""
    lines = text.split('\n')
    result = []
    for line in lines:
        if line.strip():
            result.append(f"{random_emoji()} {line} {random_emoji()}")
        else:
            result.append("")
    return '\n'.join(result)

# ========== USER MANAGEMENT ==========
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def load_banned():
    if os.path.exists(BANNED_FILE):
        try:
            with open(BANNED_FILE, 'r') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_banned(banned_set):
    with open(BANNED_FILE, 'w') as f:
        json.dump(list(banned_set), f, indent=2)

def register_user(user_id, username, name):
    users = load_users()
    if str(user_id) not in users:
        users[str(user_id)] = {
            "id": user_id,
            "username": username or "NoUsername",
            "name": name,
            "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_users(users)
        print(f"✅ New user: {user_id}")

def is_banned(user_id):
    return str(user_id) in load_banned()

# ========== OSINT FUNCTION (Alternates + Map) ==========
def get_all_details(number, visited=None, depth=0):
    if visited is None:
        visited = set()
    if depth > 3:
        return [], []
    
    if str(number) in visited:
        return [], []
    visited.add(str(number))
    
    all_details = []
    all_addresses = []
    
    try:
        url = OSINT_API.format(number)
        response = requests.get(url, timeout=15)
        data = response.json()
        
        if data.get("success") and data.get("result", {}).get("results"):
            for rec in data["result"]["results"]:
                name = rec.get("name", "N/A")
                fname = rec.get("fname", "N/A")
                primary = rec.get("num", number)
                alt = rec.get("alt", None)
                aadhar = rec.get("aadhar", "N/A")
                email = rec.get("email", "N/A")
                circle = rec.get("circle", "N/A")
                address = rec.get("address", "")
                
                if address:
                    cleaned = address.replace("!", " ").replace("\n", " ")
                    all_addresses.append(cleaned)
                
                details = f"""═══════════════════════════
📱 NUMBER: +91{primary}
👤 NAME: {name}
👨 FATHER: {fname}
📞 ALTERNATE: {alt if alt else 'N/A'}
🆔 AADHAAR: {aadhar}
📧 EMAIL: {email}
📡 CIRCLE: {circle}
🏠 ADDRESS: {cleaned if address else 'N/A'}
═══════════════════════════"""
                all_details.append(details)
                
                # Alternate number mila to uski bhi details le
                if alt and alt != "N/A" and len(str(alt)) == 10 and str(alt) not in visited:
                    alt_details, alt_addrs = get_all_details(alt, visited, depth + 1)
                    all_details.extend(alt_details)
                    all_addresses.extend(alt_addrs)
    except Exception as e:
        pass
    
    return all_details, all_addresses

# ========== BOT COMMANDS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    register_user(user_id, username, first_name)
    
    if is_banned(user_id) and user_id != OWNER_ID:
        await update.message.reply_text("🚫 You are banned.")
        return
    
    caption = f"""WELCOME TO VENOM OSINT BOT

USER: {first_name}
ID: {user_id}
USERNAME: @{username if username else 'NoUsername'}

HOW TO USE:
➤ Send any 10-digit mobile number
➤ Bot will fetch all details
➤ Alternate numbers ki bhi details milegi
➤ Address with Google Map

OWNER COMMANDS:
/owner - Admin panel
/users - List all users
/ban <id> - Ban user
/unban <id> - Unban user
/broadcast <msg> - Broadcast

Developer: {DEVELOPER}"""
    
    caption = format_with_emojis(caption)  # Premium emoji lagega har line pe
    
    try:
        await update.message.reply_photo(photo=WELCOME_IMAGE, caption=caption, parse_mode="HTML")
    except Exception as e:
        print(f"Image error: {e}")
        await update.message.reply_text(caption, parse_mode="HTML")

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg_text = update.message.text.strip()
    
    register_user(user_id, update.effective_user.username, update.effective_user.first_name)
    
    if is_banned(user_id) and user_id != OWNER_ID:
        await update.message.reply_text("🚫 You are banned.")
        return
    
    number = re.sub(r'\D', '', msg_text)
    if len(number) != 10:
        await update.message.reply_text(f"{random_emoji()} Send valid 10-digit mobile number")
        return
    
    status_msg = await update.message.reply_text(f"{random_emoji()} Fetching details for +91{number}...")
    
    all_details, all_addresses = get_all_details(number)
    
    if not all_details:
        await status_msg.edit_text(f"{random_emoji()} No data found for +91{number}")
        return
    
    final_output = "\n".join(all_details)
    
    if len(final_output) > 4000:
        parts = [final_output[i:i+4000] for i in range(0, len(final_output), 4000)]
        await status_msg.delete()
        for part in parts:
            await update.message.reply_text(part, parse_mode="HTML")
            await asyncio.sleep(0.3)
    else:
        await status_msg.edit_text(final_output, parse_mode="HTML")
    
    # Map bhejna
    sent = set()
    for addr in all_addresses:
        if addr and len(addr) > 5 and addr not in sent:
            sent.add(addr)
            map_url = f"https://www.google.com/maps?q={addr.replace(' ', '+')}"
            map_msg = f"📍 LOCATION MAP:\n{addr}\n{map_url}"
            await update.message.reply_text(map_msg, parse_mode="HTML")
            await asyncio.sleep(0.5)

async def owner_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Access Denied! Only owner.")
        return
    
    users = load_users()
    banned = load_banned()
    
    text = f"""OWNER PANEL

📊 STATISTICS
• Total Users: {len(users)}
• Banned Users: {len(banned)}
• Active: {len(users) - len(banned)}

📌 COMMANDS
/users - List all users
/ban <user_id> - Ban user
/unban <user_id> - Unban user
/broadcast <message> - Broadcast

Developer: {DEVELOPER}"""
    
    text = format_with_emojis(text)
    await update.message.reply_text(text, parse_mode="HTML")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Access Denied!")
        return
    
    users = load_users()
    banned = load_banned()
    
    if not users:
        await update.message.reply_text("No users found.")
        return
    
    msg = "USERS LIST\n\n"
    for uid, data in users.items():
        status = "BANNED" if uid in banned else "ACTIVE"
        msg += f"ID: {uid} | @{data.get('username', 'N/A')} | {data.get('name', 'N/A')} | {status}\n"
    
    msg += f"\nTotal: {len(users)} users"
    msg = format_with_emojis(msg)
    
    if len(msg) > 4000:
        await update.message.reply_text(f"Total users: {len(users)}\nUse /owner for stats")
    else:
        await update.message.reply_text(msg, parse_mode="HTML")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Access Denied!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /ban <user_id>")
        return
    
    target = str(context.args[0])
    if target == str(OWNER_ID):
        await update.message.reply_text("❌ Cannot ban owner!")
        return
    
    banned = load_banned()
    banned.add(target)
    save_banned(banned)
    
    msg = format_with_emojis(f"✅ User {target} has been banned.")
    await update.message.reply_text(msg, parse_mode="HTML")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Access Denied!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /unban <user_id>")
        return
    
    target = str(context.args[0])
    banned = load_banned()
    
    if target in banned:
        banned.remove(target)
        save_banned(banned)
        msg = format_with_emojis(f"✅ User {target} has been unbanned.")
        await update.message.reply_text(msg, parse_mode="HTML")
    else:
        await update.message.reply_text(f"User {target} is not banned.")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Access Denied!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    
    msg = ' '.join(context.args)
    users = load_users()
    
    formatted_msg = format_with_emojis(f"📢 BROADCAST\n\n{msg}\n\n- Admin")
    
    sent = 0
    for uid in users.keys():
        try:
            await context.bot.send_message(chat_id=int(uid), text=formatted_msg, parse_mode="HTML")
            sent += 1
            await asyncio.sleep(0.05)
        except:
            pass
    
    await update.message.reply_text(f"✅ Broadcast sent to {sent} users.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""VENOM OSINT BOT

COMMANDS:
/start - Start bot
/help - Show help
/owner - Owner panel (owner only)

HOW TO USE:
Send any 10-digit Indian mobile number

Developer: {DEVELOPER}"""
    
    text = format_with_emojis(text)
    await update.message.reply_text(text, parse_mode="HTML")

# ========== MAIN ==========
def main():
    logging.basicConfig(level=logging.INFO)
    
    if not os.path.exists(USERS_FILE):
        save_users({})
    if not os.path.exists(BANNED_FILE):
        save_banned(set())
    
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
        print("✅ Webhook deleted")
    except:
        pass
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("owner", owner_panel))
    app.add_handler(CommandHandler("users", list_users))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))
    
    print("=" * 50)
    print("🤖 VENOM OSINT BOT STARTED")
    print(f"👑 Owner ID: {OWNER_ID}")
    print("✅ Tere diye hue premium emojis use ho rahe hain")
    print("=" * 50)
    
    threading.Thread(target=run_flask, daemon=True).start()
    
    app.run_polling(poll_interval=1.0, timeout=30)

if __name__ == "__main__":
    main()
