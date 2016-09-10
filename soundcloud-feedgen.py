#!/usr/bin/env python

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

client = Client(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        username=USERNAME,
        password=PASSWORD)

for set_url in sys.argv[1:]:
    fg = FeedGenerator()
    fg.load_extension('podcast', atom=True, rss=True)

    res = client.get('/resolve', url=set_url)

    fg.id(set_url)
    fg.title(res.title)
    fg.description(res.title)
    fg.author({'name': res.user['username']})
    fg.link(href=res.permalink_url, rel='alternate')
    fg.logo(res.user['avatar_url'])

    for track in res.tracks:
        if track['downloadable']:
            url = track['download_url']
        elif track['streamable']:
            url = track['stream_url']
        else:
            continue

        fe = fg.add_entry()
        fe.id(track['permalink_url'])
        fe.title(track['title'])
        fe.description(track['description'])
        date = parser.parse(track['last_modified'])
        fe.published(date)
        resolved_url = client.get(url, allow_redirects=False)
        fe.enclosure(resolved_url.location, str(track['original_content_size']), 'audio/mpeg')

    fg.rss_file('%s/%s.xml' % (OUTPUT_DIR, res.permalink), pretty=True)
