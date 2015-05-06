#!/usr/bin/python

import sys
import codecs

import ConfigParser

import os
import time
import sys
import codecs
import datetime
import urlparse
import oauth2 as oauth

import cPickle as pickle

from pytumblr import TumblrRestClient

from twitter import Twitter

from twitter.oauth import OAuth, write_token_file, read_token_file
from twitter.oauth_dance import oauth_dance

import socket

sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

socket.setdefaulttimeout(60)  # Force a timeout if twitter doesn't respond

config = ConfigParser.ConfigParser()
basedir = os.path.dirname(os.path.abspath(sys.argv[0]))

try:
    config.readfp(open(basedir + '/config.ini'))
except IOError:
    config.readfp(open(os.getcwd() + '/config.ini'))

TIMECACHE = basedir + '/' + config.get("cache", "time")
OAUTH_TUMBLR = basedir + '/' + config.get("cache", "oauth_tumblr")
OAUTH_TWITTER = basedir + '/' + config.get("cache", "oauth_twitter")

f = open(TIMECACHE, "rb")
highestid = f.read(128)
f.close()


def tumblrAuth(config, OAUTH_TUMBLR):
    consumer_key = config.get("tumblr", "consumer_key")
    consumer_secret = config.get("tumblr", "secret_key")
    hostname = config.get("tumblr", "blog")

    try:
        f = open(OAUTH_TUMBLR, "rb")
        oauth_token = pickle.load(f)
        f.close()
    except:
        print "Couldn't open %s, reloading..." % OAUTH_TUMBLR
        oauth_token = False

    if(not oauth_token):
        tumblr_oauth = TumblrOAuthClient(consumer_key, consumer_secret)

        authorize_url = tumblr_oauth.get_authorize_url()
        print "Visit: %s" % authorize_url

        oauth_verifier = raw_input('What is the oauth_verifier?')
        oauth_token = tumblr_oauth.get_access_token(oauth_verifier)
        print "Access key:", oauth_token.key
        print "Access Secret:", oauth_token.secret

        f = open(OAUTH_TUMBLR, "w")
        pickle.dump(oauth_token, f)
        f.close()

    f = open(TIMECACHE, "rb")
    lasttime = f.read(128)
    f.close()

    return TumblrRestClient(consumer_key, consumer_secret,
                            oauth_token.key, oauth_token.secret)


def twitterAuth(config, OAUTH_TWITTER):
    HOME = os.environ.get('HOME', '')
    twitter_user = config.get("twitter", "username")
    OAUTH_FILENAME = HOME + os.sep + '.lifesteam_oauth_' + twitter_user
    CONSUMER_KEY = config.get("twitter", "consumer_key")
    CONSUMER_SECRET = config.get("twitter", "consumer_secret")

    if not os.path.exists(OAUTH_FILENAME):
        oauth_dance(
            "Lifestream", CONSUMER_KEY, CONSUMER_SECRET,
            OAUTH_FILENAME)

    oauth_token, oauth_token_secret = read_token_file(OAUTH_FILENAME)

    return Twitter(
        auth=OAuth(
            oauth_token, oauth_token_secret, CONSUMER_KEY, CONSUMER_SECRET),
        secure=True,
        api_version='1.1',
        domain='api.twitter.com')


twitterClient = twitterAuth(config, OAUTH_TWITTER)

tumblrClient = tumblrAuth(config, OAUTH_TUMBLR)

favourites = twitterClient.favorites.list(
    screen_name=config.get("twitter", "username"))

newhighest = long(highestid)


def text_tweet(favourite):
    tweet = favourite['text'].encode('utf8')
    user = favourite['user']['screen_name']
    link = 'http://twitter.com/%s/status/%s' % (
        favourite['user']['screen_name'], favourite['id'])
    source = '<a href="%s">@%s</a> (Favourited on Twitter by @%s)' % (
        link, user, config.get("twitter", "username"))
    source = source.encode('utf8')

    post = tumblrClient.create_quote(
        "tumblr.aquarionics.com", quote=tweet,
        source=source, tags=["twitterfave"])

    # print favourite['id']
    if long(favourite['id']) > newhighest:
        newhighest = favourite['id']


def photo_tweet(favourite):
    tweet = favourite['text'].encode('utf8')
    user = favourite['user']['screen_name']
    link = 'http://twitter.com/%s/status/%s' % (
        favourite['user']['screen_name'], favourite['id'])
    source = '<a href="%s">@%s</a> (Favourited on Twitter by @%s)' % (
        link, user, config.get("twitter", "username"))
    source = source.encode('utf8')

    photo_url = favourite['entities']['media'][0]['media_url']

    tumblrClient.create_photo("tumblr.aquarionics.com", state="published",
                              tags=["twitterfave"],
                              source=photo_url,
                              caption=source,
                              link=link)

    # print favourite['id']

for favourite in favourites:
    if long(favourite['id']) > long(highestid):

        if 'entities' in favourite and 'media' in favourite['entities']:
            photo_tweet(favourite)
        else:
            quote_tweet(favourite)

        if long(favourite['id']) > newhighest:
            newhighest = favourite['id']


f = open(TIMECACHE, "w")
f.write(str(int(newhighest)))
f.close()
