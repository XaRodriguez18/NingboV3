import pandas as pd
from datetime import datetime
import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import time as dtime
from dotenv import load_dotenv
import os
import pytz

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("CHANNEL_ID"))


def get_daily_news():
    # Get current month
    month = datetime.now().month
    month_dict = {
        1 : "January", 2 : "February", 3 : "March", 4 : "April", 5 : "May", 6 : "June",
        7 : "July", 8 : "August", 9 : "September", 10 : "October", 11 : "November", 12 : "December"
    }
    month = month_dict[month]
    # print(month)

    # Open corresponding csv file
    file_string = month + '_news.csv'
    news = pd.read_csv("forex_factory_calendar_news_scraper-main/news/" + file_string)
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
    # print(day)

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
    # print(news_message)
    return news_message

# Replace with your bot token and channel ID
TOKEN = DISCORD_TOKEN
CHANNEL_ID = DISCORD_CHANNEL_ID  # Replace with your channel ID
MESSAGE = get_daily_news()

LOCAL_TZ = "America/Denver"

def convert_to_utc(hour: int, minute: int, local_tz_str: str = LOCAL_TZ) -> tuple:
    local_tz = pytz.timezone(local_tz_str)
    now = datetime.now(local_tz)
    local_dt = local_tz.localize(datetime(now.year, now.month, now.day, hour, minute))

    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt.hour, utc_dt.minute

utc_hour, utc_minute = convert_to_utc(6, 30, "America/Denver")

# Set the time you want the message to be sent (24-hour format)
SEND_TIME = dtime(hour=utc_hour, minute=utc_minute)  # 2:00 PM daily
# SEND_TIME = dtime(hour=12, minute=41)  # 2:00 PM daily
print(f"UTC time: {utc_hour}:{utc_minute}")


intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_message, 'cron', hour=SEND_TIME.hour, minute=SEND_TIME.minute)
    scheduler.start()
    print("Scheduler started")


async def send_daily_message():
    print("🧠 Generating message...")
    message = get_daily_news()
    print("Attempting to send message...")
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(message)
        print('Message sent successfully')
    else:
        print("Channel not found!")


bot.run(TOKEN)