import datetime
import os


def get_audio_path_from_config():
    config_path = 'mp3-path.conf'
    if not os.path.exists(config_path):
        yield None

    with open(config_path) as config_file:
        for path in config_file:
            yield path.strip()


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


def get_timedelta_from_datetime(date_time):
    return datetime.timedelta(hours=date_time.hour,
                              minutes=date_time.minute,
                              seconds=date_time.second)
