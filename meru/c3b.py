from .binary import BinaryReader, Endian
from .linear import Mat44, Vec4, Vec3, Vec2

C3B_SIGNATURE = "C3B\0"
C3B_SIGNATURE_LENGTH = 4


class C3bError(Exception):
    pass


class C3bType:
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
    MESHES = 34
    MESH_PART = 35
    MESH_SKIN = 36
    TYPES = [
        SCENE, NODES, ANIMATIONS, ANIMATION, ANIMATION_CHANNEL, MODEL,
        MATERIALS, EFFECT, CAMERA, LIGHT, MESHES, MESH_PART, MESH_SKIN
    ]

    @classmethod
    def is_valid(self, value):
        return value in self.TYPES


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
    def __init__(self, _id, vertex_array):
        self.id = _id
        self.vertex_array = vertex_array
        self.indices = []
        self.aabb = []


class C3bVertexArray:
    def __init__(self):
        self.attributes = []
        self.values = []

    def values_per_vertex(self):
        value_count = 0
        for attrib in self.attributes:
            value_count += attrib.value_count
        return value_count

    def vertex_count(self):
        return int(len(self.values) / self.values_per_vertex())

    def get_attribute_vertices(self, attrib_name):
        value_offset = 0
        for attrib in self.attributes:
            if attrib.name == attrib_name:
                matched_attrib = attrib
                break
            else:
                value_offset += attrib.value_count
        else:
            raise ValueError("No attribute named {0}.".format(attrib_name))

        attrib_vertices = []
        stride = self.values_per_vertex()
        for i in range(0, len(self.values), stride):
            _offset = i + value_offset
            vertex = self.values[_offset: _offset + matched_attrib.value_count]
            attrib_vertices.append(tuple(vertex))

        assert len(attrib_vertices) == int(self.vertex_count())
        return attrib_vertices

    def get_positions(self):
        return self._get_vec3("VERTEX_ATTRIB_POSITION")

    def get_normals(self):
        return self._get_vec3("VERTEX_ATTRIB_NORMAL")

    def get_uvs(self):
        uvs = []
        for vertex in self.get_attribute_vertices("VERTEX_ATTRIB_TEX_COORD"):
            uvs.append(Vec2(vertex[0], vertex[1]))
        return uvs

    def get_blend_weights(self):
        return self._get_vec4("VERTEX_ATTRIB_BLEND_WEIGHT")

    def get_blend_indices(self):
        formatted_indices = []
        for _vec4 in self._get_vec4("VERTEX_ATTRIB_BLEND_INDEX"):
            formatted_indices.append(Vec4(int(_vec4.x), int(_vec4.y),
            int(_vec4.z), int(_vec4.w)))
        return formatted_indices

    def _get_vec3(self, attrib_name):
        attrib_vertices = []
        for vertex in self.get_attribute_vertices(attrib_name):
            attrib_vertices.append(Vec3(vertex[0], vertex[1], vertex[2]))
        return attrib_vertices

    def _get_vec4(self, attrib_name):
        attrib_vertices = []
        for vertex in self.get_attribute_vertices(attrib_name):
            attrib_vertices.append(Vec4(vertex[0], vertex[1],
                vertex[2], vertex[3]))
        return attrib_vertices


class C3bVertexAttribute:
    def __init__(self, value_count, _type, name):
        self.value_count = value_count
        self.type = _type
        self.name = name


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

    def get_skeleton(self):
        assert self.is_skeleton


class MeruSkeleton:
    def __init__(self):
        self.bones = []
        self._index = 0

    @classmethod
    def from_nodes(self, nodes):
        skeleton_node = self._find_skeleton(nodes)
        skeleton = MeruSkeleton()
        skeleton._parse_bone(skeleton_node, None)
        return skeleton

    @classmethod
    def _find_skeleton(self, nodes):
        filtered = list(filter(lambda node: node.is_skeleton, nodes))
        assert len(filtered) == 1
        return filtered[0]

    def _parse_bone(self, node, parent):
        bone = MeruBone(node.id, self._next_index(), node.transform, parent)
        self.bones.append(bone)
        for child in node.children:
            self._parse_bone(child, bone)
        return bone

    def _next_index(self):
        index = self._index
        self._index += 1
        return index


class MeruBone:
    def __init__(self, _id, index, transform, parent=None):
        self.id = _id
        self.index = index
        self.transform = transform
        self.parent = parent


