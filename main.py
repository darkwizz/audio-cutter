# UI will be here - pass the .json config file + listen to audio + something else
import datetime
import json

import os
import pydub

from base import AudioLoader
from lib_cutter import LibCutter, LibAudioVolumeSetter, LibFramingManager, LibAudioSaver
from utils import get_timedelta_from_datetime


class AudioEditorFactory:
    CUSTOM = 'custom'
    LIB = 'lib'

    __types = {
        LIB: {
            'cutter': LibCutter,
            'volumer': LibAudioVolumeSetter,
            'framer': LibFramingManager,
            'saver': LibAudioSaver
        },
    }

    @staticmethod
    def get_audio_cutter(implementation, cursor):
        return AudioEditorFactory.__types[implementation]['cutter'](cursor)

    @staticmethod
    def get_audio_volume_setter(implementation, cursor):
        return AudioEditorFactory.__types[implementation]['volumer'](cursor)

    @staticmethod
    def get_audio_framing_manager(implementation, audio_metadata):
        return AudioEditorFactory.__types[implementation]['framer'](audio_metadata)

    @staticmethod
    def get_audio_saver(implementation, cursor, audio_metadata):
        return AudioEditorFactory.__types[implementation]['saver'](cursor, audio_metadata)


if __name__ == '__main__':
    config_path = 'cut_config.json'
    if not os.path.exists(config_path):
        print('No config file')
        exit()

    with open(config_path) as config:
        songs_config = json.load(config)
    for song_config in songs_config:
        loader = AudioLoader(song_config['path'])
        audio_meta = loader.get_audio_metadata()
        audio_meta.codec = song_config['codec']
        framer = AudioEditorFactory.get_audio_framing_manager(AudioEditorFactory.LIB, audio_meta)
        tags = song_config['tags']
        loud = song_config['loud']
        cursor = framer.get_cursor()

        # if song_config['codec'] is not None:
        #     segment = pydub.AudioSegment.from_file(song_config['path'], codec=song_config['codec'])
        # else:
        #     segment = pydub.AudioSegment.from_mp3(song_config['path'])
        for track in song_config['tracks']:
            start, end, name = tuple(track.split('|'))
            start_time = datetime.datetime.strptime(start, '%H:%M:%S')
            end_time = datetime.datetime.strptime(end, '%H:%M:%S')
            start_seconds = int(get_timedelta_from_datetime(start_time).total_seconds())
            end_seconds = int(get_timedelta_from_datetime(end_time).total_seconds())
            # tags = song_config['tags']
            # tags['title'] = name
            save_path = tags['artist'] + ' - ' + name + '.mp3'
            cutter = AudioEditorFactory.get_audio_cutter(AudioEditorFactory.LIB, cursor)
            cut_audio = cutter.get_cut_audio(start_seconds, end_seconds)
            volumer = AudioEditorFactory.get_audio_volume_setter(AudioEditorFactory.LIB, cut_audio)
            volumed_audio = volumer.get_volumed_audio(loud)
            saver = AudioEditorFactory.get_audio_saver(AudioEditorFactory.LIB, volumed_audio, volumed_audio.audio_metadata)
            track_tags = dict(tags)
            track_tags['title'] = name
            saver.set_tags(**track_tags)
            saver.set_save_path(save_path)
            saver.save_cut_audio()
            print(name)
    print("Success")
