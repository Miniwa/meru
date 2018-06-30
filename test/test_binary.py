import struct
import sys
import pytest
from meru.binary import Endian, parse_int32, parse_uint32, BinaryReader


_int = -255
_int_bytes = struct.pack("=i", _int)
_int_bytes_little = struct.pack("<i", _int)
_int_bytes_big = struct.pack(">i", _int)


_uint = 255
_uint_bytes = struct.pack("=I", _uint)
_uint_bytes_little = struct.pack("<I", _uint)
_uint_bytes_big = struct.pack(">I", _uint)


class TestEndian:
    def test_native(self):
        if sys.byteorder == "little":
            assert Endian.native() == Endian.LITTLE
        else:
            assert Endian.native() == Endian.BIG


class TestParse:
    def test_parse_int32(self):
        assert parse_int32(_int_bytes) == _int

    def test_parse_int32_little(self):
        assert parse_int32(_int_bytes_little, Endian.LITTLE) == _int

    def test_parse_int32_big(self):
        assert parse_int32(_int_bytes_big, Endian.BIG) == _int

    def test_parse_uint32(self):
        assert parse_uint32(_uint_bytes) == _uint

    def test_parse_uint32_little(self):
        assert parse_uint32(_uint_bytes_little, Endian.LITTLE) == _uint

    def test_parse_uint32_big(self):
        assert parse_uint32(_uint_bytes_big, Endian.BIG) == _uint


class TestBinaryReader:
    def setup_method(self):
        self._reader = BinaryReader(bytes(10))

    def test_length(self):
        assert self._reader.length() == 10

    def test_pos(self):
        assert self._reader.pos() == 0

    def test_remaining(self):
        assert self._reader.remaining() == 10

    def test_seek(self):
        self._reader.seek(5)
        assert self._reader.pos() == 5
        assert self._reader.remaining() == 5

    def test_move(self):
        self._reader.move(2)
        assert self._reader.pos() == 2

        self._reader.move(-2)
        assert self._reader.pos() == 0

    def test_seek_throws_on_invalid_index(self):
        with pytest.raises(IndexError):
            self._reader.seek(-1)
        with pytest.raises(IndexError):
            self._reader.seek(11)

    def test_read(self):
        _bytes = self._reader.read(4)
        assert len(_bytes) == 4
        assert self._reader.pos() == 4

    def test_read_returns_empty_bytes_if_reached_eof(self):
        self._reader.seek(10)
        _bytes = self._reader.read(1)
        assert len(_bytes) == 0
        assert self._reader.pos() == 10

    def test_read_int32(self):
        reader = BinaryReader(_int_bytes)
        assert reader.read_int32() == _int
        assert reader.pos() == 4

    def test_read_int32_little(self):
        reader = BinaryReader(_int_bytes_little)
        assert reader.read_int32(Endian.LITTLE) == _int
        assert reader.pos() == 4

    def test_read_int32_big(self):
        reader = BinaryReader(_int_bytes_big)
        assert reader.read_int32(Endian.BIG) == _int
        assert reader.pos() == 4

    def test_read_uint32(self):
        reader = BinaryReader(_uint_bytes)
        assert reader.read_uint32() == _uint
        assert reader.pos() == 4

    def test_read_uint32_little(self):
        reader = BinaryReader(_uint_bytes_little)
        assert reader.read_uint32(Endian.LITTLE) == _uint
        assert reader.pos() == 4

    def test_read_uint32_big(self):
        reader = BinaryReader(_uint_bytes_big)
        assert reader.read_uint32(Endian.BIG) == _uint
        assert reader.pos() == 4

    def test_read_string(self):
        reader = BinaryReader(b"Hello")
        assert reader.read_string(5) == "Hello"
