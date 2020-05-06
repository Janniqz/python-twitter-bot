import re
import tweepy_video
import random
import json
import os
import sys
import asyncio
import logging
from datetime import datetime, date, timezone, timedelta
from dateutil import parser
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from logging.handlers import TimedRotatingFileHandler


def load_data():  # Executed on Startup
    global data
    with open("config.json", "r", encoding="utf-8") as f:
        data = json.load(f)


def get_file_list(pathin):
    return [os.path.join(path, file)
            for (path, dirs, files) in os.walk(pathin)
            for file in files]


def setup_logger():
    if not os.path.exists("logs"):
        os.mkdir("logs")

    log_formatter = logging.Formatter(fmt='[%(asctime)s][%(levelname)s]: %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')

    logging_file_handler = TimedRotatingFileHandler(os.path.join("logs", f"twitter.log"), when="midnight", backupCount=3, encoding='utf-8')
    logging_file_handler.setFormatter(log_formatter)
    logging_console_handler = logging.StreamHandler()
    logging_console_handler.setFormatter(log_formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(logging_file_handler)
    logger.addHandler(logging_console_handler)

    return logger


def get_time_thingy():
    time = datetime.now().hour
    if time < 6:
        return "Night!"
    elif 6 <= time < 12:
        return "Morning!"
    elif 12 <= time < 17:
        return "Afternoon!"
    else:
        return "Evening!"


twitter_streaming_started = False
scheduler = AsyncIOScheduler()
logger = setup_logger()
twitter_data = {}
file_lists = {}
data = {}


class TwitterStreamListener(tweepy_video.StreamListener):
    def on_status(self, status):
        if not hasattr(status, 'retweeted_status') and status.in_reply_to_status_id is None:
            for bot_name, bot_data in data['bots'].items():
                if status.user.id_str in bot_data["accounts"]:
                    if (not bot_data["only_media"]) or (hasattr(status, "extended_tweet") and ("media" in status.extended_tweet['entities']) and len(status.extended_tweet['entities']['media']) != 0) or ("media" in status.entities and len(status.entities['media']) != 0):
                        if bot_data["like"]:
                            twitter_data[bot_name]['api'].create_favorite(status.id)
                        if bot_data["retweet"]:
                            twitter_data[bot_name]['api'].retweet(status.id)
                        logger.info(f"[{bot_name.title()}] Retweeted / Liked Tweet {str(status.id)}")

    def on_error(self, status_code):
        logger.error(status_code)
        return True


async def start():
    while True:
        await asyncio.sleep(1)


def setup_bots():
    global twitter_streaming_started
    for bot_name, bot_data in data['bots'].items():
        bot_data['name'] = bot_name
        if not bot_data["enabled"] or not (bot_data['post'] or bot_data['post_scheduled'] or bot_data['like'] or bot_data['retweet']):
            continue
        twitter_data[bot_name] = {}
        twitter_data[bot_name]["auth"] = tweepy_video.OAuthHandler(bot_data["consumer_key"], bot_data["consumer_secret"])
        twitter_data[bot_name]["auth"].set_access_token(bot_data["access_token"], bot_data["access_token_secret"])
        twitter_data[bot_name]["api"] = tweepy_video.API(twitter_data[bot_name]["auth"], timeout=60)
        if not os.path.exists(f"./media/{bot_name}"):
            os.makedirs(f"./media/{bot_name}")
        if not twitter_streaming_started and (bot_data["like"] or bot_data["retweet"]):
            twitter_streaming_started = True
            combined_account_list = []
            for bot in data['bots'].values():
                combined_account_list = combined_account_list + bot["accounts"]
            combined_account_list = list(set(combined_account_list))
            listener = TwitterStreamListener()
            stream = tweepy_video.Stream(auth=twitter_data[bot_name]["api"].auth, listener=listener)
            stream.filter(follow=combined_account_list, is_async=True)
        if bot_data["post"]:
            if bot_data["media_directory"] != "":
                file_lists[bot_name] = get_file_list(bot_data["media_directory"])
            else:
                file_lists[bot_name] = get_file_list(f"./media/{bot_name}")
            scheduler.add_job(post, 'interval', [bot_data, twitter_data[bot_name]], seconds=bot_data["interval"], id=bot_name, name=f"Twitter - {bot_name.title()}", misfire_grace_time=300)
        if bot_data["post_scheduled"]:
            for scheduled_name, scheduled_data in bot_data['scheduled_posts'].items():
                scheduled_data['name'] = scheduled_name
                dt = post_scheduled_get_next(scheduled_data['time'])
                scheduler.add_job(post_scheduled, 'date', [bot_data, twitter_data[bot_name], scheduled_data], run_date=dt, id=f"{bot_name}_{scheduled_name}", name=f"Twitter - {bot_name.title()} Scheduled - {scheduled_name.title()}", misfire_grace_time=300)


async def post(bot, twitter):
    message = None
    if len(bot['message_list']) != 0:
        message = format_message(bot, twitter, random.choice(bot["message_list"]))

    if bot["post_type"] == 1:
        if message is None:
            logger.error(f"[{bot['name'].title()}] No Messages set but Post Type set to 1! Disabling!")
            scheduler.remove_job(bot['name'])
            return
        twitter["api"].update_status(status=message)
    elif bot["post_type"] == 2:
        if len(file_lists[bot['name']]) == 0:
            if bot["media_directory"] != "":
                file_lists[bot['name']] = get_file_list(bot["media_directory"])
            else:
                file_lists[bot['name']] = get_file_list(f"./media/{bot['name']}")
            for file in file_lists[bot['name']]:
                if os.path.getsize(file) / 1024 >= 15360:
                    file_lists[bot['name']].remove(file)
            if len(file_lists[bot['name']]) == 0:
                logger.warning(f"[{bot['name'].title()}] Has no files available. Disabled.")
                scheduler.remove_job(bot['name'])
                return

        while True:
            file = random.choice(file_lists[bot['name']])
            file_lists[bot['name']].remove(file)
            if os.path.exists(file):
                break
        if message:
            while "$src$" in message:
                if os.path.basename(os.path.dirname(file)) == bot['name']:
                    message = message.replace('$src$', "Unknown")
                message = message.replace('$src$', os.path.basename(os.path.dirname(file)))

        if data['general']['debug']:
            logger.info(f"[{bot['name'].title()}] Used file: {file}")
        upload = twitter["api"].media_upload(file)
        await asyncio.sleep(10)
        twitter["api"].update_status(status=message, media_ids=[upload.media_id_string])

    logger.info(f"[{bot['name'].title()}] Posted!")
    await asyncio.sleep(1)


async def post_scheduled(bot, twitter, scheduled_data):
    message = ""
    if scheduled_data['message'] is not None:
        message = format_message(bot, twitter, scheduled_data['message'])

    if scheduled_data['image'] is None:
        if message is None:
            logger.error(f"[{bot['name'].title()}] No Images & Messages set! Disabling!")
            scheduler.remove_job(bot['name'])
            return
        twitter["api"].update_status(status=message)
    else:
        if os.path.isdir(scheduled_data['image']):
            image = random.choice(get_file_list(scheduled_data['image']))
        else:
            if not os.path.exists(scheduled_data['image']):
                logger.warning(f"[{bot['name'].title()}] Couldn't find Image for Scheduled Tweet {scheduled_data['name'].title()}")
                return
            elif os.path.getsize(scheduled_data['image']) / 1024 > 15360:
                logger.warning(f"[{bot['name'].title()}] Image Size for Scheduled Tweet {scheduled_data['name'].title()} too big!")
                return
            image = scheduled_data['image']

        if data['general']['debug']:
            logger.info(f"[{bot['name'].title()}] Used file: {scheduled_data['image']}")
        upload = twitter["api"].media_upload(image)
        await asyncio.sleep(10)
        twitter["api"].update_status(status=message, media_ids=[upload.media_id_string])

    logger.info(f"[{bot['name'].title()}] Scheduled Tweet {scheduled_data['name']} Posted!")

    dt = post_scheduled_get_next(scheduled_data['time'])
    scheduler.add_job(post_scheduled, 'date', [bot, twitter, scheduled_data], run_date=dt, id=f"{bot['name']}_{scheduled_data['name']}", name=f"Twitter - {bot['name'].title()} Scheduled - {scheduled_data['name'].title()}", misfire_grace_time=300)
    logger.info(f"[{bot['name'].title()}] Scheduled next Tweet for {scheduled_data['name']} at {dt}!")

    await asyncio.sleep(1)


def post_scheduled_get_next(times):
    next_dt = None
    for time_string in times:
        if 'utc-' in time_string.lower():
            time_string = re.sub("UTC-", "UTC+", time_string, flags=re.I)
        elif 'utc+' in time_string.lower():
            time_string = re.sub("UTC\\+", "UTC-", time_string, flags=re.I)
        dt = parser.parse(time_string, default=datetime(year=date.today().year, month=date.today().month, day=date.today().day, hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc))
        dt = time_check(dt)
        if not dt:
            continue
        if next_dt is None or dt < next_dt:
            next_dt = dt
    return next_dt


def format_message(bot, twitter, message):
    account_list = list(bot["account_list"])
    hashtag_list = list(bot["hashtag_list"])
    while "$user$" in message:
        user = random.choice(account_list)
        try:
            message = message.replace('$user$', f"@{twitter['api'].get_user(user).screen_name}", 1)
        except tweepy_video.TweepError as e:
            if e.api_code == 50:
                logger.warning(f"[{bot['name'].title()}] Couldn't find user with ID {str(user)}")
        account_list.remove(user)
    while "$hashtag$" in message:
        hashtag = random.choice(hashtag_list)
        message = message.replace('$hashtag$', f"#{random.choice(hashtag_list)}", 1)
        hashtag_list.remove(hashtag)
    while "$time$" in message:
        message = message.replace('$time$', get_time_thingy())
    while "$emoji$" in message:
        message = message.replace('$emoji$', random.choice(bot['emoji_list']))
    return message


def time_check(dt: datetime):
    now = datetime.now(tz=timezone.utc)
    if dt < now:
        if (now - dt).days < 1:
            dt = dt + timedelta(days=1)
        else:
            return False
    return dt


if __name__ == '__main__':
    load_data()

    setup_bots()
    if len(scheduler._pending_jobs) == 0:
        logger.error(f"No Bots found / enabled! Shutting down.")
        sys.exit(0)

    scheduler.start()
    scheduler.print_jobs()

loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(start())]
loop.run_until_complete(asyncio.wait(tasks))
loop.close()
