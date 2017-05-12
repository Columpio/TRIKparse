from __future__ import print_function
import pickle


class Entry(object):
    def __init__(self, name):
        if name:
            self.name = name.split()[-1]  # remove macros and stuff
        else:  # anonymous classes ?!?
            self.name = name
        self.nested = set()

    def __repr__(self):
        if self.nested:
            return "[%s %s : size = %d]" % (self.__class__.__name__, self.name, len(self.nested))
        else:
            return "[%s %s]" % (self.__class__.__name__, self.name)

    @classmethod
    def typename(cls):
        return cls.__name__.lower()


class Namespace(Entry):
    def __init__(self, name):
        super(Namespace, self).__init__(name)


class Class(Entry):
    def __init__(self, name):
        super(Class, self).__init__(name)

    def isInterface(self):
        return 'interface' in self.name.lower()

    @staticmethod
    def typename():
        return "(?:class|struct)"


class Enum(Entry):
    def __init__(self, name):
        super(Enum, self).__init__(name)


class File(object):
    def __init__(self, name, scope, local_includes=None, global_includes=None):
        self.name = name
        self.scope = scope
        self.local_includes  = local_includes  or set()
        self.global_includes = global_includes or set()

    def __repr__(self):
        return "[File %s: %d entries in global scope]" % (self.name, len(self.scope))


def loadFromFile(filename="parsed.pickle"):
    with open(filename, 'rb') as file:
        (root, files) = pickle.load(file)

    return root, files


if __name__ == '__main__':
    loadFromFile("parsed.pickle")
