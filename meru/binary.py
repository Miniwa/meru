import sys
import struct
from enum import Enum


class Endian(Enum):
    LITTLE = 1
    BIG = 2
    NATIVE = LITTLE if sys.byteorder == "little" else BIG

    @classmethod
    def native(self):
        if sys.byteorder == "big":
            return self.BIG
        else:
            return self.LITTLE


def parse_from_format(frmt, _bytes, endianess=None):
    if endianess is None:
        endianess = Endian.native()
    endian_str = "<" if endianess == Endian.LITTLE else ">"
    combined_format = endian_str + frmt

    calced_size = struct.calcsize(combined_format)
    _len = len(_bytes)
    if struct.calcsize(combined_format) != len(_bytes):
        raise ValueError("Length of byte buffer was {0}, expected {1}."
            .format(_len, calced_size))
    return struct.unpack(combined_format, _bytes)[0]


INT8_FORMAT = "b"
INT16_FORMAT = "h"
INT32_FORMAT = "i"
INT64_FORMAT = "q"

UINT8_FORMAT = "B"
UINT16_FORMAT = "H"
UINT32_FORMAT = "I"
UINT64_FORMAT = "Q"

FLOAT32_FORMAT = "f"
FLOAT64_FORMAT = "d"


def parse_int8(byte):
    return parse_from_format(INT8_FORMAT, byte)


def parse_int16(_bytes, endianness=None):
    return parse_from_format(INT16_FORMAT, _bytes, endianness)


def parse_int32(_bytes, endianness=None):
    return parse_from_format(INT32_FORMAT, _bytes, endianness)


def parse_int64(_bytes, endianness=None):
    return parse_from_format(INT64_FORMAT, _bytes, endianness)


def parse_uint8(byte):
    return parse_from_format(UINT8_FORMAT, byte)


def parse_uint16(_bytes, endianness=None):
    return parse_from_format(UINT16_FORMAT, _bytes, endianness)


def parse_uint32(_bytes, endianness=None):
    return parse_from_format(UINT32_FORMAT, _bytes, endianness)


def parse_uint64(_bytes, endianness=None):
    return parse_from_format(UINT64_FORMAT, _bytes, endianness)


def parse_float32(_bytes, endianness=None):
    return parse_from_format(FLOAT32_FORMAT, _bytes, endianness)


def parse_float64(_bytes, endianness=None):
    return parse_from_format(FLOAT64_FORMAT, _bytes, endianness)


def parse_bool(byte):
    return parse_uint8(byte) != 0


class BinaryReader:
    def __init__(self, _bytes):
        self._bytes = _bytes
        self._index = 0
        self._length = len(_bytes)

    def length(self):
        return self._length

    def remaining(self):
        return self._length - self._index

    def seek(self, index):
        if index < 0 or index > self._length:
            raise IndexError("Index out of bounds.")
        self._index = index

    def move(self, offset):
        self.seek(self._index + offset)

    def read(self, count):
        to_read = min(count, self.remaining())
        if to_read == 0:
            return bytes()
        else:
            _read = self.bytes[self._index:self._index + to_read]
            self.move(to_read)
            return _read

    def strict_read(self, count):
        if self.remaining() < count:
            msg = "Attempted to read {0} bytes but only {1} are available."\
                .format(count, self.remaining())
            raise ValueError(msg)
        _read = self.read(count)
        _read_count = len(_read)
        if _read_count != count:
            msg = "Attempted to read {0} bytes but only {1} were read."\
                .format(count, _read_count)
            raise ValueError(msg)
        return _read

    def read_int8(self):
        return parse_int8(self.strict_read(1))

    def read_int16(self, endianness=None):
        return parse_int16(self.strict_read(2), endianness)

    def read_int32(self, endianness=None):
        return parse_int32(self.strict_read(4), endianness)

    def read_int64(self, endianness=None):
        return parse_int64(self.strict_read(8), endianness)

    def read_uint8(self):
        return parse_uint8(self.strict_read(1))

    def read_uint16(self, endianness=None):
        return parse_uint16(self.strict_read(2), endianness)

    def read_uint32(self, endianness=None):
        return parse_uint32(self.strict_read(4), endianness)

    def read_uint64(self, endianness=None):
        return parse_uint64(self.strict_read(8), endianness)

    def read_float32(self, endianness=None):
        return parse_float32(self.strict_read(4), endianness)

    def read_float64(self, endianness=None):
        return parse_float64(self.strict_read(8), endianness)

    def read_bool(self):
        return parse_bool(self.strict_read(1))

    def read_size_prefixed_int8(self):
        count = self.read_int8()
        return self.strict_read(count)

    def read_size_prefixed_int16(self, endianness=None):
        return self._read_size_prefixed(self.read_int16, endianness)

    def read_size_prefixed_int32(self, endianness=None):
        return self._read_size_prefixed(self.read_int32, endianness)

    def read_size_prefixed_int64(self, endianness=None):
        return self._read_size_prefixed(self.read_int64, endianness)

    def read_size_prefixed_uint8(self):
        count = self.read_uint8()
        return self.strict_read(count)

    def read_size_prefixed_uint16(self, endianness=None):
        return self._read_size_prefixed(self.read_uint16, endianness)

    def read_size_prefixed_uint32(self, endianness=None):
        return self._read_size_prefixed(self.read_uint32, endianness)

    def read_size_prefixed_uint64(self, endianness=None):
        return self._read_size_prefixed(self.read_uint64, endianness)

    def _read_size_prefixed(self, read_func, endianness):
        count = read_func(endianness)
        return self.strict_read(count)

    def read_string(self, length, encoding=None):
        if encoding is None:
            encoding = "utf-8"
        return self.strict_read(length).encode(encoding)

    def read_prefixed_string_int8(self, encoding=None):
        length = self.read_int8()
        return self.read_string(length, encoding)

    def read_prefixed_string_int16(self, encoding=None, endianness=None):
        return self._read_prefixed_string(self.read_int16,
            encoding, endianness)

    def read_prefixed_string_int32(self, encoding=None, endianness=None):
        return self._read_prefixed_string(self.read_int32,
            encoding, endianness)

    def read_prefixed_string_int64(self, encoding=None, endianness=None):
        return self._read_prefixed_string(self.read_int64,
            encoding, endianness)

    def read_prefixed_string_uint8(self, encoding=None):
        length = self.read_uint8()
        return self.read_string(length, encoding)

    def read_prefixed_string_uint16(self, encoding=None, endianness=None):
        return self._read_prefixed_string(self.read_uint16,
            encoding, endianness)

    def read_prefixed_string_uint32(self, encoding=None, endianness=None):
        return self._read_prefixed_string(self.read_uint32,
            encoding, endianness)

    def read_prefixed_string_uint64(self, encoding=None, endianness=None):
        return self._read_prefixed_string(self.read_uint64,
            encoding, endianness)

    def _read_prefixed_string(self, read_func, encoding, endianness):
        length = read_func(endianness)
        return self.read_string(length, encoding)
