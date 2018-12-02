from main import get_audio_path_from_config
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

def audio_headers_valid(headers):
    return True


path = next(get_audio_path_from_config())
with open(path, 'rb') as mp3_file:
    mp3_size = os.path.getsize(path)
    file_bytes = mp3_file.read()

i = 0
while i < len(file_bytes):
    frame_header = []
    byte = file_bytes[i]
    i += 1
    if byte == 255:
        second_byte = file_bytes[i]
        i += 1
        gen_headers_bits = get_general_headers_bits(second_byte)
        if second_byte & SYNC_MASK == SYNC_MASK and general_headers_valid(gen_headers_bits):
            rest_bytes = file_bytes[i:i+2]
            i += 2
            audio_headers_bits = get_audio_headers_bits(rest_bytes)
            frame_header.extend([byte, second_byte, *rest_bytes])
            print(frame_header)
    pass