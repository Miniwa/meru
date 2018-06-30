from binary import BinaryReader

C3B_SIGNATURE = "C3B\0"
C3B_SIGNATURE_LENGTH = 4


class C3bError(Exception):
    pass


class C3bHeader:
    def __init__(self, version, references):
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
