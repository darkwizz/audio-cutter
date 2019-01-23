import os


ID3V1_BLOCK_SIZE = 128
GENRES_LIST = [''] * 192
GENRES_LIST[9] = 'Metal'
GENRES_LIST[137] = 'Heavy Metal'


def get_tag_valuable_part(tag_bytes):
    zero_byte_pos = tag_bytes.find(b'\x00')
    return tag_bytes[:zero_byte_pos] if zero_byte_pos >= 0 else tag_bytes


def get_id3v1_headers(id3v1):
    title = get_tag_valuable_part(id3v1[:30])
    artist = get_tag_valuable_part(id3v1[30:60])
    album = get_tag_valuable_part(id3v1[60:90])
    year = get_tag_valuable_part(id3v1[90:94])
    comment = get_tag_valuable_part(id3v1[94:122])
    track_position = id3v1[123]
    genre = id3v1[124]
    return {
        'title': title.decode('ascii'),
        'artist': artist.decode('ascii'),
        'album': album.decode('ascii'),
        'year': year.decode('ascii'),
        'comment': comment.decode('ascii'),
        'track_position': str(track_position),
        'genre': GENRES_LIST[genre]
    }


def get_id3v2_headers(mp3_file):
    return {}


class ID3V1_TAG:
    def __init__(self):
        pass

    def to_bytes_tag(self):
        return b''


class ID3V2_TAG:
    def __init__(self):
        pass

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
            mp3_file.seek(-ID3V1_BLOCK_SIZE, os.SEEK_END)
            id3v1 = None if mp3_file.read(3) != b'TAG' else get_id3v1_headers(mp3_file.read())
            mp3_file.seek(0, os.SEEK_SET)
            id3v2 = None if mp3_file.read(3) != b'ID3' else get_id3v2_headers(mp3_file)
            return id3v1, id3v2


class AudioMetadata:
    def __init__(self, path, id3v1, id3v2):
        self.path = path
        self.id3v1 = id3v1
        self.id3v2 = id3v2


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
