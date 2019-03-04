# UI will be here - pass the .json config file + listen to audio + something else
import datetime
import json

import pydub

from utils import get_timedelta_from_datetime

if __name__ == '__main__':
    with open('cut_config.json') as config:
        songs_config = json.load(config)
    for song_config in songs_config:
        if song_config['codec'] is not None:
            segment = pydub.AudioSegment.from_file(song_config['path'], codec=song_config['codec'])
        else:
            segment = pydub.AudioSegment.from_mp3(song_config['path'])
        for track in song_config['tracks']:
            start, end, name = tuple(track.split('|'))
            start_time = datetime.datetime.strptime(start, '%H:%M:%S')
            end_time = datetime.datetime.strptime(end, '%H:%M:%S')
            start_seconds = get_timedelta_from_datetime(start_time).total_seconds()
            end_seconds = get_timedelta_from_datetime(end_time).total_seconds()
            tags = song_config['tags']
            tags['title'] = name
            save_path = tags['artist'] + ' - ' + name + '.mp3'
            song = segment[start_seconds * 1000: end_seconds * 1000]
            loud = song_config['loud']
            song = song + loud
            song.export(save_path, format='mp3', bitrate='320k', tags=tags)
            print(name)
    # print(segment)
