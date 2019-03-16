
ID3V1_SIZE = 128
ID3V2_TAG_HEADER_SIZE = 10
ID3V2_TAG_FOOTER_SIZE = 10
TAG_UNSYNC = 0b10000000
TAG_EXT_HEADER = 0b01000000
TAG_IS_DEV = 0b00100000
TAG_HAS_FOOTER = 0b00010000
GENRES_LIST = {
    9: 'Metal',
    13: 'Pop',
    137: 'Heavy Metal'
}


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


def get_id3v2_tag_flags(flags_byte):
    flags = {
        'unsync': flags_byte & TAG_UNSYNC,
        'ext_head': flags_byte & TAG_EXT_HEADER,
        'is_dev': flags_byte & TAG_IS_DEV,
        'has_footer': flags_byte & TAG_HAS_FOOTER,  # is applicable since 2.4.0, but for lesser versions it doesn't break
    }
    return flags


def get_id3v2_total_size(tag_size, flags):
    result = tag_size + ID3V2_TAG_HEADER_SIZE
    if flags['has_footer']:
        result += ID3V2_TAG_FOOTER_SIZE
    return result


def get_id3v2_tag_header(id3v2):
    tag_header_bytes = id3v2[:ID3V2_TAG_HEADER_SIZE]
    id3version = tag_header_bytes[3:5]
    flags_byte = tag_header_bytes[5]
    flags = get_id3v2_tag_flags(flags_byte)
    tag_size_bytes = tag_header_bytes[6:]
    tag_size_bin = ''.join([format(byte, '#09b') for byte in tag_size_bytes]).replace('0b', '')
    tag_size = int(tag_size_bin, 2)
    total_size = get_id3v2_total_size(tag_size, flags)
    tag_header = {
        'version': (id3version[0], id3version[1]),
        'tag_size': tag_size,
        'total_size': total_size,
        'flags': flags
    }
    return tag_header


def get_id3v24_frames(tag_bytes, tag_header, extended_tag_header):
    return []


def get_id3v23_frames(tag_bytes, tag_header, extended_tag_header):
    return []


def get_id3v2_extended_tag_header(tag_bytes, tag_header):
    if not tag_header['flags']['ext_head']:
        return {}
    return {}


class ID3V2Parser:
    def __init__(self, id3v2_bytes, tag_header=None):
        self.tag_header = get_id3v2_tag_header(id3v2_bytes) if not tag_header else tag_header
        self.tag_bytes = id3v2_bytes
        self.get_frames = get_id3v24_frames if self.tag_header['version'][0] == 4 else get_id3v23_frames
        self.extended_tag_header = get_id3v2_extended_tag_header(id3v2_bytes, self.tag_header)

    def get_tag_frames(self):
        return self.get_frames(self.tag_bytes, self.tag_header, self.tag_header)
