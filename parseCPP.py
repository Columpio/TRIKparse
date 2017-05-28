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
    extra_declaration = re.compile(r";\s*\S")

    # Templates
    template = re.compile(r"\btemplate\b")
    template_typeblock_start = re.compile(r"\s*<")
    name_of_template_class = re.compile(r"^\s*\b%s[^;]+" % Class.typename())

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


def collectCodeBlocks(text):
    def deep_structure(blocks, start=0, fin=float("inf")):
        out = {}
        while blocks:
            block = blocks[-1]
            (b_st, b_fin) = block
            if start <= b_st and b_fin < fin:  # block is inside us
                blocks.pop()  # remove it and inspect it's structure
                out[(b_st-start, b_fin-start)] = deep_structure(blocks, b_st, b_fin)
            else:  # block is our neighbour
                return out
        return out

    # "{{}{}}" ~> [(1, 3), (3, 5), (0, 6)] (indexes of beginnings and ends of scopes)
    blocks = []
    stack = []
    for m in re.finditer(r'[{}]', text):
        if m.group() == '{':
            stack.append(m.start())
        else:
            blocks.append((stack.pop(), m.end()))

    return deep_structure(sorted(blocks, reverse=True))  # return nested structure


def collectTypeBlock(text):
    """typeblock is `<class Tuple, typename T, int k>`"""
    s = 0
    for m in re.finditer(r'[<>]', text):
        if m.group() == '<':
            if s == 0:
                start = m.start()
            s += 1
        else:
            s -= 1
        if s == 0:
            yield (start, m.end())


def addMaxDeclaration(d, entry):
    if len(d.setdefault(entry.name, entry)) < len(entry):
        d[entry.name] = entry


def setFirstMaxUnion(d1, d2):
    for name in d2:
        addMaxDeclaration(d1, d2[name])
    return d1


def clearClassName(name):
    return name.split(':')[0].strip()  # remove inheritance and spaces


def removeTemplates(text):
    def skipTypeBlock(fragment):
        """ returns fragment without starting TypeBlock
            TypeBlock is something like `<class Tuple, typename T, int k>` """
        _, typeblock_end = next(collectTypeBlock(fragment))  # should not be empty
        fragment = fragment[typeblock_end:]  # skip typeblock (see `collectTypeBlocks`)
        return fragment

    template_match = _regexps.template.search(text)

    new_text = []
    while True:
        if not template_match:
            new_text.append(text)
            return True, ''.join(new_text)  # text ends with NOT template declaration

        (start, fin) = template_match.span()
        new_text.append(text[:start])  # template-free code

        text = text[fin:]  # skip: `template <> struct ..` -> ` <> struct ..`
        if _regexps.template_typeblock_start.match(text):  # if starts with `  <` (so typeblock)
            text = skipTypeBlock(text)
        text = _regexps.name_of_template_class.sub('', text, count=1)  # `struct Name; sth` -> `; sth`

        if not text:
            return False, ''.join(new_text)  # text ends with template declaration

        template_match = _regexps.template.search(text)  # loop


def parsePlainScope(text):
    need_parse_next_block, text = removeTemplates(text)

    entries = {}

    if not need_parse_next_block:  # template was before {}, so just collect plain names
        for type_with_junk in _regexps.inlined.finditer(text):
            entry_type = _regexps.type_names[type_with_junk.group('TYPE_NAME')]
            name = clearClassName(type_with_junk.group('INST_NAME'))
            addMaxDeclaration(entries, entry_type(name))
        return None, entries  # == <it was template before {}>, collected entries

    last_entry = Entry(None)
    last_end = -1
    for type_with_junk in _regexps.inlined.finditer(text):
        last_end = type_with_junk.end()  # so we could know if we really have LAST declaration before {}
        entry_type = _regexps.type_names[type_with_junk.group('TYPE_NAME')]
        name = clearClassName(type_with_junk.group('INST_NAME'))
        addMaxDeclaration(entries, last_entry)
        last_entry = entry_type(name)

    if last_entry:
        entries.pop(None)  # if we entered `for` loop, we put `Entry(None)`
        if not _regexps.extra_declaration.search(text[last_end:]):  # our declaration is the last
            return last_entry, entries

        addMaxDeclaration(entries, last_entry)  # if our decl is not last then it is equal to others

    return None, entries


def parseScope(text, codeBlocks):
    entries = {}
    prev_end = 0
    for codeBlock in sorted(codeBlocks.keys()):
        (start, fin) = codeBlock
        raw_scope_and_current_name = text[prev_end:start]
        # parse before {}
        main_entry, new_entries = parsePlainScope(raw_scope_and_current_name)
        setFirstMaxUnion(entries, new_entries)

        prev_end = fin
        if not main_entry:  # not a valid class, namespace,.. (sth like: `int main() {..}` -- not class decl)
            continue

        # parse inside {}
        main_entry.nested = parseScope(text[start:fin], codeBlocks[codeBlock])
        addMaxDeclaration(entries, main_entry)

    # parse after last {}
    last_entry, new_entries = parsePlainScope(text[prev_end:])
    if last_entry:
        addMaxDeclaration(new_entries, last_entry)

    return set(setFirstMaxUnion(entries, new_entries).itervalues())


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

    codeBlocks = collectCodeBlocks(text)
    SCOPE = parseScope(text, codeBlocks)

    return File(filename, SCOPE, local_includes, global_includes)
