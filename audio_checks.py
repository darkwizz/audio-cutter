from utils import get_audio_path_from_config
import os

SYNC_MASK = 0b11100000
VER_MASK = 0b00011000
LAYER_MASK = 0b00000110
CRC_MASK = 0b00000001
BIT_RATE_MASK = 0b11110000
SAMPLE_RATE_MASK = 0b00001100
PAD_MASK = 0b00000010
CH_MODE_MASK = 0b11000000
MODE_EXT_MASK = 0b00110000
CP_MASK = 0b00001000
MEDIA_ORIG_MASK = 0b00000100
EMPH_MASK = 0b00000011

VERSION_1 = 0b00011000
VERSION_2 = 0b00010000
LAYER_1 = 0b00000110
LAYER_2 = 0b00000100
LAYER_3 = 0b00000010

ID3V1_SIZE = 128
ID3V2_TAG_HEADER_SIZE = 10
GENRES_LIST = ['nope', '', '', '', '', '', '', '', '', 'Metal']


def get_general_headers_bits(header_byte):
    result = {}
    result['version'] = header_byte & VER_MASK
    result['layer'] = header_byte & LAYER_MASK
    result['crc'] = header_byte & CRC_MASK
    return result


def get_audio_headers_bits(header_bytes):
    result = {}
    result['bitrate'] = header_bytes[0] & BIT_RATE_MASK
    result['sample'] = header_bytes[0] & SAMPLE_RATE_MASK
    result['padding'] = header_bytes[0] & PAD_MASK
    result['ch_mode'] = header_bytes[1] & CH_MODE_MASK
    result['mode_ext'] = header_bytes[1] & MODE_EXT_MASK
    result['copyright'] = header_bytes[1] & CP_MASK
    result['media'] = header_bytes[1] & MEDIA_ORIG_MASK
    result['emphasis'] = header_bytes[1] & EMPH_MASK
    return result


def general_headers_valid(headers):
    valid_version = headers['version'] != 0b00001000
    valid_layer = headers['layer'] != 0b00000000
    return valid_layer and valid_version


ALLOWED_BIT_RATES = {
    0b11000000: [32, 48, 56, 64, 80, 96, 112, 128, 160, 192],
    0b01000000: [64, 96, 112, 128, 160, 196, 224, 256, 320, 384],
    0b10000000: [64, 96, 112, 128, 160, 196, 224, 256, 320, 384],
    0b00000000: [64, 96, 112, 128, 160, 196, 224, 256, 320, 384]
}


def get_bitrate(general_headers, bitrate):
    v1_l1_rates = [32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448]
    v1_l2_rates = [32, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384]
    v1_l3_rates = [32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]
    v2_l1_rates = [32, 48, 56, 64, 80, 96, 112, 128, 144, 160, 176, 192, 224, 256]
    v2_l2_l3_rates = [8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160]
    v1l1 = {(i + 1) << 4: val for i, val in enumerate(v1_l1_rates)}
    v1l2 = {(i + 1) << 4: val for i, val in enumerate(v1_l2_rates)}
    v1l3 = {(i + 1) << 4: val for i, val in enumerate(v1_l3_rates)}
    v2l1 = {(i + 1) << 4: val for i, val in enumerate(v2_l1_rates)}
    v2l2l3 = {(i + 1) << 4: val for i, val in enumerate(v2_l2_l3_rates)}
    version = general_headers['version']
    layer = general_headers['layer']
    if version == 0b00011000:
        if layer == 0b00000110:
            return v1l1[bitrate]
        elif layer == 0b00000100:
            return v1l2[bitrate]
        elif layer == 0b00000010:
            return v1l3[bitrate]
    elif version == 0b00010000:
        if layer == 0b00000110:
            return v2l1[bitrate]
        elif layer != 0b00000000:
            return v2l2l3[bitrate]
    return 0


def audio_headers_valid(headers, general_headers):
    bit_rate_valid = headers['bitrate'] != BIT_RATE_MASK
    sample_rate_valid = headers['sample'] != SAMPLE_RATE_MASK
    layer_ii = 0b00000100
    sample_mode_pair_valid = True
    if general_headers['layer'] == layer_ii:
        bit_rate = get_bitrate(general_headers, headers['bitrate'])
        channel_mode = headers['ch_mode']
        sample_mode_pair_valid = bit_rate in ALLOWED_BIT_RATES[channel_mode]
    return bit_rate_valid and sample_rate_valid and sample_mode_pair_valid


def divide_bits(dividend, divisor):
    current_dividend = bin(int(dividend, 2))
    while len(current_dividend) >= len(divisor):
        zeros_for_divisor_count = len(current_dividend) - len(divisor)
        current_divisor = divisor + '0' * zeros_for_divisor_count
        xor_res = int(current_dividend, 2) ^ int(current_divisor, 2)
        current_dividend = bin(xor_res)
    return int(current_dividend, 2)


def get_bytes_in_binary(byte_seq):
    res = ''.join([format(byte, '#010b') for byte in byte_seq]).replace('0b', '')
    return '0b' + res


def get_layer3_for_crc_bits_count(general_headers, audio_headers):
    if general_headers['version'] == VERSION_1:
        bytes_count = 17 if audio_headers['ch_mode'] == 0b11000000 else 32
    else:
        bytes_count = 9 if audio_headers['ch_mode'] == 0b11000000 else 17
    return bytes_count * 8


