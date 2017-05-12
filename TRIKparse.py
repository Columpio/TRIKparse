from itertools import chain
import pickle
import os
import os.path

from parseCPP import *


# Constants
OUT_INCLUDES_PATH = "out/trikPythonIncludes.h"
OUT_INCLUDE_DIRS_PATH = "out/include_dirs.txt"
OUT_XML_PATH = "out/trikPython.xml"

TYPESYSTEM_NAME = "PythonTrikTypesystem"


def isHeaderExt(ext):
    return ext in ('.h', '.hpp')


def collectHeaders(trikRuntimeRoot):
    # TODO: handle ~/folder

    parsed_files = set()
    for root, _, files in os.walk(trikRuntimeRoot):
        for filename in files:
            if isHeaderExt(os.path.splitext(filename)[1]):
                parsed_files.add(parseFile(os.path.join(root, filename)))

    return parsed_files


def collectDirs(files):
    return {os.path.dirname(file.name) for file in files}


def collectIncludes(files):
    return {os.path.basename(file.name) for file in files}


def dumpToFile(root, files, filename='parsed.pickle', force=False):
    if not os.access(filename, os.F_OK) or force:
        with open(filename, 'wb') as file:
            pickle.dump((root, files), file)


def generateDirs(files, force=False):
    include_dirs = collectDirs(files)
    if not os.access(OUT_INCLUDE_DIRS_PATH, os.F_OK) or force:
        with open(OUT_INCLUDE_DIRS_PATH, 'w') as file:
            file.write('\n'.join(include_dirs))


def generateH(qt_includes, our_includes, force=False):
    if not os.access(OUT_INCLUDES_PATH, os.F_OK) or force:
        with open(OUT_INCLUDES_PATH, 'w') as file:
            file.write('\n'.join("#include <%s>" % include for include in sorted(qt_includes)))
            file.write('\n\n')
            file.write('\n'.join('#include "%s"' % include for include in sorted(our_includes)))


class XMLBuilder(object):
    def __init__(self, name):
        self.head = '\n'.join([
            '<?xml version="1.0"?>',
            '<typesystem package="{name}">'.format(name=name),
            '\t<load-typesystem name="typesystem_core.xml" generate="no" />',
            '\t<load-typesystem name="typesystem_gui.xml"  generate="no" />\n\n\t'
            '{body}',
            '</typesystem>'
        ]).replace('\t', ' ' * 4)
        self.body = set()

    def addEntry(self, entry, prefix=''):
        self.body.update(entry.xml(prefix))

    def build(self):
        return self.head.format(body='\n    '.join(sorted(self.body)))


def generateXML(files, force=False):
    def walk(builder, scope, prefix=''):
        for entry in scope:
            builder.addEntry(entry, prefix)
            if entry.nested:
                walk(builder, entry.nested, "%s%s::" % (prefix, entry.name))

    builder = XMLBuilder(TYPESYSTEM_NAME)

    for file in files:
        walk(builder, file.scope)

    if not os.access(OUT_XML_PATH, os.F_OK) or force:
        with open(OUT_XML_PATH, 'w') as file:
            file.write(builder.build())


def checkIncludes(files, global_includes):
    for file in files:
        for include in file.global_includes:
            if 'trik' in include.lower():
                print("WARNING: `#include <{0}>` in {1}".format(include, file.name))
            include_name, ext = os.path.splitext(include)
            if isHeaderExt(ext) and include_name in global_includes:
                print("WARNING: `#include <{0}>` is `#include <{2}>`? in {1}".format(include, file.name, include_name))


def main(root):
    files = collectHeaders(root)

    our_includes = collectIncludes(files)
    global_includes = set(chain.from_iterable(file.global_includes for file in files))

    checkIncludes(files, global_includes)

    generateDirs(files)
    generateH(global_includes, our_includes)
    generateXML(files)


if __name__ == "__main__":
    main("/home/columpio/myTRIKStudio/src/trikRuntime/")
