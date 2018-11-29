import os


class AudioLoader:
    def __init__(self, path='', bytes=[]):
        if not bytes and not path:
            raise ValueError('must be one of parameters')
        self.path = path
        self.bytes = bytes

    def __get_info_from_bytes(self, bytes):
        return {}

    def get_audio(self):
        if self.bytes:
            info = self.__get_info_from_bytes(self.bytes)
            return Audio(self.bytes, info)
        if not os.path.exists(self.path):
            raise ValueError('No audio with such path')
        with open(self.path, 'rb') as audio_file:
            audio = audio_file.read()
            info = self.__get_info_from_bytes(audio)
            return Audio(audio, info)


class Audio:
    def __init__(self, audio, info):
        self.audio = audio
        self.frame_size = info.get('frame_size', 4)
        self.duration = info.get('duration', int(len(audio) / float(self.frame_size)))


class FramingManager:
    def __init__(self, audio):
        self.audio = audio

    def get_cursor(self):
        return Cursor(self.audio)


class Cursor:
    def __init__(self, audio):
        self.audio = audio
        self.position = 0
        step = audio.frame_size
        self.frames = [audio.audio[i * step:i * step + step] for i in range(audio.duration)]

    def get_current_frame(self):
        return self.frames[self.position]

    def finished(self):
        return self.position == self.audio.duration - 1

    def move_next(self):
        if self.finished():
            raise ValueError('Cannot move further')
        self.position += 1

    def move_back(self):
        if self.position == 0:
            raise ValueError('Cannot move back')
        self.position -= 1

    def set_position(self, position):
        if 0 <= position <= self.audio.duration - 1:
            self.position = position
        else:
            raise ValueError('Out of audio bounds')


class Cutter:
    def __init__(self, cursor):
        self.cursor = cursor

    def get_cut_audio(self, start, end):
        self.cursor.set_position(start)
        result = []
        for _ in range(end - start):
            result.append(self.cursor.get_current_frame())
            self.cursor.move_next()
        return result


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


def get_audio_path_from_config():
    config_path = 'mp3-path.conf'
    if not os.path.exists(config_path):
        return 'path-not-existing'

    with open(config_path) as config_file:
        for path in config_file:
            yield path.strip()

if __name__ == '__main__':
    path = next(get_audio_path_from_config())  # add external file to read
    loader = AudioLoader(path)
    audio = loader.get_audio()
    framer = FramingManager(audio)
    cursor = framer.get_cursor()
    cutter = Cutter(cursor)
    result = cutter.get_cut_audio(start=15, end=75)
    print(result)
