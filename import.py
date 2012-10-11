import ConfigParser
import feedparser # from http://www.feedparser.org/

import os, time,sys,codecs,datetime, urlparse
import oauth2 as oauth

import cPickle  as pickle

from tumblr.oauth import TumblrOAuthClient
from tumblr import TumblrClient

config  = ConfigParser.ConfigParser()
#try:
#    config.readfp(open(basedir+'/config.ini'))
#except IOError:
config.readfp(open(os.getcwd()+'/config.ini'))

TIMECACHE  = os.getcwd()+'/'+config.get("cache", "time")
OAUTHCACHE = os.getcwd()+'/'+config.get("cache", "oauth")
FAVOURITES = "https://api.twitter.com/1/favorites.rss?screen_name=%s" % config.get("twitter", "username")


consumer_key    = config.get("tumblr", "consumer_key")
consumer_secret = config.get("tumblr", "secret_key")
hostname        = config.get("tumblr", "blog")


try:
	f = open(OAUTHCACHE, "rb")
	oauth_token = pickle.load(f)
	f.close();
except:
	print "Couldn't open %s, reloading..." % OAUTHCACHE
	oauth_token = False

if(not oauth_token):
	tumblr_oauth = TumblrOAuthClient(consumer_key, consumer_secret)

	authorize_url = tumblr_oauth.get_authorize_url()
	print "Visit: %s" % authorize_url

	oauth_verifier = raw_input('What is the oauth_verifier?')
	oauth_token = tumblr_oauth.get_access_token(oauth_verifier)
	print "Access key:", oauth_token.key
	print "Access Secret:", oauth_token.secret

	f = open(OAUTHCACHE, "w")
	pickle.dump(oauth_token, f)
	f.close();
	
f = open(TIMECACHE, "rb")
lasttime = f.read(128);
f.close();


highest = lasttime;

consumer = oauth.Consumer(consumer_key, consumer_secret)
token = oauth.Token(oauth_token.key, oauth_token.secret)
client = TumblrClient(hostname, consumer, token)

fp = feedparser.parse(FAVOURITES)
for i in range(len(fp['entries'])):
	item = fp['entries'][i]

	datetime = time.mktime(item['updated_parsed'])

	if int(datetime) > int(lasttime):
		tweet = item['title'].split(": ")[1].encode( "utf-8" )
		user = item['title'].split(": ")[0]
		link= item['link']

		source = '<a href="%s">@%s</a>' % (link, user)

		post = {
			'type': "quote",
			'tweet': 'off',
			'quote': tweet,
			'source': source
		}
		post = client.create_post(post)

		if int(datetime) > int(highest):
			highest = datetime;


f = open(TIMECACHE, "w")
f.write(str(int(highest)))
f.close();
