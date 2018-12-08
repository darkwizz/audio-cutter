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
    current_dividend = dividend
    while len(current_dividend) >= len(divisor):
        zeros_for_divisor_count = len(current_dividend) - len(divisor)
        current_divisor = divisor + '0' * zeros_for_divisor_count
        xor_res = int(current_dividend, 2) ^ int(current_divisor, 2)
        current_dividend = bin(xor_res)
    return int(current_dividend, 2)


def get_crc(frame_header):
    return 0


def crc_passed(frame_header, crc_check):
    header_crc = get_crc(frame_header)
    return header_crc == crc_check


path = next(get_audio_path_from_config())
with open(path, 'rb') as mp3_file:
    mp3_size = os.path.getsize(path)
    file_bytes = mp3_file.read()

i = len(file_bytes)  # = 0
while i < len(file_bytes):
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
            if audio_headers_valid(audio_headers_bits, gen_headers_bits):
                frame_header = [byte, second_byte, *rest_bytes]
                if gen_headers_bits['crc'] == 0:
                    crc_check = file_bytes[i:i+2]
                    i += 2
                    if not crc_passed(frame_header, crc_check):
                        continue
                print(frame_header)
    pass

left = '0b11010011101100000'
right = '0b1011'
res = divide_bits(left, right)
assert res == 4