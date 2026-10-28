import telebot
from telebot import types
import yt_dlp
import os
import glob
import time
import threading
import uuid
import shutil
from flask import Flask

BOT_TOKEN = "9245738723:AAHO8pZ6zHeiapBJNrDfykk1qHgRTfGkjKo"
bot = telebot.TeleBot(BOT_TOKEN)
CHANNEL_USERNAME = "@l_max19"
DOWNLOAD_DIR = "/tmp/downloads"
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

app = Flask('')
@app.route('/')
def home(): return "Bot is alive!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive(): threading.Thread(target=run).start()

def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['member', 'administrator', 'creator']: return True
    except: pass
    return False

def download_and_send(chat_id, query, reply_to_message_id=None):
    task_id = str(uuid.uuid4())
    task_dir = os.path.join(DOWNLOAD_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)
    try:
        status_msg = bot.send_message(chat_id, "⏳ جاري التحميل...", reply_to_message_id=reply_to_message_id)
    except: return 
    
    url = query if "youtube.com" in query or "youtu.be" in query else f"ytsearch1:{query}"
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': os.path.join(task_dir, '%(id)s.%(ext)s'),
        'writethumbnail': True, 'nopart': True, 'quiet': True,
        'concurrent_fragment_downloads': 16,
        'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Audio')
        files = glob.glob(os.path.join(task_dir, "*"))
        media_files = [f for f in files if not f.endswith(('.jpg', '.jpeg', '.webp', '.png'))]
        if media_files:
            file_path = max(media_files, key=os.path.getsize)
            thumb_path = next((f for f in files if f.endswith(('.jpg', '.jpeg', '.webp', '.png'))), None)
            with open(file_path, 'rb') as audio:
                kwargs = {'title': title, 'performer': "@kg_22bot", 'caption': f"🎵 **{title}**", 'parse_mode': "Markdown"}
                if thumb_path: kwargs['thumb'] = open(thumb_path, 'rb')
                if reply_to_message_id: kwargs['reply_to_message_id'] = reply_to_message_id
                bot.send_audio(chat_id, audio, **kwargs)
            bot.delete_message(chat_id, status_msg.message_id)
        else:
            bot.edit_message_text("❌ لم يتم العثور على ملف.", chat_id, status_msg.message_id)
    except Exception as e:
        try: bot.edit_message_text(f"❌ خطأ.", chat_id, status_msg.message_id)
        except: pass
    finally: shutil.rmtree(task_dir, ignore_errors=True)

@bot.message_handler(commands=['start'])
def start(message): bot.reply_to(message, "أهلاً بك! 🎵\nأرسل اسم الأغنية.")

@bot.message_handler(func=lambda message: message.text and not message.text.startswith('/'))
def handle_message(message):
    if not check_subscription(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 اشترك أولاً", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"))
        bot.reply_to(message, "⚠️ **اشترك في القناة أولاً.**", reply_markup=markup, parse_mode="Markdown")
        return
    threading.Thread(target=download_and_send, args=(message.chat.id, message.text, message.message_id)).start()

if __name__ == "__main__":
    keep_alive()
    print("Bot Running...")
    while True:
        try: bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except: time.sleep(5)
