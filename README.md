# TRIKparse
Retrieves all class names and namespaces from headers in root
# Usage
+ One can use `collectHeaders(root)` function to collect all information from headers in `root` directory. This function returns `tuple(includes, parsed_files)` where
+ + `includes` is typeof `Set[str]`, and contents all names from `#include <name>` from all headers.
+ + `parsed_files` is typeof `Set[File]`, it can be used to look for class declarations from file.   
+ `dumpToFile(root, filename)` allows user to dump (using `pickle`) call to `collectHeaders` to database with name `filename` for further usage (provided with `loadFromFile` of `simpleAPI.py`)
# Example
folder/sth.h:
```
#include <QCore>
#include <QString>

namespace NS {
    class A {
        class B;
    }
}
```   
myscript.py:
```
from TRIKparse import *

includes, parsed_files = collectHeaders("folder")

print(includes)
print(parsed_files)
myfile = parsed_files.pop()
print(myfile.scope)
ns = myfile.scope.pop()
print(ns.nested)
a = ns.nested.pop()
print(a.nested)
```
output:
```
set(['QCore', 'QString'])
set([[File test_cpp_features.h: 1 entries in global scope]])
set([[Namespace NS : size = 1]])
set([[Class A : size = 1]])
[[Class B]]
```
