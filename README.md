# Installation

This Twitter Bot uses a modified version of Tweepy (https://github.com/tweepy/tweepy) to enable the use of Videos.
The modified Library is included with the Bot itself.

The Bot was built with Python 3.6.4 but should be compatible with older versions.

The following libraries need to be installed manually (Use `pip install -r requirements.txt` or install manually via `pip install [package]`):
* apscheduler
* python-dateutil
* requests
* requests_oauthlib
* six

# Configuration

This is the default configuration:
```
{
   "general":{
      "debug":false
   },
   "bots":{
      "default_name":{
         "enabled":false,
         "consumer_key":"XXX",
         "consumer_secret":"XXX",
         "access_token":"XXX",
         "access_token_secret":"XXX",
         "retweet":false,
         "like":false,
         "post":false,
         "post_scheduled":true,
         "only_media":false,
         "accounts":[
            "2741994341"
         ],
         "post_type":0,
         "interval":900,
         "media_directory":"",
         "message_list":[
            "This is a normal messsage",
            "This message tags some user $user$ (Converts ID from account_list to a username)",
            "This message uses a hashtag $hashtag$ (From the hashtag_list)",
            "This message uses an Emoji $emoji$ (From the emoji_list)",
            "This is a message saying Good Morning or something $time$ (Uses Morning, Afternoon, Evening or Night depending on Time)"
         ],
         "account_list":[
            2741994341,
            705342159499587584,
            235601687
         ],
         "hashtag_list":[
            "Cool",
            "Cute",
            "Nicebot"
         ],
         "emoji_list": ["💗", "🌺", "✨", "❤", "💖", "💮", "🌸", "🌹"],
         "scheduled_posts":{
            "shades":{
               "message":"This is a cool example for a scheduled Post wow!",
               "image":"./media/coolfile.png",
               "time":[
                  "3AM UTC+1",
                  "6PM UTC+1"
               ]
            }
         }
      }
   }
}
```

***

All settings are explained below:  
### General Settings

`debug` - Either true / false. Turns Debug message On or Off. Use this before reporting Errors!
  
`default_name`, `account_name` - Just put a Name for your Bot to make identification easier! Not relevant for the Bot itself.

`consumer_key`,`consumer_secret`,`access_token`,`access_token_secret` -  IMPORTANT! Without these settings the Bot won't be able to run. You can get all of these on the https://apps.twitter.com/ site by creating a application. These settings are responsible for connecting the Bot with the Twitter API.  
  
`retweet`, `like`, `post` - Either true / false. Use these to enable / disable the different functions of the Bot. If all of them are False the Bot won't do anything. Enabling all of them works fine.    
 
### Like & Retweet Settings

`only_media` - Either true / false. If set to true, only Tweets with some kind of media (images, videos) will be retweeted / liked.

`accounts` - List of Twitter Account IDs to Retweet / Like. Seperated by a comma (["123", "321"])
You can get Twitter Account IDs on http://mytwitterid.com/

### Post Settings

`post_type` - Either 1 or 2. Use 1 for simple Text Tweets. Use 2 for Tweets with Videos or Images.

`interval` - Tweet cooldown in seconds. How long to wait until the next Tweet will be sent?

`media_directory` - Directory from which the Bot should take it's Images / Videos. Only with `post_type` 2.

`message_list` - List of messages to post. Bot will pick a random one. Messages enclosed in "" and seperated by a comma.

`account_list` - List of Twitter Account IDs to use for $user$. Bot will pick a random one and convert it to a @.
You can get Twitter Account IDs on http://mytwitterid.com/

`hashtag_list` - List of Hashtags to use for $hashtag$. Bot will pick a random one and convert it to a #.

`emoji_list` - List of Emojis to use for $hashtag$. Bot will pick one(!) and use it for all Emojis in the Message.

### Scheduled Post Settings
`scheduled_posts` - Comma separated List of Dictionaries for scheduled Posts

* `message` - Message that'll be sent with the scheduled Post
* `image` - Path to the Image that should be posted
* `time` - List of Time Strings. 
    * The Bot will try to parse this. E.g. "7:39PM UTC+1". 
    * Picks the closest time out of the List. After the Tweet was posted it'll use the check for the closest time again.

# Using multiple Accounts

Multiple Bot Accounts can be used as follows:

```
{
  "general": {
    "debug": false
  },
  "bots": {
      "default_name": {...},
      "default_name2": {...}
  }
}
```

Accounts are separated by a comma after the } at the end of the first Bot. The last Bot does not have a comma at the end.

# Using Media

When using `post_type: 2` the following regulations apply:
* Image max. size: 5MB
* Animated GIF max. size: 15MB
* Video max. size: 15MB
