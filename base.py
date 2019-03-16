import os

from id3 import ID3V1_SIZE, get_id3v1_headers, get_id3v2_tag_header, ID3V2_TAG_HEADER_SIZE, ID3V2Parser

AUDIO_START = 0
AUDIO_END = -1


class ID3V1_TAG(dict):
    def to_bytes_tag(self):
        return b''


class ID3V2_TAG(dict):
    def to_bytes_tag(self):
        return b''


class AudioLoader:
    def __init__(self, path):
        if os.path.exists(path):
            self.path = path
        else:
            raise ValueError('No such file')

    def get_audio_metadata(self):
        id3v1, id3v2 = self.__get_audio_id3()
        audio = AudioMetadata(self.path, id3v1, id3v2)
        return audio

    def __get_audio_id3(self):
        with open(self.path, 'rb') as mp3_file:
            mp3_file.seek(-ID3V1_SIZE, os.SEEK_END)
            id3v1 = None if mp3_file.read(3) != b'TAG' else get_id3v1_headers(mp3_file.read())
            mp3_file.seek(0, os.SEEK_SET)
            id3v2_header_block = mp3_file.read(ID3V2_TAG_HEADER_SIZE)
            mp3_file.seek(0, os.SEEK_SET)
            id3v2_headers = None if id3v2_header_block[:3] != b'ID3' else get_id3v2_tag_header(id3v2_header_block)
            id3v2 = None
            if id3v2_headers:
                parser = ID3V2Parser(mp3_file.read(id3v2_headers['total_size']), id3v2_headers)
                id3v2 = self.__get_audio_id3v2_info(parser.get_tag_frames())
            return id3v1, id3v2

    @staticmethod
    def __get_audio_id3v2_info(id3v2_frames):
        return {}


class AudioMetadata:
    def __init__(self, path, id3v1, id3v2, codec=None):
        self.path = path
        self.id3v1 = id3v1
        self.id3v2 = id3v2
        self.codec = codec

    @property
    def tags(self):
        return self.id3v2 or self.id3v1


class Cursor:
    def __init__(self, audio_metadata, frames):
        self.audio_metadata = audio_metadata
        self.position = 0
        self.frames = frames

    def get_current_frame(self):
        return self.frames[self.position]

    def finished(self):
        return self.position >= len(self.frames) - 1

    def move_next(self):
        if self.finished():
            raise ValueError('Cannot move further')
        self.position += 1

    def move_back(self):
        if self.position <= 0:
            raise ValueError('Cannot move back')
        self.position -= 1

    def set_position(self, position):
        if 0 <= position <= len(self.frames) - 1:
            self.position = position
        else:
            raise ValueError('Out of audio bounds')

    def __iter__(self):
        self.set_position(AUDIO_START)
        return self

    def __next__(self):
        if self.finished():
            raise StopIteration
        else:
            current = self.get_current_frame()
            self.move_next()
            return current


class Player:
    def __init__(self, cursor):
        self.cursor = cursor
        self.stopped = False

    def play(self):
        self.stopped = True
        while not self.cursor.finished() and not self.stopped:
            frame = self.cursor.get_current_frame()
            # some playing operations
            print('frame is being played')
        self.stopped = False

    def stop(self):
        self.stopped = False
