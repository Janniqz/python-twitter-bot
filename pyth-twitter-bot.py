import libraries.tweepy as tweepy
import random
import json
import datetime as dt
import os
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from logging.handlers import TimedRotatingFileHandler


def activate_logging():
    if not os.path.exists("logs"):
        os.makedirs("logs")
    logging_handler = TimedRotatingFileHandler(os.path.join("logs", "debug.log"), when="midnight")
    logging_handler.setFormatter(logging.Formatter(fmt='%(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
    logging_handler.setLevel(10)
    logging.getLogger().addHandler(logging_handler)


def load_data():  # Executed on Startup
    global data
    with open("config.json", "r", encoding="utf-8") as f:
        data = json.load(f)


def get_file_list(pathin):
    return [os.path.join(path, file)
            for (path, dirs, files) in os.walk(pathin)
            for file in files]


def get_time():
    now = dt.datetime.now()
    return "[" + now.strftime("%Y-%m-%d %H:%M:%S") + "] "


def get_time_thingy():
    time = dt.datetime.now().hour
    if time < 6:
        return "Night!"
    elif 6 <= time < 12:
        return "Morning!"
    elif 12 <= time < 17:
        return "Afternoon!"
    else:
        return "Evening!"


async def start():
    while True:
        await asyncio.sleep(1)


streaming_started = False
scheduler = AsyncIOScheduler()
load_data()
twitter_data = {}


class TwitterStreamListener(tweepy.StreamListener):
    def on_status(self, status):
        if not hasattr(status, 'retweeted_status') and status.in_reply_to_status_id is None:
            for bot in data['bots']:
                if status.user.id_str in data['bots'][bot]["accounts"]:
                    if (not data['bots'][bot]["only_media"]) or (hasattr(status, "extended_tweet") and ("media" in status.extended_tweet['entities']) and len(status.extended_tweet['entities']['media']) != 0) or ("media" in status.entities and len(status.entities['media']) != 0):
                        if data['bots'][bot]["like"]:
                            twitter_data[bot]['api'].create_favorite(status.id)
                        if data['bots'][bot]["retweet"]:
                            twitter_data[bot]['api'].retweet(status.id)
                        print(get_time() + "[" + bot.title() + "] Retweeted / Liked Tweet " + str(status.id))

    def on_error(self, status_code):
        print(status_code)


for bot in data['bots']:
    twitter_data[bot] = {}
    twitter_data[bot]["auth"] = tweepy.OAuthHandler(data['bots'][bot]["consumer_key"], data['bots'][bot]["consumer_secret"])
    twitter_data[bot]["auth"].set_access_token(data['bots'][bot]["access_token"], data['bots'][bot]["access_token_secret"])
    twitter_data[bot]["api"] = tweepy.API(twitter_data[bot]["auth"])
    if not os.path.exists("./media/" + bot):
        os.makedirs("./media/" + bot)
    if not streaming_started and (data['bots'][bot]["like"] or data['bots'][bot]["retweet"]):
        streaming_started = True
        combined_account_list = []
        for bot_n in data['bots']:
            combined_account_list = combined_account_list + data['bots'][bot_n]["accounts"]
        combined_account_list = list(set(combined_account_list))
        listener = TwitterStreamListener()
        stream = tweepy.Stream(auth=twitter_data[bot]["api"].auth, listener=listener)
        stream.filter(follow=combined_account_list, async=True)
    if data['bots'][bot]["post"]:
        if data['bots'][bot]["media_directory"] != "":
            twitter_data[bot]["file_list"] = get_file_list(data['bots'][bot]["media_directory"])
        else:
            twitter_data[bot]["file_list"] = get_file_list("./media/" + bot)


async def tweet(name):
    message = random.choice(data['bots'][name]["message_list"])
    account_list = list(data['bots'][name]["account_list"])
    hashtag_list = list(data['bots'][name]["hashtag_list"])

    while "$user$" in message:
        user = random.choice(account_list)
        try:
            message = message.replace('$user$', "@" + twitter_data[name]['api'].get_user(user).screen_name, 1)
        except tweepy.TweepError as e:
            if e.api_code == 50:
                print(get_time() + "[" + name.title() + "] Couldn't find user with ID" + str(user))
        account_list.remove(user)
    while "$hashtag$" in message:
        hashtag = random.choice(hashtag_list)
        message = message.replace('$hashtag$', "#" + hashtag, 1)
        hashtag_list.remove(hashtag)
    while "$time$" in message:
        time = get_time_thingy()
        message = message.replace('$time$', time)

    if data['bots'][name]["post_type"] == 1:
        twitter_data[name]["api"].update_status(status=message)
    elif data['bots'][name]["post_type"] == 2:
        if len(twitter_data[name]["file_list"]) == 0:
            if data['bots'][name]["media_directory"] != "":
                twitter_data[name]["file_list"] = get_file_list(data['bots'][name]["media_directory"])
            else:
                twitter_data[name]["file_list"] = get_file_list("./media/" + bot)
        file = random.choice(twitter_data[name]["file_list"])
        twitter_data[name]["file_list"].remove(file)
        if data['general']['debug']:
            print(get_time() + "[" + name.title() + "] Used file: " + file)
        upload = twitter_data[name]["api"].media_upload(file)
        await asyncio.sleep(10)
        twitter_data[name]["api"].update_status(status=message, media_ids=[upload.media_id_string])

    print(get_time() + "[" + name.title() + "] Tweet posted!")
    await asyncio.sleep(1)


for bot in data['bots']:
    if data['bots'][bot]["post"]:
        scheduler.add_job(tweet, 'interval', [bot], seconds=data['bots'][bot]["interval"], name=bot.title(), misfire_grace_time=300)


if data['general']['enable_logging']:
    activate_logging()


async def reload():
    load_data()
    await asyncio.sleep(1)

scheduler.add_job(reload, 'interval', seconds=data['general']['reload_timer'], name="Data Reload", misfire_grace_time=300)
scheduler.start()
scheduler.print_jobs()

loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(start())]
loop.run_until_complete(asyncio.wait(tasks))
loop.close()
