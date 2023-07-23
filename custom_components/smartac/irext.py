TAG_AC_BOOT_CODE = 1
TAG_AC_ZERO = 2
TAG_AC_ONE = 3
TAG_AC_DELAY_CODE = 4
TAG_AC_FRAME_LENGTH = 5
TAG_AC_ENDIAN = 6
TAG_AC_LAST_BIT = 7

TAG_AC_POWER_1 = 21
TAG_AC_DEFAULT_CODE = 22
TAG_AC_TEMP_1 = 23
TAG_AC_MODE_1 = 24
TAG_AC_SPEED_1 = 25
TAG_AC_SWING_1 = 26
TAG_AC_CHECKSUM_TYPE = 27
TAG_AC_SOLO_FUNCTION = 28
TAG_AC_FUNCTION_1 = 29
TAG_AC_TEMP_2 = 30
TAG_AC_MODE_2 = 31
TAG_AC_SPEED_2 = 32
TAG_AC_SWING_2 = 33
TAG_AC_FUNCTION_2 = 34

TAG_AC_BAN_FUNCTION_IN_COOL_MODE = 41
TAG_AC_BAN_FUNCTION_IN_HEAT_MODE = 42
TAG_AC_BAN_FUNCTION_IN_AUTO_MODE = 43
TAG_AC_BAN_FUNCTION_IN_FAN_MODE = 44
TAG_AC_BAN_FUNCTION_IN_DRY_MODE = 45
TAG_AC_SWING_INFO = 46
TAG_AC_REPEAT_TIMES = 47
TAG_AC_BIT_NUM = 48
tags = [
    TAG_AC_BOOT_CODE, TAG_AC_ZERO, TAG_AC_ONE, TAG_AC_DELAY_CODE, TAG_AC_FRAME_LENGTH, TAG_AC_ENDIAN, TAG_AC_LAST_BIT,
    TAG_AC_POWER_1, TAG_AC_DEFAULT_CODE, TAG_AC_TEMP_1, TAG_AC_MODE_1, TAG_AC_SPEED_1, TAG_AC_SWING_1, TAG_AC_CHECKSUM_TYPE,
    TAG_AC_SOLO_FUNCTION, TAG_AC_FUNCTION_1, TAG_AC_TEMP_2, TAG_AC_MODE_2, TAG_AC_SPEED_2, TAG_AC_SWING_2, TAG_AC_FUNCTION_2,
    TAG_AC_BAN_FUNCTION_IN_COOL_MODE, TAG_AC_BAN_FUNCTION_IN_HEAT_MODE, TAG_AC_BAN_FUNCTION_IN_AUTO_MODE, TAG_AC_BAN_FUNCTION_IN_FAN_MODE,
    TAG_AC_BAN_FUNCTION_IN_DRY_MODE, TAG_AC_SWING_INFO, TAG_AC_REPEAT_TIMES, TAG_AC_BIT_NUM
]

CHECKSUM_TYPE_BYTE = 1
CHECKSUM_TYPE_BYTE_INVERSE = 2
CHECKSUM_TYPE_HALF_BYTE = 3
CHECKSUM_TYPE_HALF_BYTE_INVERSE = 4
CHECKSUM_TYPE_SPEC_HALF_BYTE = 5
CHECKSUM_TYPE_SPEC_HALF_BYTE_INVERSE = 6
CHECKSUM_TYPE_SPEC_HALF_BYTE_ONE_BYTE = 7
CHECKSUM_TYPE_SPEC_HALF_BYTE_INVERSE_ONE_BYTE = 8

AC_FUNCTION_POWER = 1
AC_FUNCTION_MODE = 2
AC_FUNCTION_TEMPERATURE_UP = 3
AC_FUNCTION_TEMPERATURE_DOWN = 4
AC_FUNCTION_WIND_SPEED = 5
AC_FUNCTION_WIND_SWING = 6
AC_FUNCTION_WIND_FIX = 7

