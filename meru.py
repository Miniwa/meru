#!/usr/bin/env python3
import click
from meru.c3b import C3bParser


CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"]
}


@click.group(context_settings=CONTEXT_SETTINGS)
def main():
    pass


@main.command()
@click.argument("filenames", type=click.Path(exists=True), nargs=-1)
def header(filenames):
    for filename in filenames:
        with open(filename, "rb") as _file:
            buffer = _file.read()
            parser = C3bParser(buffer)

        if not parser.verify_signature():
            print("ERROR: {0} is not a c3b file.".format(filename))
            continue

        header = parser.read_header()
        print("File: {0}".format(filename))
        print("Version: {0}.{1}".format(header.major_version,
            header.minor_version))
        print("RefCount: {0}".format(len(header.references)))

        for ref in header.references:
            print("ID: {0}".format(ref.id))
            print("Type: {0}".format(ref.type))
            print("Offset: {0}".format(ref.offset))
            print()
        print()


@main.command()
@click.argument("filenames", type=click.Path(exists=True), nargs=-1)
def meshes(filenames):
    for filename in filenames:
        parser = C3bParser.from_file(filename)
        if not parser.verify_signature():
            print("ERROR: {0} is not a c3b file.".format(filename))
            continue

        meshes = parser.read_meshes(0)
        print("File: {0}".format(filename))
        print("MeshCount: {0}".format(len(meshes)))
        for mesh in meshes:
            indices = mesh.vertex_array.get_blend_indices()
            print()
            print("ID: {0}".format(mesh.id))
            print("VertexCount: {0}".format(mesh.vertex_array.vertex_count()))
            print("IndexCount: {0}".format(len(mesh.indices)))
            print("AttributeCount: {0}".format(
                len(mesh.vertex_array.attributes)))
            for attribute in mesh.vertex_array.attributes:
                print()
                print("Name: {0}".format(attribute.name))
                print("Type: {0}".format(attribute.type))
                print("ValueCount: {0}".format(attribute.value_count))
            print()


@main.command()
@click.argument("filenames", type=click.Path(exists=True), nargs=-1)
def materials(filenames):
    for filename in filenames:
        parser = C3bParser.from_file(filename)
        materials = parser.read_materials(0)
        print(materials)


@main.command()
@click.argument("filenames", type=click.Path(exists=True), nargs=-1)
def nodes(filenames):
    for filename in filenames:
        parser = C3bParser.from_file(filename)
        nodes = parser.read_nodes(0)
        print(nodes)


if __name__ == "__main__":
    main()
