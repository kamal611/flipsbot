
# 💥 SUPER FLIPS BOT (Facebook + OfferUp + Craigslist)
# Один Telegram токен, один чат, три источника
# Запускается каждые 1–2 минуты через schedule
# Готов к запуску на Render / VPS

import time
import os
import re
import requests
import schedule
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from telegram import Bot

TELEGRAM_TOKEN = '8199786673:AAH9rM4L-enn0TCMZXeTaMqNEfEeJx3MDSs'
CHAT_ID = '6853246366'
CHROME_DRIVER_PATH = './chromedriver.exe'
SEEN_OFFERUP = 'seen_offerup.txt'
SEEN_CRAIGSLIST = set()
SEEN_FB = set()

HEADERS = {'User-Agent': 'Mozilla/5.0'}

# -------------------- Facebook --------------------
FACEBOOK_URL = 'https://www.facebook.com/marketplace/sandiego/vehicles?sellerType=individual&exact=false'

def check_facebook():
    print("🌐 Проверка Facebook...")
    chrome_options = Options()
    chrome_options.add_argument("--user-data-dir=selenium_profile")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless=new")

    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(FACEBOOK_URL)
    time.sleep(15)

    bot = Bot(token=TELEGRAM_TOKEN)

    try:
        posts = driver.find_elements(By.XPATH, '//a[contains(@href, "/marketplace/item/")]')
        print(f"🔎 Найдено на Facebook: {len(posts)}")
        for post in posts[:5]:
            title = post.text.split("\n")[0]
            url = post.get_attribute("href")
            if url not in SEEN_FB:
                SEEN_FB.add(url)
                message = f"🚗 {title}\n{url}"
                bot.send_message(chat_id=CHAT_ID, text=message)
                print(f"✅ Facebook отправлено: {title}")
    except Exception as e:
        print("❌ FB ошибка:", e)
    driver.quit()

# -------------------- OfferUp --------------------
OFFERUP_URLS = [
    'https://offerup.com/explore/sck/ca/san_diego/cars-trucks',
    'https://offerup.com/explore/sck/ca/el_cajon/cars-trucks',
    'https://offerup.com/explore/sck/ca/oceanside/cars-trucks'
]

def load_seen_offerup():
    if not os.path.exists(SEEN_OFFERUP):
        return set()
    with open(SEEN_OFFERUP, 'r') as f:
        return set(line.strip() for line in f.readlines())

def save_offerup_url(url):
    with open(SEEN_OFFERUP, 'a') as f:
        f.write(url + '\n')

def check_offerup():
    print("🌐 Проверка OfferUp...")
    seen = load_seen_offerup()
    bot = Bot(token=TELEGRAM_TOKEN)
    for url in OFFERUP_URLS:
        try:
            response = requests.get(url, headers=HEADERS)
            soup = BeautifulSoup(response.text, 'html.parser')
            cards = soup.select('a[href^="/item/detail/"]')
            for card in cards:
                link = "https://offerup.com" + card['href'].split('?')[0]
                title = card.get('title') or 'Объявление'
                if link not in seen:
                    seen.add(link)
                    save_offerup_url(link)
                    bot.send_message(chat_id=CHAT_ID, text=f"🚘 {title}\n{link}")
                    print(f"✅ OfferUp отправлено: {title}")
                    break
        except Exception as e:
            print("❌ OfferUp ошибка:", e)

# -------------------- Craigslist --------------------
CRAIGSLIST_URL = 'https://sandiego.craigslist.org/search/cta?postal=92122&purveyor=owner&search_distance=100'

def check_craigslist():
    print("🌐 Проверка Craigslist...")
    try:
        res = requests.get(CRAIGSLIST_URL, headers=HEADERS)
        soup = BeautifulSoup(res.text, 'html.parser')
        posts = soup.select('.result-info')
        print(f"🔎 Найдено Craigslist: {len(posts)}")
        bot = Bot(token=TELEGRAM_TOKEN)
        for post in posts[:5]:
            title = post.select_one('.result-title').text.strip()
            url = post.select_one('.result-title')['href']
            price_tag = post.select_one('.result-price')
            price = price_tag.text.strip() if price_tag else 'No price'
            if url not in SEEN_CRAIGSLIST:
                SEEN_CRAIGSLIST.add(url)
                text = f"{title} - {price}\n{url}"
                bot.send_message(chat_id=CHAT_ID, text=text)
                print(f"✅ Craigslist отправлено: {title}")
    except Exception as e:
        print("❌ Craigslist ошибка:", e)

# -------------------- Расписание --------------------
schedule.every(2).minutes.do(check_facebook)
schedule.every(3).minutes.do(check_offerup)
schedule.every(4).minutes.do(check_craigslist)

print("🤖 SUPER FLIPS BOT запущен!")

if __name__ == "__main__":
    check_facebook()
    check_offerup()
    check_craigslist()
    while True:
        schedule.run_pending()
        time.sleep(15)
