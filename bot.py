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

# ========== IMPORTS ==========
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

# ========== EMOJIS ==========
EMOJI_LIST = ["✅", "😎", "💎", "❄️", "😭", "🙂", "😋", "😁", "👍", "🟫", "🔸", "🟧", "🌐", "🇮🇳", "💵", "🔝", "🤝", "👌", "🔓", "🥃", "🍂", "💀", "❤️‍🔥", "⭐", "📱", "💠"]

def random_emoji():
    return random.choice(EMOJI_LIST)

def format_line(text):
    """Har line ke aage aur piche emoji"""
    return f"{random_emoji()} {text} {random_emoji()}"

def format_with_emojis(text):
    lines = text.split('\n')
    result = []
    for line in lines:
        if line.strip():
            result.append(format_line(line))
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
        logging.info(f"New user: {user_id}")

def is_banned(user_id):
    return str(user_id) in load_banned()

# ========== OSINT FUNCTION ==========
def get_osint_details(number):
    try:
        url = OSINT_API.format(number)
        response = requests.get(url, timeout=15)
        data = response.json()
        
        if data.get("success") and data.get("result", {}).get("results"):
            records = data["result"]["results"]
            all_details = []
            all_addresses = []
            all_alternates = []
            
            for rec in records:
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
                
                if alt and alt != "N/A" and len(str(alt)) >= 10:
                    all_alternates.append(str(alt))
                
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
            
            # Alternate numbers ki details
            for alt_num in all_alternates:
                alt_url = OSINT_API.format(alt_num)
                alt_resp = requests.get(alt_url, timeout=15)
                alt_data = alt_resp.json()
                if alt_data.get("success") and alt_data.get("result", {}).get("results"):
                    for alt_rec in alt_data["result"]["results"]:
                        alt_name = alt_rec.get("name", "N/A")
                        alt_fname = alt_rec.get("fname", "N/A")
                        alt_aadhar = alt_rec.get("aadhar", "N/A")
                        alt_email = alt_rec.get("email", "N/A")
                        alt_circle = alt_rec.get("circle", "N/A")
                        alt_address = alt_rec.get("address", "")
                        
                        if alt_address:
                            alt_cleaned = alt_address.replace("!", " ").replace("\n", " ")
                            all_addresses.append(alt_cleaned)
                        
                        alt_details = f"""

🔄 ALTERNATE NUMBER: +91{alt_num}
👤 NAME: {alt_name}
👨 FATHER: {alt_fname}
🆔 AADHAAR: {alt_aadhar}
📧 EMAIL: {alt_email}
📡 CIRCLE: {alt_circle}
🏠 ADDRESS: {alt_cleaned if alt_address else 'N/A'}
═══════════════════════════"""
                        all_details.append(alt_details)
            
            return "\n".join(all_details), all_addresses
        else:
            return f"❌ No data found for +91{number}", []
    except Exception as e:
        return f"⚠️ Error: {str(e)}", []

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
➤ Address will show location on map

OWNER COMMANDS:
/owner - Admin panel
/users - Total users
/ban <id> - Ban user
/unban <id> - Unban user
/broadcast <msg> - Send to all

Developer: {DEVELOPER}"""
    
    caption = format_with_emojis(caption)
    
    try:
        await update.message.reply_photo(photo=WELCOME_IMAGE, caption=caption, parse_mode="HTML")
    except:
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
        await update.message.reply_text("❌ Send a valid 10-digit mobile number.")
        return
    
    status_msg = await update.message.reply_text(f"{random_emoji()} Fetching details for +91{number}...")
    
    details, addresses = get_osint_details(number)
    
    # Details without emoji on each line
    await status_msg.edit_text(details, parse_mode="HTML")
    
    # Send maps
    for addr in addresses:
        if addr and len(addr) > 5:
            map_url = f"https://www.google.com/maps?q={addr.replace(' ', '+')}"
            await update.message.reply_text(f"📍 LOCATION MAP:\n{addr}\n{map_url}")
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
    
    # Create files if not exist
    if not os.path.exists(USERS_FILE):
        save_users({})
    if not os.path.exists(BANNED_FILE):
        save_banned(set())
    
    # Delete webhook
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
        print("✅ Webhook deleted")
    except:
        pass
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
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
    print("=" * 50)
    
    # Start Flask for Render
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Start polling
    app.run_polling(poll_interval=1.0, timeout=30)

if __name__ == "__main__":
    main()
