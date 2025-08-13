import pandas as pd
from datetime import datetime
import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import time as dtime
import asyncio
from dotenv import load_dotenv
import os
import pytz

load_dotenv()

DSTOKEN = os.getenv("DISCORD_TOKEN")
DSCHANNEL_ID = int(os.getenv("CHANNEL_ID"))
SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL"))
NEWS_SOURCE_URL = os.getenv("NEWS_SOURCE_URL")


def getDailyNews():
    # Get current month
    month = datetime.now().month
    monthDict = {
        1 : "January",
        2 : "February",
        3 : "March",
        4 : "April",
        5 : "May",
        6 : "June",
        7 : "July",
        8 : "August",
        9 : "September",
        10 : "October",
        11 : "November",
        12 : "December"
    }
    month = monthDict[month]
    # print(month)

    # Open corresponding csv file
    fileString = month + '_news.csv'
    news = pd.read_csv("forex_factory_calendar_news_scraper-main/news/" + fileString)
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
    currentDay = [month[0:3] + " " + str(day)]
    # print(currentDay)
    mask = news['date'].isin(currentDay)
    currentDayRows = news[mask]
    print(currentDayRows)

    # Generate news message to be displayed
    messageList = ['time', 'currency', 'impact', 'event']
    newsMessage = f"{currentDay[0]} News:\n"
    if currentDayRows.empty:
        newsMessage += "No relevant news today"
    else:
        for index, row in currentDayRows.iterrows():
            for name in messageList:
                newsMessage += str(row[name]) + "\t"
            newsMessage += "\n"

    print(newsMessage)
    return newsMessage

# Replace with your bot token and channel ID
TOKEN = DSTOKEN
CHANNEL_ID = DSCHANNEL_ID  # Replace with your channel ID
MESSAGE = getDailyNews()

def convert_to_utc(hour: int, minute: int, local_tz_str: str = "America/Denver") -> tuple:
    local_tz = pytz.timezone(local_tz_str)
    now = datetime.now(local_tz)
    local_dt = local_tz.localize(datetime(now.year, now.month, now.day, hour, minute))

    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt.hour, utc_dt.minute

utc_hour, utc_minute = convert_to_utc(12, 20, "America/Denver")

# Set the time you want the message to be sent (24-hour format)
SEND_TIME = dtime(hour=utc_hour, minute=utc_minute)  # 2:00 PM daily
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
    print("Attempting to send message...")
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(MESSAGE)
        print('Message sent successfully')
    else:
        print("Channel not found!")


bot.run(TOKEN)