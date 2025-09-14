# -*- coding: utf-8 -*-
# DarkWarHelperBot Replit Free Plan Uyumluluğu
# Telegram kullanıcı: firatguler10
# Bot adı: @DarkWarHelperBot
# Token: 8434901027:AAFRxlCplNqFK4dpdLvf5VSEhPV_vvtNDd4

import logging, sqlite3, os, threading, time, requests
from telegram.ext import Updater, CommandHandler
from datetime import time as dt_time
from flask import Flask
from threading import Thread

# -----------------------------
# Keep-alive için Flask sunucusu
# -----------------------------
app = Flask('')

@app.route('/')
def home():
    return "Bot uyanık!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    server = Thread(target=run)
    server.start()
    while True:
        try:
            url = "https://darkwarhelperbot.firatguler10.repl.co/"  # Buraya kendi Replit URL'ini yaz
            requests.get(url)
        except:
            pass
        time.sleep(5*60)  # 5 dakikada bir ping

# -----------------------------
# Bot Token ve Logging
# -----------------------------
TOKEN = "8434901027:AAFRxlCplNqFK4dpdLvf5VSEhPV_vvtNDd4"
logging.basicConfig(level=logging.INFO)

# -----------------------------
# Dil ve mesajlar
# -----------------------------
diller = ["tr","en"]
mesajlar = {
    "tr":{"start":"Merhaba! Ben senin Dark War Survival botunum.\n/gorevler, /ekle, /sil, /hatirlat, /dil","no_tasks":"📭 Henüz görev yok.","tasks":"📋 Günlük Görevler:","added":"✅ Görev eklendi: ","deleted":"🗑️ Silindi: ","invalid_number":"⚠️ Geçersiz görev numarası.","reminder":"⏰ Görev zamanı! /gorevler yazabilirsin.","reminder_set":"✅ Her gün {saat}:{dakika}'da hatırlatma kuruldu.","reminder_invalid":"⚠️ Geçersiz saat formatı. Örn: 09:30","lang_set":"✅ Dil Türkçe olarak ayarlandı."},
    "en":{"start":"Hello! I am your Dark War Survival bot.\n/gorevler, /ekle, /sil, /hatirlat, /dil","no_tasks":"📭 No tasks yet.","tasks":"📋 Daily Tasks:","added":"✅ Task added: ","deleted":"🗑️ Deleted: ","invalid_number":"⚠️ Invalid task number.","reminder":"⏰ Task time! /gorevler","reminder_set":"✅ Daily reminder set at {saat}:{dakika}.","reminder_invalid":"⚠️ Invalid time format. Example: 09:30","lang_set":"✅ Language set to English."}
}

# -----------------------------
# Veritabanı
# -----------------------------
DB_PATH = os.path.join(os.path.expanduser("~"), "darkwarhelper_bot.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS users(chat_id INTEGER PRIMARY KEY, lang TEXT)""")
cursor.execute("""CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER, lang TEXT, task TEXT)""")
conn.commit()

def get_lang(chat_id):
    cursor.execute("SELECT lang FROM users WHERE chat_id=?", (chat_id,))
    row = cursor.fetchone()
    return row[0] if row else "tr"

# -----------------------------
# Komutlar
# -----------------------------
def start(update, context):
    chat_id = update.message.chat_id
    user_lang = getattr(update.effective_user,"language_code","en")[:2]
    if user_lang not in diller: user_lang="en"
    cursor.execute("INSERT OR IGNORE INTO users(chat_id,lang) VALUES(?,?)",(chat_id,user_lang))
    conn.commit()
    update.message.reply_text(mesajlar[user_lang]["start"])

def liste(update, context):
    chat_id = update.message.chat_id
    lang = get_lang(chat_id)
    cursor.execute("SELECT task FROM tasks WHERE chat_id=? AND lang=? ORDER BY id",(chat_id,lang))
    rows = cursor.fetchall()
    if not rows: update.message.reply_text(mesajlar[lang]["no_tasks"]); return
    mesaj = mesajlar[lang]["tasks"]+"\n"+ "\n".join(["{}. {}".format(i+1,row[0]) for i,row in enumerate(rows)])
    update.message.reply_text(mesaj)

def ekle(update, context):
    chat_id = update.message.chat_id
    lang = get_lang(chat_id)
    if not context.args: update.message.reply_text("❗ /ekle [metin] kullan"); return
    yeni_gorev = " ".join(context.args)
    cursor.execute("INSERT INTO tasks(chat_id,lang,task) VALUES(?,?,?)",(chat_id,lang,yeni_gorev))
    conn.commit()
    update.message.reply_text(mesajlar[lang]["added"]+yeni_gorev)

def sil(update, context):
    chat_id = update.message.chat_id
    lang = get_lang(chat_id)
    if not context.args or not context.args[0].isdigit(): update.message.reply_text("❗ /sil [numara] kullan"); return
    index = int(context.args[0])-1
    cursor.execute("SELECT id, task FROM tasks WHERE chat_id=? AND lang=? ORDER BY id",(chat_id,lang))
    rows = cursor.fetchall()
    if 0<=index<len(rows):
        task_id = rows[index][0]; task_text=rows[index][1]
        cursor.execute("DELETE FROM tasks WHERE id=?",(task_id,))
        conn.commit()
        update.message.reply_text(mesajlar[lang]["deleted"]+task_text)
    else: update.message.reply_text(mesajlar[lang]["invalid_number"])

def hatirlat(context):
    chat_id = context.job.context
    lang = get_lang(chat_id)
    context.bot.send_message(chat_id=chat_id,text=mesajlar[lang]["reminder"])

def daily_reminder(update, context):
    chat_id = update.message.chat_id
    lang = get_lang(chat_id)
    if not context.args: update.message.reply_text("❗ /hatirlat [saat] kullan (örn: /hatirlat 21:00)"); return
    try:
        saat,dakika = map(int, context.args[0].split(":"))
        context.job_queue.run_daily(hatirlat,time=dt_time(hour=saat,minute=dakika),context=chat_id)
        update.message.reply_text(mesajlar[lang]["reminder_set"].format(saat="{:02d}".format(saat),dakika="{:02d}".format(dakika)))
    except: update.message.reply_text(mesajlar[lang]["reminder_invalid"])

def dil(update, context):
    chat_id = update.message.chat_id
    if not context.args: update.message.reply_text("❗ /dil tr | en"); return
    secim = context.args[0].lower()
    if secim in diller:
        cursor.execute("INSERT OR REPLACE INTO users(chat_id,lang) VALUES(?,?)",(chat_id,secim))
        conn.commit()
        update.message.reply_text(mesajlar[secim]["lang_set"])
    else: update.message.reply_text("⚠️ Geçersiz seçim. Kullan: tr / en")

# -----------------------------
# Ana Fonksiyon
# -----------------------------
def main():
    updater = Updater(TOKEN,use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start",start))
    dp.add_handler(CommandHandler("gorevler",liste))
    dp.add_handler(CommandHandler("ekle",ekle))
    dp.add_handler(CommandHandler("sil",sil))
    dp.add_handler(CommandHandler("hatirlat",daily_reminder))
    dp.add_handler(CommandHandler("dil",dil))
    t = threading.Thread(target=keep_alive)
    t.start()
    updater.start_polling()
    updater.idle()

if __name__=="__main__":
    main()
