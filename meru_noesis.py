from inc_noesis import *
from meru.c3b import C3bParser, MeruSkeleton


def registerNoesisTypes():
    handle = noesis.register("Cocos2d-x Binary", ".c3b")
    noesis.setHandlerTypeCheck(handle, c3b_check_type)
    noesis.setHandlerLoadModel(handle, c3b_load_model)
    noesis.logPopup()
    return 1


def c3b_to_vec2(_vec):
    return NoeVec2(_vec.unpack())


def c3b_to_vec3(_vec):
    return NoeVec3(_vec.unpack())


def c3b_to_vec4(_vec):
    return NoeVec4(_vec.unpack())


def c3b_to_mat44(_mat):
    return NoeMat44(_mat.unpack())


def c3b_to_bone(_bone):
    bone = NoeBone()
    bone.index = _bone.index
    bone.name = _bone.id
    if _bone.parent is not None:
        bone.parent_index = _bone.parent.index
        bone.parent_name = _bone.parent.id
    return bone


def c3b_check_type(data):
    parser = C3bParser(data)
    return int(parser.verify_signature())


def c3b_load_model(data, models):
    parser = C3bParser(data)
    if not parser.verify_signature():
        return 0

    meshes = []
    for _mesh in parser.read_meshes(0):
        print("Mesh:")
        print("Reading positions..")
        positions = []
        for _pos in _mesh.vertex_array.get_positions():
            positions.append(c3b_to_vec3(_pos))

        print("Creating mesh..")
        mesh = NoeMesh(_mesh.indices, positions, _mesh.id)

        print("Adding normals..")
        for _normal in _mesh.vertex_array.get_normals():
            mesh.normals.append(c3b_to_vec3(_normal))

        print("Adding weights..")
        _blend_indices = _mesh.vertex_array.get_blend_indices()
        _blend_weights = _mesh.vertex_array.get_blend_weights()
        assert len(_blend_indices) == len(_blend_weights)
        for i in range(len(_blend_weights)):
            _index = _blend_indices[i]
            _weight = _blend_weights[i]
            mesh.weights.append(
                NoeVertWeight(_index.unpack(), _weight.unpack()))
        meshes.append(mesh)

    print("Reading nodes..")
    _nodes = parser.read_nodes(0)

    print("Building skeleton..")
    skeleton = MeruSkeleton.from_nodes(_nodes)

    print("Building bone list..")
    bones = []
    for _bone in skeleton.bones:
        bones.append(c3b_to_bone(_bone))

    print("Creating model..")
    model = NoeModel(meshes, bones=bones)
    models.append(model)
    return 1
