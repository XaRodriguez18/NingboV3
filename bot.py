# Import necessary libraries
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from datetime import datetime
from datetime import time as dtime
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pandas as pd
import pytz
from scraper.scraper import runScraper

# Bot initialization
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
load_dotenv()

# Load environment variables
DISCORD_TOKEN =      os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("CHANNEL_ID")
LOCAL_TZ =           os.getenv("LOCAL_TZ")
SEND_HOUR =          os.getenv("SEND_HOUR")
SEND_MIN =           os.getenv("SEND_MIN")

# Log environment variable values before type conversion
# print(f"[LOG] DISCORD_TOKEN: {repr(DISCORD_TOKEN)}")
# print(f"[LOG] CHANNEL_ID: {repr(DISCORD_CHANNEL_ID)}")
# print(f"[LOG] LOCAL_TZ: {repr(LOCAL_TZ)}")
# print(f"[LOG] SEND_HOUR: {repr(SEND_HOUR)}")
# print(f"[LOG] SEND_MIN: {repr(SEND_MIN)}")

# Convert environment variable types to integers after logging
DISCORD_CHANNEL_ID = int(DISCORD_CHANNEL_ID) if DISCORD_CHANNEL_ID is not None else None
SEND_HOUR =          int(SEND_HOUR) if SEND_HOUR is not None else None
SEND_MIN =           int(SEND_MIN) if SEND_MIN is not None else None

# def get_daily_news():
#     # Get today's date string for the CSV filename
#     today_str = datetime.now().strftime("%Y-%m-%d")
#     file_string = today_str + '_news.csv'
#     news_dir = os.path.abspath("news")
#     news_path = os.path.join(news_dir, file_string)
#     print(f"[INFO] Absolute news directory: {news_dir}")
#     print(f"[INFO] Loading news from: {news_path}")
#     if not os.path.exists(news_path):
#         print("[WARN] News file not found for today.")
#         return "No news data available for today."
#     print("[INFO] News file found, reading CSV...")
#     news = pd.read_csv(news_path)

#     # Filter countries (United States)
#     country = ['USD']
#     mask = news['currency'].isin(country)
#     news = news[mask]
#     # Filter impact (Red and Orange)
#     impact = ['red', 'orange']
#     mask = news['impact'].isin(impact)
#     news = news[mask]

#     # Get today's date for display
#     today_display = datetime.now().strftime("%b %d")
#     mask = news['date'] == today_display
#     current_day_rows = news[mask]

#     # Generate news message to be displayed
#     message_list = ['time', 'currency', 'impact', 'event']
#     news_message = f"{today_display} News:\n"
#     if current_day_rows.empty:
#         news_message += "No relevant news today"
#     else:
#         for index, row in current_day_rows.iterrows():
#             for name in message_list:
#                 news_message += str(row[name]) + "\t"
#             news_message += "\n"
#     print(f"[INFO] Current message:\n{news_message}")
#     return news_message


def convertToUtc(hour: int, minute: int, localTimeZoneString: str = LOCAL_TZ) -> tuple:
    """
    Convert local time to UTC time.

    Args:
        hour (int): Hour in local time (24-hour format).
        minute (int): Minute in local time.
        localTimeZoneString (str): Local timezone string.

    Returns:
        tuple (
            utcHour (int): Hour in UTC time (24-hour format).
            utcMinute (int): Minute in UTC time.
        )

    """
    # print(f"[INFO] Converting local time {hour}:{minute} in {localTimeZoneString} to UTC...")
    localTimeZone = pytz.timezone(localTimeZoneString)
    now = datetime.now(localTimeZone)
    localDateTime = localTimeZone.localize(datetime(now.year, now.month, now.day, hour, minute))
    utcDateTime = localDateTime.astimezone(pytz.utc)
    # print(f"[INFO] UTC time is {utcDateTime.hour}:{utcDateTime.minute}")
    return utcDateTime.hour, utcDateTime.minute

# Convert the send hour and minute to UTC time object for scheduling
utcHour, utcMinute = convertToUtc(SEND_HOUR, SEND_MIN, LOCAL_TZ)

@bot.event
async def on_ready():
    """
    Event handler when the bot is ready.

    Sets up the scheduler to send daily messages at the specified UTC time.
    """
    # print(f'[INFO] Logged in as {bot.user}')
    scheduler = AsyncIOScheduler()
    # print('[INFO] Adding daily message job to scheduler...')
    scheduler.add_job(sendDailyMessage, 'cron', hour=utcHour, minute=utcMinute)
    scheduler.start()
    # print(f"[INFO] Current time: {datetime.now()}")
    # print(f"[INFO] Scheduler started for {utcHour}:{utcMinute} UTC")

# TODO: Split into smaller functions and modularize
async def sendDailyMessage():
    runScraper()
    # print("[INFO] Generating message...")
    todayStr = datetime.now().strftime("%Y-%m-%d")
    fileStr = todayStr + '_news.csv'
    newsDir = os.path.abspath("news")
    newsPath = os.path.join(newsDir, fileStr)

    # TODO: Add error handling for file read
    if not os.path.exists(newsPath):
        embed = discord.Embed(title="Daily News", description="No news data available for today.", color=0x808080)
    else:
        news = pd.read_csv(newsPath)

        # Filter countries (United States)
        country = ['USD']
        mask = news['currency'].isin(country)
        news = news[mask]

        # Filter impact (Red and Orange)
        impact = ['red', 'orange']
        mask = news['impact'].isin(impact)
        news = news[mask]

        # Filter date (Today) & Get today's date for embed display
        todayDisplay = datetime.now().strftime("%b %d")
        mask = news['date'] == todayDisplay
        rowsToDisplay = news[mask]

        # Build embed description
        if rowsToDisplay.empty:
            desc = "No relevant news today"
            color = 0x808080 # Grey for no news
        else:
            desc = ""
            for _, row in rowsToDisplay.iterrows():
                # Set color to red if any red impact
                if row['impact'] == 'red':
                    color = 0xFF0000
                elif row['impact'] == 'orange' and color != 0xFF0000:
                    color = 0xFFA500
                elif row['impact'] == 'yellow' and color not in (0xFF0000, 0xFFA500):
                    color = 0xFFFF00
                desc += f"`{row['time']}` **{row['currency']}** {row['impact'].capitalize()} - {row['event']}\n"
        embed = discord.Embed(title=f"{todayDisplay} News", description=desc, color=color)
        embed.set_footer(text="Source: Forex Factory\nhttps://www.forexfactory.com/")
    print(f"[INFO] Attempting to get channel with ID: {DISCORD_CHANNEL_ID}")
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        print("[INFO] Channel found, sending embed...")
        await channel.send(embed=embed)
        print('[INFO] Embed sent successfully')
    else:
        print("[ERROR] Channel not found! Check channel ID and bot permissions.")

    # Cleanup: delete today's CSV after sending message
    try:
        from scraper.cleanup import delete_today_csv
        delete_today_csv()
    except Exception as e:
        print(f"[CLEANUP] Error during CSV deletion: {e}")

bot.run(DISCORD_TOKEN)