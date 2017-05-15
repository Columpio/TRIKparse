from __future__ import print_function
import re
from simpleAPI import *


class _regexps:
    include = re.compile(r"#include\s+(?P<INCLUDE_NAME>[\"<].+[\">])")

    # Garbage
    multiline_comment = re.compile("/\*.*\*/", flags=re.DOTALL)
    backslash = re.compile(r"\\\s*\n")
    comment_or_pragma = re.compile(r"(//|#).*$", flags=re.MULTILINE)
    _string = lambda c: r"((?<!\\){}.*?(?<!\\){})".format(c, c)
    string = re.compile('|'.join([_string("\""), _string("\'")]))

    friend_class = re.compile(r"\bfriend\s+class\s")

    # Raw declarations, like `enum x;`, no even `class a {};`
    type_names = {
        "namespace": Namespace,
        "struct": Class,
        "class": Class,
        "enum": Enum
    }
    inlined = re.compile(r"\b(?P<TYPE_NAME>%s)\s(?P<INST_NAME>[^;]*)" %
                         '|'.join(Type.typename() for Type in type_names.values()))

    @staticmethod
    def remove_by_re(text, *REs):
        if not REs:
            return text
        for re_c in REs:
            text = re_c.sub('', text)
        return text


def metaCollectBlocks(opened, closed):
    block_re = re.compile("[%s%s]" % (opened, closed))

    def collectBlocks(text):
        s = 0
        for m in block_re.finditer(text):
            if m.group() == opened:
                if s == 0:
                    start = m.start()
                s += 1
            else:
                s -= 1
            if s == 0:
                yield (start, m.end())

    return collectBlocks

collectCodeBlocks = metaCollectBlocks('{', '}')
collectTypeBlocks = metaCollectBlocks('<', '>')  # typeblock is `<class Tuple, typename T, int k>`


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
    entries = set()
    prev_end = 0
    for (start, fin) in collectCodeBlocks(text):
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


def collectIncludesFromText(text):
    all_includes = {incl.group('INCLUDE_NAME') for incl in _regexps.include.finditer(text)}

    local_includes, global_includes = set(), set()
    for include in all_includes:
        if include[0] == '"':
            local_includes.add(include[1:-1])
        else:
            global_includes.add(include[1:-1])

    return local_includes, global_includes


def parseFile(filename):
    # TODO: templates?

    with open(filename) as file:
        text = file.read()

    local_includes, global_includes = collectIncludesFromText(text)

    text = _regexps.remove_by_re(text,
                                 # Remove comments, pragmas, \-carry, strings
                                 _regexps.multiline_comment,
                                 _regexps.backslash,
                                 _regexps.comment_or_pragma,
                                 _regexps.string,
                                 # Remove `friend class ...`
                                 _regexps.friend_class
                                 )

    SCOPE = parseScope(text)

    return File(filename, SCOPE, local_includes, global_includes)
