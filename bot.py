import feedparser
import requests
import schedule
import time
import json
import traceback
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from newspaper import Article
from flask import Flask
from threading import Thread
from datetime import datetime

# ================== ضع بياناتك هنا ==================
TELEGRAM_TOKEN = "8651602237:AAF-YUYTpPoi9QGPGN9iRgT5dkRKABYMkAU"
CHAT_ID = "@Aaldjsuheheisu81872"
# =====================================================

# ================== تشغيل سيرفر لمنع Sleep ==================
app = Flask(__name__)

@app.route('/')
def home():
    return "News Bot Running 24/7"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
# =============================================================

RSS_FEEDS = {
    "TehranTimes": "https://www.tehrantimes.com/rss",
    "IRNA": "https://en.irna.ir/rss",
    "JerusalemPost": "https://www.jpost.com/rss/rssfeedsfrontpage.aspx",
    "TimesOfIsrael": "https://www.timesofisrael.com/feed/",
    "Reuters": "https://feeds.reuters.com/reuters/worldNews",
    "CNN": "http://rss.cnn.com/rss/edition_world.rss",
    "AlJazeera": "https://www.aljazeera.net/aljazeerarss.xml",
    "AlArabiya": "https://www.alarabiya.net/.mrss/ar.xml"
}

KEYWORDS = [
    "Iran","Israel","USA","America",
    "Tehran","Washington","Gaza",
    "missile","war","sanctions","IDF"
]

FILE_NAME = "sent_links.json"

try:
    with open(FILE_NAME, "r") as f:
        sent_links = set(json.load(f))
except:
    sent_links = set()

def save_links():
    with open(FILE_NAME, "w") as f:
        json.dump(list(sent_links), f)

def translate(text):
    try:
        return GoogleTranslator(source='auto', target='ar').translate(text)
    except:
        return text

def classify(text):
    t = text.lower()
    if any(w in t for w in ["missile","war","army","idf","attack"]):
        return "🪖 عسكري"
    if any(w in t for w in ["sanction","oil","economy","market"]):
        return "💰 اقتصادي"
    if any(w in t for w in ["president","minister","government","election"]):
        return "🏛 سياسي"
    return "🌍 عام"

def risk(text):
    if any(w in text.lower() for w in ["war","explosion","missile","attack"]):
        return "🚨 عالي الخطورة"
    return "🟢 عادي"

def fetch_full_article(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text, article.top_image
    except:
        return "", None

def send_telegram(message, image=None):
    try:
        if image:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            data = {
                "chat_id": CHAT_ID,
                "caption": message,
                "parse_mode": "HTML",
                "photo": image
            }
        else:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            data = {
                "chat_id": CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }
        requests.post(url, data=data)
    except:
        pass

def check_news():
    print("🔎 فحص:", datetime.now())

    for source, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)

        for entry in feed.entries[:5]:
            link = entry.link
            if link in sent_links:
                continue

            full_text, image = fetch_full_article(link)
            if not full_text:
                continue

            if any(k.lower() in full_text.lower() for k in KEYWORDS):

                title_ar = translate(entry.title)
                body_ar = translate(full_text[:1200])

                category = classify(full_text)
                risk_level = risk(full_text)

                message = f"""
🔥 <b>وكالة الأخبار</b>

📍 المصدر: {source}
{category} | {risk_level}

📰 <b>{title_ar}</b>

📌 {body_ar[:800]}...

🔗 المصدر:
{link}
                """

                send_telegram(message, image)
                sent_links.add(link)
                save_links()
                print("✅ تم الإرسال:", title_ar)

# ✅ فحص كل 20 ثانية شبه لحظي
schedule.every(20).seconds.do(check_news)

print("🚀 البوت يعمل 24/7")

while True:
    try:
        schedule.run_pending()
        time.sleep(5)
    except Exception as e:
        print("Error:", e)
        traceback.print_exc()
        time.sleep(10)
