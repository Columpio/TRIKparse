# TRIKparse
Retrieves all class names and namespaces from headers in root
# Usage
+ One can use `collectHeaders(root)` function to collect all information from headers in `root` directory. This function returns `parsed_files` where
+ + `parsed_files` is typeof `Set[File]`, it can be used to look for class declarations from file.   

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
from parseCPP import *
form TRIKparse import *

parsed_files = collectHeaders("folder")

print(parsed_files)
myfile = parsed_files.pop()
print(myfile.global_includes)
print(myfile.scope)
ns = myfile.scope.pop()
print(ns.nested)
a = ns.nested.pop()
print(a.nested)
```
output:
```
set([[File test_cpp_features.h: 1 entries in global scope]])
set(['QCore', 'QString'])
set([[Namespace NS : size = 1]])
set([[Class A : size = 1]])
set([[Class B]])
```
