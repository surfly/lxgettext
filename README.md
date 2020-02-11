lxgettext
====
Extract strings wrapped in gettext("...")

# Usage
```
usage: Extract gettext records from the files using `gettext(...)` as a keyword
       [-h] [-p] [-o OUTPUT] [-v VERSION] [-l LANGUAGE] PATH [PATH ...]

positional arguments:
  PATH                  Path to the file to extract gettext from

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Path to the *po file
  -p, --prune           Remove entries in OUTPUT with no corresponding `msgid`
                        in any of the input PATHs. Use this to tidy up PO
                        files as strings are removed from code.
  -v VERSION, --version VERSION
                        Version of the source file
  -l LANGUAGE, --language LANGUAGE
                        Language of the source file

```

## Extract strings from the `*.js` and `*.vue` files inside the directory and save the result to the `nl.po` file
```bash
find sources/ -iname "*.js" -o -iname "*.vue" | xargs lxgettext --output=nl.po --version=10 --language=nl
```
