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
from mimetypes import guess_type
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
        file_name = track.permalink + '.' + track.original_format
    elif track.streamable:
        url = track.stream_url
        file_name = track.permalink + '.mp3'
    else:
        return

    resolved_url = client.get(url, allow_redirects=False)
    temp = os.path.join(TRACKS_DIR, file_name + '.download')
    final = os.path.join(TRACKS_DIR, file_name)
    
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

    return file_name


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

    tracks = client.get(res.uri + '/tracks', limit=200)
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
        file_name = download(track)
        url = BASE_URL + '/tracks/' + file_name
        mime_type = guess_type(file_name)[0]
        fe.enclosure(url, str(track.original_content_size), mime_type)

    fg.rss_file('%s/%s.xml' % (OUTPUT_DIR, res.permalink), pretty=True)
