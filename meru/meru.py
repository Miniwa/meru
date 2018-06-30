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
def scan(filenames):
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
            print(" ID: {0}".format(ref.id))
            print(" Type: {0}".format(ref.type.name))
            print(" Offset: {0}".format(ref.offset))
            print()
        print()


if __name__ == '__main__':
    main()
