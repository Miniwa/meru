from enum import Enum
from binary import BinaryReader, Endian

C3B_SIGNATURE = "C3B\0"
C3B_SIGNATURE_LENGTH = 4


class C3bError(Exception):
    pass


class C3bType(Enum):
    SCENE = 1
    NODE = 2
    ANIMATIONS = 3
    ANIMATION = 4
    ANIMATION_CHANNEL = 5
    MODEL = 10
    MATERIAL = 16
    EFFECT = 18
    CAMERA = 32
    LIGHT = 33
    MESH = 34
    MESH_PART = 35
    MESH_SKIN = 36


class C3bReference:
    def __init__(self, id, _type, offset):
        self.id = id
        self.type = _type

        assert offset >= 0
        self.offset = offset


class C3bHeader:
    def __init__(self, major_version, minor_version, references):
        self.major_version = major_version
        self.minor_version = minor_version
        self.references = references


class C3bParser:
    def __init__(self, _bytes):
        self._reader = BinaryReader(_bytes)

    def verify_signature(self):
        self._reader.seek(0)
        return self._reader.read_string(C3B_SIGNATURE_LENGTH) == C3B_SIGNATURE

    def read_header(self):
        self._reader.seek(4)
        major_version = self._reader.read_int8()
        minor_version = self._reader.read_int8()
        references = []
        reference_count = self._reader.read_uint32(Endian.LITTLE)
        for i in range(reference_count):
            id = self._reader.read_prefixed_string_uint32(Endian.LITTLE)
            _type = self._reader.read_uint32(Endian.LITTLE)
            offset = self._reader.read_uint32(Endian.LITTLE)
            references.append(C3bReference(id, C3bType(_type), offset))
        return C3bHeader(major_version, minor_version, references)