def get_layer1_for_crc_bits_count(audio_headers):
    subbands_numbers_table = {
        0b00110000: 15,
        0b00100000: 19,
        0b00010000: 23,
        0b00000000: 27
    }
    channels_num = 1 if audio_headers['ch_mode'] == 0b11000000 else 2
    subbands_number = subbands_numbers_table[audio_headers['mode_ext']] if audio_headers['ch_mode'] == 0b01000000 else 32
    return 4 * (channels_num * subbands_number + 32 - subbands_number)


def get_extra_bits_for_crc(general_headers, audio_headers, current_offset, file_bytes):
    if general_headers['layer'] == LAYER_3:
        bits_count = get_layer3_for_crc_bits_count(general_headers, audio_headers)
    elif general_headers['layer'] == LAYER_1:
        bits_count = get_layer1_for_crc_bits_count(audio_headers)
    else:
        return None

    bytes_count = int(bits_count / 8)
    bytes_for_crc = [i for i in file_bytes[current_offset:current_offset + bytes_count]]
    bits_for_crc = get_bytes_in_binary(bytes_for_crc)[2:]
    count_rest = bits_count % 8
    if count_rest != 0:
        rest_byte = file_bytes[current_offset + bytes_count]
        rest_mask = int('0b' + '1' * count_rest, 2) << (8 - count_rest)
        rest = (rest_byte & rest_mask) >> (8 - count_rest)
        bits_for_crc += (format(rest, '#06b')[2:])
    return bits_for_crc


def crc_passed(header_bits_seq, general_headers, audio_headers , crc_check, current_offset, file_bytes):
    # this function does not work correctly, I didn't find yet a proper formula of how to form
    # the checked sequence (division works well [there is an assert in the bottom,
    # but the initial bit sequence is wrong)
    if type(crc_check) != type(''):
        crc_check = get_bytes_in_binary(crc_check)[2:]
    extra_bits = get_extra_bits_for_crc(general_headers, audio_headers, current_offset, file_bytes)
    if extra_bits is None:
        return True
    checked_seq = header_bits_seq + extra_bits + crc_check
    generating_polynom = bin(0x18005)
    header_crc = divide_bits(checked_seq, generating_polynom)
    return header_crc == 0


def split_audio_file(audio_file_bytes):
    """
    splits mp3 file into id3v1, id3v2 and audio stream itself

    :param audio_file_bytes: bytes from .mp3 file
    :return: part with id3v1 tags (without TAG part), id3v2 tags, mp3 bytes themselves
    """

    # [no parser for ID3V2 yet]
    if audio_file_bytes[-ID3V1_SIZE:-ID3V1_SIZE + 3] == b'TAG':
        id3v1 = audio_file_bytes[-ID3V1_SIZE + 3:]
        audio = audio_file_bytes[:-ID3V1_SIZE]
    else:
        id3v1 = b''
        audio = audio_file_bytes
    id3v2 = b''
    if audio_file_bytes[:3] == b'ID3':
        tag_size_bytes = audio_file_bytes[6:10]
        tag_size_bin = ''.join([format(byte, '#09b') for byte in tag_size_bytes]).replace('0b', '')
        tag_size = int(tag_size_bin, 2) + ID3V2_TAG_HEADER_SIZE
        id3v2 = audio_file_bytes[:tag_size]
        audio = audio[tag_size:]
    return id3v1, id3v2, audio


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


if __name__ == "__main__":
    path = next(get_audio_path_from_config())
    if not path or not os.path.exists(path):
        print("No config or no such file")
        exit()

    with open(path, 'rb') as mp3_file:
        mp3_size = os.path.getsize(path)
        file_bytes = mp3_file.read()

    id3v1, id3v2, audio = split_audio_file(file_bytes)
    id3v1_tags = get_id3v1_headers(id3v1)

    i = 0
    # i = len(file_bytes)
    while i < len(audio):
        byte = audio[i]
        i += 1
        if byte == 255:
            second_byte = audio[i]
            i += 1
            gen_headers_bits = get_general_headers_bits(second_byte)
            if second_byte & SYNC_MASK == SYNC_MASK and general_headers_valid(gen_headers_bits):
                rest_bytes = audio[i:i+2]
                i += 2
                audio_headers_bits = get_audio_headers_bits(rest_bytes)
                if audio_headers_valid(audio_headers_bits, gen_headers_bits):
                    frame_header = [byte, second_byte, *rest_bytes]
                    if gen_headers_bits['crc'] == 0:
                        crc_check = audio[i:i+2]
                        i += 2
                        header_seq = get_bytes_in_binary(rest_bytes)
                        if not crc_passed(header_seq, gen_headers_bits, audio_headers_bits, crc_check, i, audio):
                            continue
                    # find frame length
                    print(frame_header)

    left = '0b011010011101100000'
    right = '0b1011'
    res = divide_bits(left, right)
    assert res == 4
    poly = bin(0x18005)
    seq = '0b0110010001000100010100111010110101111011111111111111111111111110011100000010001010001111101001101110000111101001011001100110010101101010011011110011111111111111111111001110111100111010011001101101111001000000011001110010000001100111001011100110011011110011000101000110'
    res = divide_bits(seq, poly)
    print(res)
    poly = bin(0x8005)
    res = divide_bits(seq, poly)
    print(res)