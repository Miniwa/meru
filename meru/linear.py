class Vec2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def unpack(self):
        return (self.x, self.y)


class Vec3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def unpack(self):
        return (self.x, self.y, self.z)


class Vec4:
    def __init__(self, x, y, z, w):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def unpack(self):
        return (self.x, self.y, self.z, self.w)


class Mat:
    def __init__(self, values):
        assert len(values) == (self.__class__.ROW_COUNT *
            self.__class__.COLUMN_COUNT)
        self.values = values

    def get(self, x, y):
        offset = x * self.__class__.COLUMN_COUNT
        return self.values[offset + y]

    def unpack(self):
        return (self.values)


class Mat44(Mat):
    ROW_COUNT = 4
    COLUMN_COUNT = 4

    def __init__(self, values):
        super().__init__(values)
