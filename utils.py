import datetime
import os


def get_audio_path_from_config():
    config_path = 'mp3-path.conf'
    if not os.path.exists(config_path):
        yield None

    with open(config_path) as config_file:
        for path in config_file:
            yield path.strip()


def split_audio_file(audio_file_bytes):
    """
    splits mp3 file into id3v1, id3v2 and audio stream itself

    :param audio_file_bytes: bytes from .mp3 file
    :return: part with id3v1 tags (without TAG part), id3v2 tags, mp3 bytes themselves
    """
    from id3 import ID3V1_SIZE, get_id3v2_tag_header

    if audio_file_bytes[-ID3V1_SIZE:-ID3V1_SIZE + 3] == b'TAG':
        id3v1 = audio_file_bytes[-ID3V1_SIZE + 3:]
        audio = audio_file_bytes[:-ID3V1_SIZE]
    else:
        id3v1 = b''
        audio = audio_file_bytes
    id3v2 = b''
    if audio_file_bytes[:3] == b'ID3':
        tag_header = get_id3v2_tag_header(audio_file_bytes)
        tag_size = tag_header['total_size']
        id3v2 = audio_file_bytes[:tag_size]
        audio = audio[tag_size:]
    return id3v1, id3v2, audio


def get_timedelta_from_datetime(date_time):
    return datetime.timedelta(hours=date_time.hour,
                              minutes=date_time.minute,
                              seconds=date_time.second)
