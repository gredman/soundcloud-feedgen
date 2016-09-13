#!/usr/bin/env python

import datetime
import pytz
import sys

from dateutil import parser
from feedgen.feed import FeedGenerator
from os import environ
from soundcloud import Client

OUTPUT_DIR = environ['OUTPUT_DIR']
CLIENT_ID = environ['CLIENT_ID']
CLIENT_SECRET = environ['CLIENT_SECRET']
USERNAME = environ['USERNAME']
PASSWORD = environ['PASSWORD']

MAX_AGE_DAYS=30

client = Client(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        username=USERNAME,
        password=PASSWORD)
now = datetime.datetime.now(pytz.utc)

for set_url in sys.argv[1:]:
    fg = FeedGenerator()
    fg.load_extension('podcast', atom=True, rss=True)

    res = client.get('/resolve', url=set_url)

    fg.id(set_url)
    
    if res.kind == 'user':
        fg.title(res.username)
        fg.description(res.username)
        fg.logo(res.avatar_url)
        fg.author({'name': res.username})
    elif res.kind == 'playlist':
        fg.title(res.title)
        fg.description(res.title)
        fg.logo(res.user['avatar_url'])
        fg.author({'name': res.user['username']})
    else:
        raise Exception('unknown kind %s' % res.kind)

    tracks = client.get(res.uri + '/tracks')
    fg.link(href=res.permalink_url, rel='alternate')

    for track in tracks:
        if track.streamable:
            url = track.stream_url
        else:
            continue

        date = parser.parse(track.last_modified)
        if (now - date).days > MAX_AGE_DAYS:
            continue

        fe = fg.add_entry()
        fe.id(track.permalink_url)
        fe.title(track.title)
        fe.description(track.description)
        fe.published(date)
        resolved_url = client.get(url, allow_redirects=False)
        fe.enclosure(resolved_url.location, str(track.original_content_size), 'audio/mpeg')

    fg.rss_file('%s/%s.xml' % (OUTPUT_DIR, res.permalink), pretty=True)
