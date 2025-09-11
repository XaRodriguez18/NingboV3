import pandas as pd
from datetime import datetime
import discord
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import time as dtime
from dotenv import load_dotenv
import os
import pytz
from scraper.scraper import run_scraper

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
LOCAL_TZ = os.getenv("LOCAL_TZ")
SEND_HOUR = int(os.getenv("SEND_HOUR"))
SEND_MIN = int(os.getenv("SEND_MIN"))

def get_daily_news():
    # Get today's date string for the CSV filename
    today_str = datetime.now().strftime("%Y-%m-%d")
    file_string = today_str + '_news.csv'
    news_dir = os.path.abspath("news")
    news_path = os.path.join(news_dir, file_string)
    print(f"[INFO] Absolute news directory: {news_dir}")
    print(f"[INFO] Loading news from: {news_path}")
    if not os.path.exists(news_path):
        print("[WARN] News file not found for today.")
        return "No news data available for today."
    print("[INFO] News file found, reading CSV...")
    news = pd.read_csv(news_path)

    # Filter countries (United States)
    country = ['USD']
    mask = news['currency'].isin(country)
    news = news[mask]
    # Filter impact (Red and Orange)
    impact = ['red', 'orange']
    mask = news['impact'].isin(impact)
    news = news[mask]

    # Get today's date for display
    today_display = datetime.now().strftime("%b %d")
    mask = news['date'] == today_display
    current_day_rows = news[mask]

    # Generate news message to be displayed
    message_list = ['time', 'currency', 'impact', 'event']
    news_message = f"{today_display} News:\n"
    if current_day_rows.empty:
        news_message += "No relevant news today"
    else:
        for index, row in current_day_rows.iterrows():
            for name in message_list:
                news_message += str(row[name]) + "\t"
            news_message += "\n"
    print(f"[INFO] Current message:\n{news_message}")
    return news_message

def convert_to_utc(hour: int, minute: int, local_tz_str: str = LOCAL_TZ) -> tuple:
    print(f"[INFO] Converting local time {hour}:{minute} in {local_tz_str} to UTC...")
    local_tz = pytz.timezone(local_tz_str)
    now = datetime.now(local_tz)
    local_dt = local_tz.localize(datetime(now.year, now.month, now.day, hour, minute))
    utc_dt = local_dt.astimezone(pytz.utc)
    print(f"[INFO] UTC time is {utc_dt.hour}:{utc_dt.minute}")
    return utc_dt.hour, utc_dt.minute

utc_hour, utc_minute = convert_to_utc(SEND_HOUR, SEND_MIN, LOCAL_TZ)

# Set the time you want the message to be sent (24-hour format)
SEND_TIME = dtime(hour=utc_hour, minute=utc_minute)
# SEND_TIME = dtime(hour=12, minute=41)

@bot.event
async def on_ready():
    print(f'[INFO] Logged in as {bot.user}')
    scheduler = AsyncIOScheduler()
    print('[INFO] Adding daily message job to scheduler...')
    scheduler.add_job(send_daily_message, 'cron', hour=SEND_TIME.hour, minute=SEND_TIME.minute)
    scheduler.start()
    print(f"[INFO] Current time: {datetime.now()}")
    print(f"[INFO] Scheduler started for {SEND_TIME.hour}:{SEND_TIME.minute} UTC")


async def send_daily_message():
    run_scraper()
    print("[INFO] Generating message...")
    message = get_daily_news()
    print(f"[INFO] Message to send: {message}")
    print(f"[INFO] Attempting to get channel with ID: {DISCORD_CHANNEL_ID}")
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        print("[INFO] Channel found, sending message...")
        await channel.send(message)
        print('[INFO] Message sent successfully')
    else:
        print("[ERROR] Channel not found! Check channel ID and bot permissions.")

bot.run(DISCORD_TOKEN)