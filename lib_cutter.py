import datetime
import json

import pydub

from base import Cursor, AudioLoader
from utils import get_audio_path_from_config


class LibFramingManager:
    def __init__(self, audio_metadata):
        self.audio_metadata = audio_metadata
        self.frames = []

    def __init_frames(self):
        mp3_seg = pydub.AudioSegment.from_mp3(self.audio_metadata.path)
        self.frames = [mp3_seg[i:i + 1000] for i in range(0, len(mp3_seg), 1000)]

    def get_cursor(self):
        if not self.frames:
            self.__init_frames()
        return Cursor(self.audio_metadata, self.frames)


class LibCutter:
    def __init__(self, cursor):
        self.cursor = cursor

    def get_cut_audio(self, start, end):
        self.cursor.set_position(start)
        cut_part_list = []
        for _ in range(end - start):
            cut_part_list.append(self.cursor.get_current_frame())
            self.cursor.move_next()
        cut_part = sum(cut_part_list)
        return LibAudioCutResult(cut_part, self.cursor.audio_metadata)


class LibAudioCutResult:
    def __init__(self, cut_result, audio_metadata):
        self.cut_result = cut_result
        self.audio_metadata = audio_metadata

    def set_save_path(self, path):
        self.audio_metadata.path = path

    def save_cut_audio(self):
        self.cut_result.export(self.audio_metadata.path, format='mp3', bitrate='320k')


if __name__ == '__main__':
    path = next(get_audio_path_from_config())  # add external file to read
    if not path:
        print("No config file")
        exit()
    loader = AudioLoader(path)
    audio_meta = loader.get_audio_metadata()
    framer = LibFramingManager(audio_meta)
    cursor = framer.get_cursor()
    cutter = LibCutter(cursor)
    result = cutter.get_cut_audio(start=198, end=330)
    result.set_save_path('./Cut.mp3')
    result.save_cut_audio()
