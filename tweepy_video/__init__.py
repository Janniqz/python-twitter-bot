# Tweepy
# Copyright 2009-2010 Joshua Roesslein
# See LICENSE for details.

"""
Tweepy Twitter API library
"""
__version__ = '3.7.0'
__author__ = 'Joshua Roesslein'
__license__ = 'MIT'

from tweepy_video.models import Status, User, DirectMessage, Friendship, SavedSearch, SearchResults, ModelFactory, Category
from tweepy_video.error import TweepError, RateLimitError
from tweepy_video.api import API
from tweepy_video.cache import Cache, MemoryCache, FileCache
from tweepy_video.auth import OAuthHandler, AppAuthHandler
from tweepy_video.streaming import Stream, StreamListener
from tweepy_video.cursor import Cursor

# Global, unauthenticated instance of API
api = API()

def debug(enable=True, level=1):
    from six.moves.http_client import HTTPConnection
    HTTPConnection.debuglevel = level
