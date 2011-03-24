#!/usr/bin/python

import feedparser # from http://www.feedparser.org/
import tumblr # from http://code.google.com/p/python-tumblr/


import os, time,sys,codecs,datetime, urlparse

sys.stdout = codecs.getwriter('utf8')(sys.stdout)

FAVOURITES = "http://twitter.com/favorites/aquarion.rss"

BLOG='aquarion.tumblr.com'
USER='nicholas@aquarionics.com'
PASSWORD='Milamber'

TIMECACHE="/home/aquarion/projects/twaves2tumblr/lastime.cache";

f = open(TIMECACHE, "r")
lasttime = f.read(128);
f.close();

highest = lasttime;

api = tumblr.Api(BLOG,USER,PASSWORD)

fp = feedparser.parse(FAVOURITES)

for i in range(len(fp['entries'])):
  item = fp['entries'][i]
  
  datetime = time.mktime(item['updated_parsed'])
  
  if int(datetime) > int(lasttime):
    tweet = item['title'].split(": ")[1]
    print tweet
    user = item['title'].split(": ")[0]
    link= item['link']
    
    source = '<a href="%s">@%s</a>' % (link, user)
    
    post = api.write_quote(tweet,source)
    if int(datetime) > int(highest):
      highest = datetime;


f = open(TIMECACHE, "w")
f.write(str(int(highest)))
f.close();
