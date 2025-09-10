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
    # Get current month
    month = datetime.now().month
    month_dict = {
        1 : "January", 2 : "February", 3 : "March", 4 : "April", 5 : "May", 6 : "June",
        7 : "July", 8 : "August", 9 : "September", 10 : "October", 11 : "November", 12 : "December"
    }
    month = month_dict[month]
    print(f"Current month: {month}")

    # Open corresponding csv file
    file_string = month + '_news.csv'
    news = pd.read_csv("scraper/news/" + file_string)
    # print(news.head(10))

    # Functionality to filter dataframe data
    # Filter countries (United States)
    country = ['USD']
    mask = news['currency'].isin(country)
    news = news[mask]
    # Filter impact (Red and Orange)
    impact = ['red', 'orange']
    mask = news['impact'].isin(impact)
    news = news[mask]
    # print(news)

    # Get current day
    day = datetime.now().day
    print(f"Current day: {day}")

    # Get only those rows from the current date
    current_day = [month[0:3] + " " + str(day)]
    # print(current_day)
    mask = news['date'].isin(current_day)
    current_day_rows = news[mask]
    # print(current_day_rows)

    # Generate news message to be displayed
    message_list = ['time', 'currency', 'impact', 'event']
    news_message = f"{current_day[0]} News:\n"
    if current_day_rows.empty:
        news_message += "No relevant news today"
    else:
        for index, row in current_day_rows.iterrows():
            for name in message_list:
                news_message += str(row[name]) + "\t"
            news_message += "\n"
    print(f"Current message:\n{news_message}")
    return news_message

def convert_to_utc(hour: int, minute: int, local_tz_str: str = LOCAL_TZ) -> tuple:
    local_tz = pytz.timezone(local_tz_str)
    now = datetime.now(local_tz)
    local_dt = local_tz.localize(datetime(now.year, now.month, now.day, hour, minute))

    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt.hour, utc_dt.minute

utc_hour, utc_minute = convert_to_utc(SEND_HOUR, SEND_MIN, LOCAL_TZ)

# Set the time you want the message to be sent (24-hour format)
SEND_TIME = dtime(hour=utc_hour, minute=utc_minute)
# SEND_TIME = dtime(hour=12, minute=41)
print(f"Local time: {SEND_HOUR}:{SEND_MIN}")
print(f"UTC time: {utc_hour}:{utc_minute}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    scheduler = AsyncIOScheduler()

    # Daily message job
    scheduler.add_job(send_daily_message, 'cron', hour=SEND_TIME.hour, minute=SEND_TIME.minute)

    # Monthly scraper job
    scheduler.add_job(run_scraper, CronTrigger(day=1, hour=0, minute=0))

    scheduler.start()
    print("Scheduler started")


async def send_daily_message():
    print("Generating message...")
    message = get_daily_news()
    print("Attempting to send message...")
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send(message)
        print('Message sent successfully')
    else:
        print("Channel not found!")

bot.run(DISCORD_TOKEN)