class C3bNodePart:
    def __init__(self, mesh_id, material_id):
        self.mesh_id = mesh_id
        self.material_id = material_id
        self.bones = []


class C3bBone:
    def __init__(self, name, inv_bind_pos):
        self.name = name
        self.inv_bind_pos = inv_bind_pos


class C3bAnimFlag:
    HAS_ROTATION = (1 << 0)
    HAS_SCALE = (1 << 1)
    HAS_TRANSLATION = (1 << 2)


class C3bAnimation:
    def __init__(self, _id, total_time):
        self.id = _id
        self.total_time = total_time
        self._bones = {}

    def get_bones(self):
        return list(self._bones.keys())

    def add_keyframe(self, bone_id, keyframe):
        if bone_id not in self._bones:
            self._bones[bone_id] = []
        self._bones[bone_id].append(keyframe)

    def get_keyframes(self, bone_id):
        assert bone_id in self._bones
        return self._bones[bone_id]


class C3bAnimKeyFrame:
    def __init__(self, time, scale=None, rotation=None, translation=None):
        self.time = time
        self.scale = scale
        self.rotation = rotation
        self.translation = translation


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
            if not C3bType.is_valid(_type):
                raise ValueError("Invalid reference type {0}.".format(_type))
            offset = self._read_uint()
            references.append(C3bReference(_id, _type, offset))
        return C3bHeader(major_version, minor_version, references)

    def read_meshes(self, index):
        self.seek_type(C3bType.MESHES, index)
        meshes = []

        # Read vertex arrays
        vertex_arr_count = self._read_uint()
        for vertex_arr_index in range(vertex_arr_count):
            vertex_array = C3bVertexArray()

            # Read attributes
            attrib_count = self._read_uint()
            for attrib_index in range(attrib_count):
                value_count = self._read_uint()
                _type = self._read_string()
                name = self._read_string()
                vertex_array.attributes.append(
                    C3bVertexAttribute(value_count, _type, name))

            # Read vertices
            value_count = self._read_uint()
            for value_index in range(value_count):
                vertex_value = self._reader.read_float32(self.endianness)
                vertex_array.values.append(vertex_value)

            # Read meshes
            mesh_count = self._read_uint()
            for mesh_index in range(mesh_count):
                _id = self._read_string()
                mesh = C3bMesh(_id, vertex_array)

                # Read indices
                index_count = self._read_uint()
                for i in range(index_count):
                    _index = self._reader.read_uint16(self.endianness)
                    mesh.indices.append(_index)

                # Read axis aligned bounding box
                for aabb in range(6):
                    aabb_coord = self._reader.read_float32(Endian.LITTLE)
                    mesh.aabb.append(aabb_coord)
            meshes.append(mesh)
        return meshes

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
            mesh_id = self._read_string()
            material_id = self._read_string()
            node_part = C3bNodePart(mesh_id, material_id)

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

    def read_animations(self, index):
        self.seek_type(C3bType.ANIMATIONS, index)
        _id = self._read_string()
        total_time = self._reader.read_float32(self.endianness)
        anim = C3bAnimation(_id, total_time)

        bone_node_count = self._read_uint()
        for bone_node_index in range(bone_node_count):
            bone_name = self._read_string()
            keyframe_count = self._read_uint()

            for keyframe_index in range(keyframe_count):
                keyframe_time = self._reader.read_float32(self.endianness)
                keyframe_flag = self._reader.read_uint8(self.endianness)
                keyframe = C3bAnimKeyFrame(keyframe_time)

                if ((keyframe_flag & C3bAnimFlag.HAS_ROTATION) ==
                C3bAnimFlag.HAS_ROTATION):
                    keyframe.rotation = self._read_vec4()

                if ((keyframe_flag & C3bAnimFlag.HAS_SCALE) ==
                C3bAnimFlag.HAS_SCALE):
                    keyframe.scale = self._read_vec3()

                if ((keyframe_flag & C3bAnimFlag.HAS_TRANSLATION) ==
                C3bAnimFlag.HAS_TRANSLATION):
                    keyframe.translation = self._read_vec3()
                anim.add_keyframe(bone_name, keyframe)
        return anim

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

    def _read_vec3(self):
        values = []
        for i in range(3):
            values.append(self._reader.read_float32(self.endianness))
        return Vec3(values[0], values[1], values[2])

    def _read_vec4(self):
        values = []
        for i in range(4):
            values.append(self._reader.read_float32(self.endianness))
        return Vec4(values[0], values[1], values[2], values[3])
