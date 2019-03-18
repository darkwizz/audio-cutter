ID3V1_SIZE = 128

ID3V2_TAG_HEADER_SIZE = 10
ID3V2_TAG_FOOTER_SIZE = 10
ID3V2_TAG_EXT_HEADER_SIZE_FIELD_LENGTH = 4
ID3V2_TAG_EXT_HEADER_FLAGS_FIELD_LENGTH = 2
ID3V2_TAG_EXT_HEADER_PAD_SIZE_FIELD_LENGTH = 4

ID3V23_TAG_EXT_HEADER_CRC_SIZE = 4

ID3V24_TAG_EXT_HEADER_CRC_SIZE = 5

TAG_UNSYNC = 0b10000000
TAG_EXT_HEADER = 0b01000000
TAG_IS_DEV = 0b00100000
TAG_HAS_FOOTER = 0b00010000

TAG23_EXT_HEAD_CRC = 0b10000000

TAG24_EXT_HEAD_IS_UPDATE = 0b01000000
TAG24_EXT_HEAD_CRC = 0b00100000
TAG24_EXT_HEAD_FORMAT = 0b00010000
TAG24_EXT_HEAD_TAG_SIZE_RESTRICTIONS = 0b11000000
TAG24_EXT_HEAD_TEXT_ENCODING_RESTRICTIONS = 0b00100000
TAG24_EXT_HEAD_TEXT_LENGTH_RESTRICTIONS = 0b00011000
TAG24_EXT_HEAD_IMAGE_ENCODING_RESTRICTIONS = 0b00000100
TAG24_EXT_HEAD_IMAGE_SIZE_RESTRICTIONS = 0b00000011

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
    tag_size = get_syncsafe_bytes_int_value(tag_size_bytes)
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


def get_id3v23_extended_tag_header(tag_bytes, tag_header):
    if not tag_header['flags']['ext_head']:
        return {}
    block_start = ID3V2_TAG_HEADER_SIZE
    size_field_end = ID3V2_TAG_HEADER_SIZE + ID3V2_TAG_EXT_HEADER_SIZE_FIELD_LENGTH
    block_size_bytes = tag_bytes[block_start:size_field_end]
    block_size = int(block_size_bytes.hex(), 16)
    extended_header_bytes = tag_bytes[block_start:block_start + block_size]

    flags_field_end = size_field_end + ID3V2_TAG_EXT_HEADER_FLAGS_FIELD_LENGTH
    flags_bytes = extended_header_bytes[ID3V2_TAG_EXT_HEADER_SIZE_FIELD_LENGTH:flags_field_end]
    padding_size_bytes = extended_header_bytes[flags_field_end:]
    flags = {
        'crc': int(flags_bytes.hex(), 16) & TAG23_EXT_HEAD_CRC
    }
    padding_size = int(padding_size_bytes.hex(), 16)

    ext_header = {
        'block_size': block_size,
        'flags': flags,
        'padding_size': padding_size
    }

    if flags['crc']:
        crc_block_start = block_start + block_size
        crc_block_end = crc_block_start + ID3V23_TAG_EXT_HEADER_CRC_SIZE
        crc_block = tag_bytes[crc_block_start:crc_block_end]
        ext_header['crc_block'] = crc_block

    return ext_header


def get_id3v24_ext_flags(flags_int):
    return {
        'is_update': flags_int & TAG24_EXT_HEAD_IS_UPDATE,
        'crc': flags_int & TAG24_EXT_HEAD_CRC,
        'format': flags_int & TAG24_EXT_HEAD_FORMAT
    }


def get_id3v24_ext_extra_data(tag_bytes, block_size, flags):
    result = {}
    ext_head_end = ID3V2_TAG_HEADER_SIZE + block_size
    format_byte_pos = ext_head_end
    if not flags['crc']:
        result['crc'] = {}
    else:
        crc_end = ext_head_end + ID3V24_TAG_EXT_HEADER_CRC_SIZE
        result['crc'] = tag_bytes[ext_head_end:crc_end]
        format_byte_pos = crc_end
    if not flags['format']:
        result['format'] = {}
    else:
        format_byte = tag_bytes[format_byte_pos]
        result['format'] = {
            'tag_size': format_byte & TAG24_EXT_HEAD_TAG_SIZE_RESTRICTIONS,
            'text_encoding': format_byte & TAG24_EXT_HEAD_TEXT_ENCODING_RESTRICTIONS,
            'text_length': format_byte & TAG24_EXT_HEAD_TEXT_LENGTH_RESTRICTIONS,
            'image_encoding': format_byte & TAG24_EXT_HEAD_IMAGE_ENCODING_RESTRICTIONS,
            'image_size': format_byte & TAG24_EXT_HEAD_IMAGE_SIZE_RESTRICTIONS,
        }
    return result


def get_id3v24_extended_tag_header(tag_bytes, tag_header):
    if not tag_header['flags']['ext_head']:
        return {}

    block_start = ID3V2_TAG_HEADER_SIZE
    size_field_end = ID3V2_TAG_HEADER_SIZE + ID3V2_TAG_EXT_HEADER_SIZE_FIELD_LENGTH
    block_size_bytes = tag_bytes[block_start:size_field_end]
    block_size = get_syncsafe_bytes_int_value(block_size_bytes)
    ext_head_bytes = tag_bytes[block_start:block_start + block_size]
    flags_size = 1
    flags_field_position = 5
    flags_int = ext_head_bytes[flags_field_position]
    flags = get_id3v24_ext_flags(flags_int)
    extra_data = get_id3v24_ext_extra_data(tag_bytes, block_size, flags)

    return {
        'block_size': block_size,
        'flags': flags,
        'flags_size': flags_size,
        'extra_data': extra_data
    }


class ID3V2Parser:
    def __init__(self, id3v2_bytes, tag_header=None):
        if id3v2_bytes[:3] != b'ID3':
            raise ValueError('This is not an ID3V2 tag')
        self.tag_header = get_id3v2_tag_header(id3v2_bytes) if not tag_header else tag_header
        self.tag_bytes = id3v2_bytes[:self.tag_header['total_size']]
        self.get_frames = get_id3v24_frames if self.tag_header['version'][0] == 4 else get_id3v23_frames
        self.get_extended_header = get_id3v24_extended_tag_header if self.tag_header['version'][0] == 4 else \
            get_id3v23_extended_tag_header

    def get_tag_frames(self):
        return self.get_frames(self.tag_bytes, self.tag_header, self.get_extended_tag_header())

    def get_extended_tag_header(self):
        return self.get_extended_header(self.tag_bytes, self.tag_header)


if __name__ == '__main__':
    from utils import get_audio_path_from_config, get_syncsafe_bytes_int_value

    path = next(get_audio_path_from_config())  # add external file to read
    if not path:
        print("No config file")
        exit()
    with open(path, 'rb') as mp3_file:
        parser = ID3V2Parser(mp3_file.read())
        ext_head = parser.get_extended_tag_header()
    print(ext_head)
