#!/usr/bin/env python3
import click
from c3b import C3bParser


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
            print("Type: {0}".format(ref.type.name))
            print("Offset: {0}".format(ref.offset))
            print()
        print()


@main.command()
@click.argument("filenames", type=click.Path(exists=True), nargs=-1)
def mesh(filenames):
    for filename in filenames:
        parser = C3bParser.from_file(filename)
        if not parser.verify_signature():
            print("ERROR: {0} is not a c3b file.".format(filename))
            continue

        mesh = parser.read_mesh(0)
        print("File: {0}".format(filename))
        print("VertexArrayCount: {0}".format(len(mesh.vertex_arrays)))
        for vertex_array in mesh.vertex_arrays:
            print()
            print("VertexCount: {0}".format(vertex_array.vertex_count()))
            print("AttributeCount: {0}".format(len(vertex_array.attributes)))
            for attribute in vertex_array.attributes:
                print()
                print("Name: {0}".format(attribute.name))
                print("Type: {0}".format(attribute.type))
                print("NrValues: {0}".format(attribute.nr_values))
            print()
            print("ShapeCount: {0}".format(len(vertex_array.shapes)))
            for shape in vertex_array.shapes:
                print()
                print("ID: {0}".format(shape.id))
                print("IndexCount: {0}".format(len(shape.indices)))


@main.command()
@click.argument("filenames", type=click.Path(exists=True), nargs=-1)
def materials(filenames):
    for filename in filenames:
        parser = C3bParser.from_file(filename)
        materials = parser.read_materials(0)
        print(materials)


if __name__ == '__main__':
    main()
