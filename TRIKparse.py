from __future__ import print_function
import pickle
import re
import os
import os.path
from simpleAPI import *


DEBUG = reduce(lambda x, y: x * y, map(int, '3'.split()))
"""
2 - use test_cpp_features.h
3 - remove \n
"""


class _regexps:
    nontrivial_include = re.compile(r"#include\s+<(?P<INCLUDE_NAME>[^>]*)>")

    # Garbage
    multiline_comment = re.compile("/\*.*\*/", flags=re.DOTALL)
    backslash = re.compile(r"\\\s*\n")
    comment_or_pragma = re.compile(r"(//|#).*$", flags=re.MULTILINE)
    _string = lambda c: r"((?<!\\){}.*?(?<!\\){})".format(c, c)
    string = re.compile('|'.join([_string("\""), _string("\'")]))

    friend_class = re.compile(r"^.*\sfriend\s+class\s+.*$", flags=re.MULTILINE)

    # Raw declarations, like `enum x;`, no even `class a {};`
    type_names = {
        "namespace": Namespace,
        "struct": Class,
        "class": Class,
        "enum": Enum
    }
    inlined = re.compile(r"\b(?P<TYPE_NAME>%s)\s(?P<INST_NAME>[^;]*)" % '|'.join(
        [Type.typename()for Type in type_names.values()]))

    @staticmethod
    def remove_by_re(text, *REs):
        if not REs:
            return text
        for re_c in REs:
            text = re_c.sub('', text)
        return text


def getBlocks(text):
    s = 0
    for m in re.finditer("[{}]", text):
        if m.group() == '{':
            if s == 0:
                start = m.start()
            s += 1
        else:
            s -= 1
        if s == 0:
            yield (start, m.end())


def clearClassName(name):
    return name.split(':')[0].strip()  # remove inheritance and spaces


def parseRawScope(text):
    entries = []
    for type_with_junk in _regexps.inlined.finditer(text):
        entry_type = _regexps.type_names[type_with_junk.group('TYPE_NAME')]
        name = clearClassName(type_with_junk.group('INST_NAME'))
        entries.append(entry_type(name))

    return entries


def parseScope(text):
    blocks = list(getBlocks(text))
    if not blocks:
        return parseRawScope(text)

    entries = set()
    prev_end = 0
    for (start, fin) in blocks:
        raw_scope_and_current_name = text[prev_end:start]
        new_entries = parseRawScope(raw_scope_and_current_name)
        if not new_entries:
            continue
        main_entry = new_entries[-1]
        new_entries = set(new_entries[:-1])
        entries |= new_entries

        main_entry.nested = parseScope(text[start+1:fin-1])
        entries.add(main_entry)

        prev_end = fin
    return entries | set(parseRawScope(text[prev_end:]))


def collectNontrivialIncludes(text):
    return [incl.group('INCLUDE_NAME') for incl in _regexps.nontrivial_include.finditer(text)]


def parseFile(filename):
    # TODO: templates?

    if not DEBUG % 2:
        filename = "test_cpp_features.h"

    with open(filename) as file:
        text = file.read()

    INCLUDES = collectNontrivialIncludes(text)

    text = _regexps.remove_by_re(text,
                                 # Remove comments, pragmas, \-carry, strings
                                 _regexps.multiline_comment,
                                 _regexps.backslash,
                                 _regexps.comment_or_pragma,
                                 _regexps.string,
                                 # Remove `friend class ...`
                                 _regexps.friend_class
                                 )

    if not DEBUG % 3:
        text = re.sub("((\r?\n){2,})", '\g<2>', text)  # \n+ ~> \n

    SCOPE = parseScope(text)

    return INCLUDES, File(filename, SCOPE)


def collectHeaders(trikRuntimeRoot):
    # TODO: handle ~/trikRuntime

    parsed_files = set()
    includes = set()
    for root, _, files in os.walk(trikRuntimeRoot):
        for filename in files:
            if filename.endswith(".h"):  # like: os.path.splitext(filename)[1] == '.h'
                incls, file = parseFile(os.path.join(root, filename))
                includes |= set(incls)
                parsed_files.add(file)

    return includes, parsed_files


def collectDirs(files):
    return {os.path.dirname(file.name) for file in files}


def collectIncludes(files):
    return {os.path.basename(file.name) for file in files}


def dumpToFile(root, filename='parsed.pickle', force=True):
    if not os.access(filename, os.F_OK) or force:
        with open(filename, 'wb') as file:
            pickle.dump((root, collectHeaders(root)), file)


if __name__ == "__main__":
    dumpToFile("/home/columpio/myTRIKStudio/src/trikRuntime/", 'parsed.pickle')
