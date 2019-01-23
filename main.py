import os

from base import AudioLoader
from lib_cutter import LibFramingManager, LibCutter


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
    audio_meta = loader.get_audio_metadata()
    framer = LibFramingManager(audio_meta)
    cursor = framer.get_cursor()
    cutter = LibCutter(cursor)
    result = cutter.get_cut_audio(start=198, end=330)
    result.set_save_path('./Cut.mp3')
    result.save_cut_audio()
