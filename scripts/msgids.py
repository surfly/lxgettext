#!/usr/bin/env python3
# flake8: noqa
'''
msgids.py <pofile>... > msgids.txt
extract all msgids with comments
'''

import polib
import sys


def extract_msgids(filename):
    s = ''
    po = polib.pofile(filename)
    for entry in po:
        if entry.obsolete:
            continue
        for source, line in entry.occurrences:
            s += "# {}:{}\n".format(source, line)
        if entry.comment:
            s += "# {}\n".format(entry.comment)
        if entry.tcomment:
            s += "#. {}\n".format(entry.tcomment)
        if entry.flags:
            s += "#, {}\n".format(" ".join(entry.flags))
        s += '"{}"\n\n'.format(entry.msgid)
    return s


if __name__ == "__main__":
    for filename in sys.argv[1:]:
        print(extract_msgids(filename), end='')
