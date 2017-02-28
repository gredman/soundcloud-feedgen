#!/usr/bin/env python
# coding=utf-8

from __future__ import print_function

import datetime
import os
import pytz
import sys
import urllib

from dateutil import parser
from feedgen.feed import FeedGenerator
from soundcloud import Client

OUTPUT_DIR = os.environ['OUTPUT_DIR']
CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']
USERNAME = os.environ['USERNAME']
PASSWORD = os.environ['PASSWORD']
BASE_URL = os.environ['BASE_URL']

TRACKS_DIR = os.path.join(OUTPUT_DIR, 'tracks')

MAX_AGE_DAYS = 7

def download(track):
    if track.downloadable:
        url = track.download_url
    elif track.streamable:
        url = track.stream_url
    else:
        return

    resolved_url = client.get(url, allow_redirects=False)
    temp = os.path.join(TRACKS_DIR, track.permalink + '.download')
    final = os.path.join(TRACKS_DIR, track.permalink)
    
    if not os.path.exists(temp) and not os.path.exists(final):
        # print('🎵 ', track.permalink, end='')
        try:
            urllib.urlretrieve(resolved_url.location, temp)
            os.rename(temp, final)
        except Exception as err:
            print(' 😟')
            print(err)
            if os.path.exists(temp):
                os.remove(temp)
        # else:
        #     print(' 😊')


if not os.path.exists(TRACKS_DIR):
    os.makedirs(TRACKS_DIR)

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

    # print('🎧 ', res.permalink)

    tracks = client.get(res.uri + '/tracks')
    fg.link(href=res.permalink_url, rel='alternate')

    for track in tracks:
        date = parser.parse(track.created_at)
        if (now - date).days > MAX_AGE_DAYS:
            continue

        fe = fg.add_entry()
        fe.id(track.permalink_url)
        fe.title(track.title)
        fe.description(track.description)
        fe.published(date)
        download(track)
        url = BASE_URL + '/tracks/' + track.permalink
        fe.enclosure(url, str(track.original_content_size), 'audio/mpeg')

    fg.rss_file('%s/%s.xml' % (OUTPUT_DIR, res.permalink), pretty=True)
