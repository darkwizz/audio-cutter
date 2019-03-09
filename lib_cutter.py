import pydub

from base import Cursor, AudioLoader, AUDIO_START
from utils import get_audio_path_from_config


class LibFramingManager:
    def __init__(self, audio_metadata):
        self.audio_metadata = audio_metadata
        self.frames = []

    def __init_frames(self):
        if self.audio_metadata.codec in ['mp3', None]:
            mp3_seg = pydub.AudioSegment.from_mp3(self.audio_metadata.path)
        else:
            mp3_seg = pydub.AudioSegment.from_file(self.audio_metadata.path, codec=self.audio_metadata.codec)
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
        cut_cursor = Cursor(self.cursor.audio_metadata, cut_part_list)
        return cut_cursor


class LibAudioVolumeSetter:
    def __init__(self, cursor):
        self.cursor = cursor

    def get_volumed_audio(self, volume):
        self.cursor.set_position(AUDIO_START)
        volumed_frames = [frame + volume for frame in self.cursor]
        return Cursor(self.cursor.audio_metadata, volumed_frames)


class LibAudioSaver:
    def __init__(self, cursor, audio_metadata):
        self.cursor = cursor
        self.path = audio_metadata.path
        self.tags = audio_metadata.tags

    def set_save_path(self, path):
        self.path = path

    def set_tags(self, **tags):
        self.tags = tags

    def save_audio(self):
        audio_to_save = sum(self.cursor.frames)
        audio_to_save.export(self.path, format='mp3', bitrate='320k', tags=self.tags)


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
    cut_audio_cursor = cutter.get_cut_audio(start=198, end=330)
    volumer = LibAudioVolumeSetter(cut_audio_cursor)
    volumed_audio = volumer.get_volumed_audio(8)
    saver = LibAudioSaver(volumed_audio, volumed_audio.audio_metadata)
    saver.set_save_path('./Cut.mp3')
    saver.save_audio()
