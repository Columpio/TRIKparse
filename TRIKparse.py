from itertools import chain
import pickle
import os
import os.path

from parseCPP import *

OUT_INCLUDES_PATH = "out/trikPythonIncludes.h"
OUT_INCLUDE_DIRS_PATH = "out/include_dirs.txt"


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


def dumpToFile(root, files, filename='parsed.pickle', force=True):
    if not os.access(filename, os.F_OK) or force:
        with open(filename, 'wb') as file:
            pickle.dump((root, files), file)


def generateH(qt_includes, our_includes, force=True):
    if not os.access(OUT_INCLUDES_PATH, os.F_OK) or force:
        with open(OUT_INCLUDES_PATH, 'w') as file:
            file.write('\n'.join("#include <%s>" % include for include in sorted(qt_includes)))
            file.write('\n\n')
            file.write('\n'.join('#include "%s"' % include for include in sorted(our_includes)))


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

    include_dirs = collectDirs(files)
    with open(OUT_INCLUDE_DIRS_PATH, 'w') as file:
        file.write('\n'.join(include_dirs))

    our_includes = collectIncludes(files)
    global_includes = set(chain.from_iterable(file.global_includes for file in files))

    checkIncludes(files, global_includes)

    generateH(global_includes, our_includes, force=True)


if __name__ == "__main__":
    main("/home/columpio/myTRIKStudio/src/trikRuntime/")
