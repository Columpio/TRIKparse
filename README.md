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
REPL:
```
>>> from parseCPP import *
>>> from TRIKparse import *
>>> parsed_files = collectHeaders("folder")
>>> parsed_files
set([[File folder/sth.h: 1 entries in global scope]])
>>> myfile = parsed_files.pop()
>>> myfile.global_includes
set(['QCore', 'QString'])
>>> myfile.scope
set([[Namespace NS : set([[Class A : set([[Class B]])]])]])
>>> ns = myfile.scope.pop()
>>> ns.nested
set([[Class A : set([[Class B]])]])
>>> a = ns.nested.pop()
>>> a.nested
set([[Class B]])
```
