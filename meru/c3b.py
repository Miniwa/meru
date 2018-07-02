from enum import Enum
from binary import BinaryReader, Endian
from linear import Mat44

C3B_SIGNATURE = "C3B\0"
C3B_SIGNATURE_LENGTH = 4


class C3bError(Exception):
    pass


class C3bType(Enum):
    SCENE = 1
    NODES = 2
    ANIMATIONS = 3
    ANIMATION = 4
    ANIMATION_CHANNEL = 5
    MODEL = 10
    MATERIALS = 16
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


class C3bMesh:
    def __init__(self):
        self.vertex_arrays = []


class C3bVertexArray:
    def __init__(self):
        self.attributes = []
        self.values = []
        self.shapes = []

    def values_per_vertex(self):
        value_count = 0
        for attrib in self.attributes:
            value_count += attrib.nr_values
        return value_count

    def vertex_count(self):
        return len(self.values) / self.values_per_vertex()


class C3bVertexAttribute:
    def __init__(self, nr_values, _type, name):
        self.nr_values = nr_values
        self.type = _type
        self.name = name


class C3bShape:
    def __init__(self, _id):
        self.id = _id
        self.indices = []
        self.aabb = []


class C3bMaterial:
    def __init__(self, _id):
        self.id = _id
        self.textures = []


class C3bTexture:
    def __init__(self, _id, filename, _type, wrap_u, wrap_v):
        self.id = _id
        self.filename = filename
        self.type = _type
        self.wrap_u = wrap_u
        self.wrap_v = wrap_v


class C3bNode:
    def __init__(self, _id, is_skeleton, transform):
        self.id = _id
        self.is_skeleton = is_skeleton
        self.transform = transform
        self.parts = []
        self.children = []


class C3bNodePart:
    def __init__(self, shape_id, material_id):
        self.shape_id = shape_id
        self.material_id = material_id
        self.bones = []


class C3bBone:
    def __init__(self, name, inv_bind_pos):
        self.name = name
        self.inv_bind_pos = inv_bind_pos


class C3bParser:
    def __init__(self, _bytes):
        self._reader = BinaryReader(_bytes)
        self.endianness = Endian.LITTLE

    @classmethod
    def from_file(self, filename):
        with open(filename, "rb") as _file:
            buffer = _file.read()
            parser = C3bParser(buffer)
        return parser

    def verify_signature(self):
        self._reader.seek(0)
        return self._reader.read_string(C3B_SIGNATURE_LENGTH) == C3B_SIGNATURE

    def read_header(self):
        self._reader.seek(4)
        major_version = self._reader.read_int8()
        minor_version = self._reader.read_int8()

        references = []
        reference_count = self._read_uint()
        for i in range(reference_count):
            _id = self._read_string()
            _type = self._read_uint()
            offset = self._read_uint()
            references.append(C3bReference(_id, C3bType(_type), offset))
        return C3bHeader(major_version, minor_version, references)

    def read_mesh(self, index):
        self.seek_type(C3bType.MESH, index)
        mesh = C3bMesh()

        # Read vertex arrays
        vertex_arr_count = self._read_uint()
        for vertex_arr_index in range(vertex_arr_count):
            vertex_array = C3bVertexArray()

            # Read attributes
            attrib_count = self._read_uint()
            for attrib_index in range(attrib_count):
                nr_values = self._read_uint()
                _type = self._read_string()
                name = self._read_string()
                vertex_array.attributes.append(
                    C3bVertexAttribute(nr_values, _type, name))

            # Read vertices
            value_count = self._read_uint()
            for value_index in range(value_count):
                vertex_value = self._reader.read_float32(self.endianness)
                vertex_array.values.append(vertex_value)

            # Read shapes
            shape_count = self._read_uint()
            for shape_index in range(shape_count):
                _id = self._read_string()
                shape = C3bShape(_id)

                # Read indices
                index_count = self._read_uint()
                for i in range(index_count):
                    _index = self._reader.read_uint16(self.endianness)
                    shape.indices.append(_index)

                # Read axis aligned bounding box
                for aabb in range(6):
                    aabb_coord = self._reader.read_float32(Endian.LITTLE)
                    shape.aabb.append(aabb_coord)
                vertex_array.shapes.append(shape)
            mesh.vertex_arrays.append(vertex_array)
        return mesh

    def read_materials(self, index):
        self.seek_type(C3bType.MATERIALS, index)
        materials = []

        material_count = self._read_uint()
        for material_index in range(material_count):
            _id = self._read_string()
            material = C3bMaterial(_id)

            # Skip diffuse(3 float), ambient(3 float), emissive(3 float),
            # opacity(1 float), specular(3 float), shininess(1 float)
            self._reader.strict_read(14 * 4)

            texture_count = self._read_uint()
            for texture_index in range(texture_count):
                texture_id = self._read_string()
                texture_filename = self._read_string()

                # Skip UV data (4 float), handled by vertex attribute?
                self._reader.read(4 * 4)

                texture_type = self._read_string()
                texture_wrap_u = self._read_string()
                texture_wrap_v = self._read_string()
                texture = C3bTexture(texture_id, texture_filename,
                    texture_type, texture_wrap_u, texture_wrap_v)
                material.textures.append(texture)
            materials.append(material)
        return materials

    def read_nodes(self, index):
        self.seek_type(C3bType.NODES, index)

        nodes = []
        node_count = self._read_uint()
        for i in range(node_count):
            nodes.append(self._read_node(node_count == 1))
        return nodes

    def _read_node(self, single_sprite):
        _id = self._read_string()
        is_skeleton = self._reader.read_bool()
        transform = self._read_mat44()

        node = C3bNode(_id, is_skeleton, transform)
        part_count = self._read_uint()
        for part_index in range(part_count):
            shape_id = self._read_string()
            material_id = self._read_string()
            node_part = C3bNodePart(shape_id, material_id)

            bone_count = self._read_uint()
            for bone_index in range(bone_count):
                bone_name = self._read_string()
                inv_bind_pos = self._read_mat44()
                bone = C3bBone(bone_name, inv_bind_pos)
                node_part.bones.append(bone)

            uv_map_count = self._read_uint()
            for uv_map_index in range(uv_map_count):
                texture_index_count = self._read_uint()
                for texture_index in range(texture_index_count):
                    # Skip
                    self._read_uint()
            node.parts.append(node_part)

        child_count = self._read_uint()
        for child_index in range(child_count):
            child = self._read_node(single_sprite)
            node.children.append(child)
        return node

    def seek_type(self, _type, index):
        refs = self.read_header().references
        filtered = list(filter(lambda ref: ref.type == _type, refs))
        if index >= len(filtered):
            raise IndexError("{0} index out of bounds, max {1}."
                .format(_type.name, len(filtered) - 1))
        self._reader.seek(filtered[index].offset)

    def _read_uint(self):
        return self._reader.read_uint32(self.endianness)

    def _read_ushort(self):
        return self._reader.read_uint16(self.endianness)

    def _read_string(self):
        return self._reader.read_prefixed_string_uint32(self.endianness)

    def _read_mat44(self):
        values = []
        for i in range(16):
            values.append(self._reader.read_float32(self.endianness))
        return Mat44(values)