MODE_COOL = 0
MODE_HEAT = 1
MODE_AUTO = 2
MODE_FAN = 3
MODE_DRY = 4

SPEED_AUTO = 0
SPEED_LOW = 1
SPEED_MEDIUM = 2
SPEED_HIGH = 3
speeds = [SPEED_AUTO, SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH]

POWER_ON = 0
POWER_OFF = 1

modes = [MODE_COOL, MODE_HEAT, MODE_AUTO, MODE_FAN, MODE_DRY]

SWING_ON = 0
SWING_OFF = 1
swing_modes = [SWING_ON, SWING_OFF]


class AC:

    def __init__(self, data) -> None:

        tag_count = data[0]  # must be 29

        data = data[1:]
        offsets = []
        for i in range(0, tag_count):
            offsets.append(int.from_bytes(
                data[i*2:i*2+2], "little", signed=False))

        data = data[tag_count * 2:]
        tags_data = {}
        for i in range(0, tag_count):
            if offsets[i] == 0xffff:
                tags_data[tags[i]] = b''
                continue
            for j in range(i + 1, tag_count + 1):
                if j == tag_count:
                    tags_data[tags[i]] = data[offsets[i]:]
                    break
                if offsets[j] != 0xffff:
                    tags_data[tags[i]] = data[offsets[i]:offsets[j]]
                    break

        self._tags = tags_data

        # '0' = no, '1' = swing only, '1,2,3'=normal  , ''=normal & mode=2 & enable swing1 swing2
        self._swing_mode = tags_data[TAG_AC_SWING_INFO].decode()
        self._swing1 = self._parse_data(tags_data.get(TAG_AC_SWING_1).decode())
        self._swing2 = self._parse_data(tags_data.get(TAG_AC_SWING_2).decode())
        self._mode1 = self._parse_data(tags_data.get(TAG_AC_MODE_1).decode())
        self._mode2 = self._parse_data(tags_data.get(TAG_AC_MODE_2).decode())
        self._power1 = self._parse_data(tags_data.get(TAG_AC_POWER_1).decode())

        # default code
        default_code = bytes.fromhex(
            tags_data.get(TAG_AC_DEFAULT_CODE).decode())
        self._default_code = default_code[1:default_code[0] + 1]

        self._n_mode = []
        # 'NA' = disable, 'S'or's' = all speed, 'T'or't'=all temp, '&16,17,18'>disable 16,17,18
        self._n_mode.append(self._parse_n_mode(
            tags_data[TAG_AC_BAN_FUNCTION_IN_COOL_MODE].decode()))
        self._n_mode.append(self._parse_n_mode(
            tags_data[TAG_AC_BAN_FUNCTION_IN_HEAT_MODE].decode()))
        self._n_mode.append(self._parse_n_mode(
            tags_data[TAG_AC_BAN_FUNCTION_IN_AUTO_MODE].decode()))
        self._n_mode.append(self._parse_n_mode(
            tags_data[TAG_AC_BAN_FUNCTION_IN_FAN_MODE].decode()))
        self._n_mode.append(self._parse_n_mode(
            tags_data[TAG_AC_BAN_FUNCTION_IN_DRY_MODE].decode()))

        # temp1
        temp1_hex = tags_data.get(TAG_AC_TEMP_1).decode()
        self._temp1 = []
        if temp1_hex != '':
            temp1_data = bytes.fromhex(temp1_hex)
            seg_len = temp1_data[0]
            if seg_len != len(temp1_data) - 1:
                self._temp1_type = 'static'
                self._temp1 = self._parse_data(temp1_hex)
            else:
                self._temp1_type = 'dynamic'
                for index in range(0, 15):
                    segment = []
                    for i in range(1, seg_len, 2):
                        segment.append(temp1_data[i])
                        segment.append(temp1_data[i+1]*index)
                    self._temp1.append(segment)
        # temp1

        # temp2
        temp2_hex = tags_data.get(TAG_AC_TEMP_2).decode()
        self._temp2 = []
        if temp2_hex != '':
            temp2_data = bytes.fromhex(temp2_hex)
            seg_len = temp2_data[0]
            if seg_len != len(temp2_data) - 1:
                self._temp2_type = 'static'
                self._temp2 = self._parse_data(temp2_hex)
            else:
                self._temp2_type = 'dynamic'
                for index in range(0, 15):
                    segment = []
                    for i in range(2, seg_len, 3):
                        segment.append(temp2_data[i-1])
                        segment.append(temp2_data[i])
                        segment.append(temp2_data[i+1]*index)
                    self._temp2.append(segment)
        # temp2 end

        self._speed1 = self._parse_data(tags_data.get(TAG_AC_SPEED_1).decode())
        self._speed2 = self._parse_data(tags_data.get(TAG_AC_SPEED_2).decode())

        # funtion1
        self._function1 = {}
        function1_hex = tags_data.get(TAG_AC_FUNCTION_1).decode()
        function1_parsed = self._parse_data(function1_hex)
        for f in function1_parsed:
            self._function1[f[0]] = f[1:]
        # function1 end

        # function2
        self._function2 = {}
        function2_hex = tags_data.get(TAG_AC_FUNCTION_2).decode()
        function2_parsed = self._parse_data(function2_hex)
        for f in function2_parsed:
            self._function2[f[0]] = f[1:]
        # function2 end

        self._solo_function = set()
        # [len][function1][function2]
        solo_function_hex = tags_data.get(TAG_AC_SOLO_FUNCTION).decode()
        if len(solo_function_hex) >= 4:
            self._solo_function = {
                int(func) for func in bytes.fromhex(solo_function_hex)[1:]}

        self._frame_len = tags_data.get(TAG_AC_FRAME_LENGTH).decode()

        self._zero = []
        for time in tags_data.get(TAG_AC_ZERO).decode().split(','):
            if time:
                self._zero.append(int(time))

        self._one = []
        for time in tags_data.get(TAG_AC_ONE).decode().split(','):
            if time:
                self._one.append(int(time))

        self._boot_code = []
        for time in tags_data.get(TAG_AC_BOOT_CODE).decode().split(','):
            if time:
                self._boot_code.append(int(time))

        self._repeat_time = 1
        if tags_data.get(TAG_AC_REPEAT_TIMES):
            self._repeat_time = int(
                tags_data.get(TAG_AC_REPEAT_TIMES).decode())

        self._bit_num = []
        for sub in tags_data.get(TAG_AC_BIT_NUM).decode().split('|'):
            item = sub.split('&')
            if len(item) < 2:
                continue
            pos = int(item[0])
            if pos == -1:
                pos = len(self._default_code) - 1
            self._bit_num.append({'pos': pos, 'bits': int(item[1])})

        self._endian = 0
        if tags_data.get(TAG_AC_ENDIAN):
            self._endian = int(tags_data.get(TAG_AC_ENDIAN).decode())

        # delay code
        self._delay = []
        for sub in tags_data.get(TAG_AC_DELAY_CODE).decode().split('|'):
            delay = sub.split('&')
            if len(delay) < 2:
                continue
            self._delay.append({'pos': int(delay[0]), 'time': [
                               int(t) % 65536 for t in delay[1].split(',')]})

        self._last_bit = int(tags_data.get(TAG_AC_LAST_BIT).decode()) if tags_data.get(
            TAG_AC_LAST_BIT) else 0
        # delay code end

        self._checksum = []
        for t_hex in tags_data.get(TAG_AC_CHECKSUM_TYPE).decode().split('|'):
            checksum_data = bytes.fromhex(t_hex)
            if len(checksum_data) <= 1:
                continue
            checksum_len = checksum_data[0]
            checksum_type = checksum_data[1]
            checksum = {'type': checksum_type}
            if checksum_type >= 1 and checksum_type <= 4:
                checksum['start_byte_pos'] = checksum_data[2]
                checksum['end_byte_pos'] = checksum_data[3]
                checksum['checksum_byte_pos'] = checksum_data[4]
                checksum['checksum_plus'] = checksum_data[5] if checksum_len > 4 else 0
            elif checksum_type >= 5 and checksum_type <= 8:
                checksum['start_byte_pos'] = 0
                checksum['end_byte_pos'] = 0
                checksum['checksum_byte_pos'] = checksum_data[2]
                checksum['checksum_plus'] = checksum_data[3]
                checksum['spec_pos'] = checksum_data[4:]
            self._checksum.append(checksum)

    def ir_decode(self, power, temperature, mode, speed, swing=SWING_ON, dir=0, function_code=1):
        ir_hex = bytearray(self._default_code)
        # apply power
        if len(self._power1) > power:
            ir_hex = self._apply_type_1(ir_hex, self._power1[power])
        if power == POWER_ON:
            # apply mode:
            if AC_FUNCTION_MODE not in self._solo_function:
                if self._mode1:
                    ir_hex = self._apply_type_1(ir_hex, self._mode1[mode])
                elif self._mode2:
                    ir_hex = self._apply_type_2(ir_hex, self._mode2[mode])
            # apply speed
            if AC_FUNCTION_WIND_SPEED not in self._solo_function:
                if self._speed1:
                    ir_hex = self._apply_type_1(ir_hex, self._speed1[speed])
                elif self._speed2:
                    ir_hex = self._apply_type_2(ir_hex, self._speed2[speed])
            # apply swing
            if AC_FUNCTION_WIND_SWING not in self._solo_function and AC_FUNCTION_WIND_FIX not in self._solo_function:
                if self._swing1:
                    ir_hex = self._apply_type_1(ir_hex, self._swing1[swing])
                elif self._swing2:
                    ir_hex = self._apply_type_2(ir_hex, self._swing2[swing])
            # apply temperature
            if AC_FUNCTION_TEMPERATURE_UP not in self._solo_function and AC_FUNCTION_TEMPERATURE_DOWN not in self._solo_function:
                if self._temp1:
                    ir_hex = self._apply_type_1(
                        ir_hex, self._temp1[temperature - 16], self._temp1_type == 'dynamic')
                elif self._temp2:
                    ir_hex = self._apply_type_2(
                        ir_hex, self._temp2[temperature - 16], self._temp2_type == 'dynamic')
        # apply function
        if function_code in self._function1:
            ir_hex = self._apply_type_1(ir_hex, self._function1[function_code])
        elif function_code in self._function2:
            ir_hex = self._apply_type_2(ir_hex, self._function2[function_code])
        # aplly checksum
        for checksum in self._checksum:
            value = 0
            if checksum['type'] == CHECKSUM_TYPE_BYTE or checksum['type'] == CHECKSUM_TYPE_BYTE_INVERSE:
                for i in range(checksum['start_byte_pos'], checksum['end_byte_pos']):
                    value += ir_hex[i]
                value += checksum['checksum_plus']
                value %= 256
                value = ~value + \
                    256 if checksum['type'] == CHECKSUM_TYPE_BYTE_INVERSE else value
                ir_hex[checksum['checksum_byte_pos']] = value % 256
            elif checksum['type'] == CHECKSUM_TYPE_HALF_BYTE or checksum['type'] == CHECKSUM_TYPE_HALF_BYTE_INVERSE:
                for i in range(checksum['start_byte_pos'], checksum['end_byte_pos']):
                    value += (ir_hex[i] >> 4) + (ir_hex[i] & 0x0F)
                value += checksum['checksum_plus']
                value %= 256
                value = ~value + \
                    256 if checksum['type'] == CHECKSUM_TYPE_HALF_BYTE_INVERSE else value
                ir_hex[checksum['checksum_byte_pos']] = value % 256
            elif checksum['type'] == CHECKSUM_TYPE_SPEC_HALF_BYTE or checksum['type'] == CHECKSUM_TYPE_SPEC_HALF_BYTE_INVERSE:
                if not 'spec_pos' in checksum:
                    continue
                for pos in checksum['spec_pos']:
                    byte_pos = pos >> 1
                    value += ir_hex[byte_pos] >> 4 if 0 == (
                        pos & 0x01) else ir_hex[byte_pos] & 0x0F
                value += checksum['checksum_plus']
                value %= 256
                value = ~value + \
                    256 if checksum['type'] == CHECKSUM_TYPE_SPEC_HALF_BYTE_INVERSE else value
                apply_byte_pos = checksum['checksum_byte_pos'] >> 1
                if 0 == (checksum['checksum_byte_pos'] & 0x01):
                    ir_hex[apply_byte_pos] = (
                        (ir_hex[apply_byte_pos] & 0x0F) | (value << 4)) % 256
                else:
                    ir_hex[apply_byte_pos] = (
                        (ir_hex[apply_byte_pos] & 0xF0) | (value & 0x0F)) % 256
            elif checksum['type'] == CHECKSUM_TYPE_SPEC_HALF_BYTE_ONE_BYTE or checksum['type'] == CHECKSUM_TYPE_SPEC_HALF_BYTE_INVERSE_ONE_BYTE:
                if not 'spec_pos' in checksum:
                    continue
                for pos in checksum['spec_pos']:
                    byte_pos = pos >> 1
                    value += ir_hex[byte_pos] >> 4 if 0 == (
                        pos & 0x01) else ir_hex[byte_pos] & 0x0F
                value += checksum['checksum_plus']
                value %= 256
                value = ~value + \
                    256 if checksum['type'] == CHECKSUM_TYPE_SPEC_HALF_BYTE_INVERSE_ONE_BYTE else value
                apply_byte_pos = checksum['checksum_byte_pos'] >> 1
                ir_hex[apply_byte_pos] = value % 256

        ir_raw = []
        ir_raw.extend(self._boot_code)
        for i in range(0, len(ir_hex)):
            bit_num = self._bits_per_byte(i)
            for j in range(0, bit_num):
                mask = 0x00
                if self._endian == 0:
                    mask = ((1 << (bit_num - 1)) >> j)
                else:
                    mask = (1 << j)
                if ir_hex[i] & mask:
                    ir_raw.extend(self._one)
                else:
                    ir_raw.extend(self._zero)
            for delay in self._delay:
                if delay['pos'] == i:
                    ir_raw.extend(delay['time'])
        if self._last_bit == 0:
            ir_raw.append(self._one[0])
        for delay in self._delay:
            if delay['pos'] == -1:
                ir_raw.extend(delay['time'])
        # for i in range(1, len(ir_raw), 2):
        #     ir_raw[i] = -ir_raw[i]
        ir_raw *= self._repeat_time
        return ir_raw

    def _apply_type_1(self, hex, data, is_temp=False):
        for i in range(0, len(data), 2):
            if is_temp:
                hex[data[i]] = (hex[data[i]] + data[i+1]) % 256
            else:
                hex[data[i]] = data[i+1]
        return hex

    def _apply_type_2(self, hex, data, is_temp=False):
        for i in range(0, len(data), 3):
            start_bit = data[i]
            end_bit = data[i+1]
            bit_range = end_bit - start_bit
            raw_value = data[i+2]
            cover_byte_pos_hi = start_bit >> 3
            cover_byte_pos_lo = (end_bit - 1) >> 3
            int_start_bit = start_bit - (cover_byte_pos_hi << 3)
            int_end_bit = end_bit - (cover_byte_pos_lo << 3)
            if cover_byte_pos_hi == cover_byte_pos_lo:
                mask = ((0xFF << (8 - int_start_bit))
                        | (0xFF >> int_end_bit)) % 256
                origin = hex[cover_byte_pos_lo]
                if is_temp:
                    move_bit = (8 - int_end_bit)
                    value = (origin & mask) | (
                        ((((origin & ~mask) >> move_bit) + raw_value) << move_bit) & ~mask)
                else:
                    value = (origin & mask) | (
                        (raw_value << (8 - int_start_bit - bit_range)) & ~mask)
                hex[cover_byte_pos_lo] = value % 256
            else:
                origin_hi = hex[cover_byte_pos_hi]
                origin_lo = hex[cover_byte_pos_lo]
                mask_hi = 0xFF << (8 - int_start_bit)
                mask_lo = 0xFF >> int_end_bit
                value = ((origin_hi & ~mask_hi) << int_end_bit) | (
                    (origin_lo & ~mask_lo) >> (8 - int_end_bit))
                if is_temp:
                    raw_value += value
                hex[cover_byte_pos_hi] = ((origin_hi & mask_hi) | (
                    ((0xFF >> (8 - bit_range)) & raw_value) >> int_end_bit)) % 256
                hex[cover_byte_pos_lo] = ((origin_lo & mask_lo) | (
                    ((0xFF >> (8 - bit_range)) & raw_value) << (8 - int_end_bit))) % 256
        return hex

    def _parse_n_mode(self, data: str):
        result = {}
        if data == 'NA':
            return result
        if data == '':
            result['speed'] = []
            result['temperature'] = []
            return result
        data = data.split('|')
        for sub in data:
            if sub in ['S', 's']:
                result['speed'] = list(range(0, 4))
            elif sub in ['T', 't']:
                result['temperature'] = list(range(16, 31))
            elif sub.startswith('S&') or sub.startswith('s&'):
                result['speed'] = []
                for s in sub[2:].split(','):
                    if s:
                        result['speed'].append(int(s))
            elif sub.startswith('T&') or sub.startswith('t&'):
                result['temperature'] = []
                for t in sub[2:].split(','):
                    if t:
                        result['temperature'].append(int(t))
        return result

    def _parse_data(self, hex_data: str):
        data = bytes.fromhex(hex_data)
        result = []
        index = 0
        while index < len(data):
            seg_len = data[index]
            index += 1
            result.append(data[index:index + seg_len])
            index += seg_len
        return result

    def _bits_per_byte(self, index):
        if not self._bit_num:
            return 8
        for bit_num in self._bit_num:
            if bit_num['pos'] == index:
                return bit_num['bits']
            if bit_num['pos'] > index:
                return 8
        return 8

    def get_supported_mode(self):
        supported_modes = []
        for mode in modes:
            # and ( self._mode1[mode] or self._mode2[mode]): # TODO: fix
            if not self._n_mode[mode]:
                continue
            if self._mode1 and not self._mode1[mode]:
                continue
            if self._mode2 and not self._mode2[mode]:
                continue
            supported_modes.append(mode)
        return supported_modes

    def get_temperature_range(self, mode):
        temp = []
        for t in range(0, 15):
            if self._n_mode[mode] and 'temperature' in self._n_mode[mode] and t + 16 in self._n_mode[mode]['temperature']:
                continue
            if self._temp1 and not self._temp1[t]:
                continue
            if self._temp2 and not self._temp2[t]:
                continue
            temp.append(t + 16)
        return temp

    def get_supported_wind_speed(self, mode):
        speed = []
        for s in speeds:
            if self._n_mode[mode] and 'speed' in self._n_mode[mode] and s in self._n_mode[mode]['speed']:
                continue
            if self._speed1 and not self._speed1[s]:
                continue
            if self._speed2 and not self._speed2[s]:
                continue
            speed.append(s)
        return speed
    
    def get_supported_swing_mode(self):
        if self._swing_mode not in ["0", "1"] and ( self._swing1 or self._swing2):
            return swing_modes
        return []
