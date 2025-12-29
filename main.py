import os
import telebot
import requests
from telebot import types
from flask import Flask
import threading

# --- SETUP ---
# We get the token from Render's "Environment Variables" later
BOT_TOKEN = os.environ.get('BOT_TOKEN') 
bot = telebot.TeleBot(BOT_TOKEN)
API_URL = "https://www.1secmail.com/api/v1/"

# --- FAKE WEBSITE (To keep Render happy) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web_server():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# --- BOT LOGIC ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    btn_gen = types.InlineKeyboardButton("Generate Email 📧", callback_data='generate')
    markup.add(btn_gen)
    bot.reply_to(message, "Hello! Click below to get a temporary email.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'generate')
def generate_email(call):
    response = requests.get(f"{API_URL}?action=genRandomMailbox&count=1")
    if response.status_code == 200:
        email = response.json()[0]
        login, domain = email.split('@')
        markup = types.InlineKeyboardMarkup()
        btn_check = types.InlineKeyboardButton("Check Inbox 📩", callback_data=f"check|{login}|{domain}")
        markup.add(btn_check)
        bot.send_message(call.message.chat.id, f"Your Temp Mail:\n`{email}`", parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('check'))
def check_inbox(call):
    _, login, domain = call.data.split('|')
    response = requests.get(f"{API_URL}?action=getMessages&login={login}&domain={domain}")
    if response.status_code == 200:
        messages = response.json()
        if not messages:
            bot.answer_callback_query(call.id, "Inbox is empty! 📭")
            return
        for msg in messages:
            msg_id = msg['id']
            full_msg = requests.get(f"{API_URL}?action=readMessage&login={login}&domain={domain}&id={msg_id}").json()
            bot.send_message(call.message.chat.id, f"📩 **From:** {full_msg['from']}\n**Subject:** {full_msg['subject']}\n\n{full_msg.get('textBody', 'No text')}", parse_mode='Markdown')

# --- START EVERYTHING ---
if __name__ == "__main__":
    # Start the web server in a separate thread
    t = threading.Thread(target=run_web_server)
    t.start()
    # Start the bot
    bot.infinity_polling()
  
