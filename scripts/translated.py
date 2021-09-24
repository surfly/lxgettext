#!/usr/bin/env python3
# flake8: noqa
'''
translated.py <pofile>... > translated.txt
extract all translated messages with comments
'''

import polib
import sys


def extract_translated(filenames):
    s = ''
    entries = []
    for filename in filenames:
        entries.extend(polib.pofile(filename))
    entries = sorted(entries, key=lambda entry: entry.msgid.lower())
    for entry in entries:
        if entry.obsolete or not entry.translated():
            continue
        if entry.comment:
            for line in entry.comment.split('\n'):
                s += "# {}\n".format(line)
        if entry.tcomment:
            for line in entry.tcomment.split('\n'):
                s += "#. {}\n".format(line)
        if entry.flags:
            s += "#, {}\n".format(" ".join(entry.flags))
        s += '{}\n> {}\n\n'.format(entry.msgid, entry.msgstr)
    return s


if __name__ == "__main__":
    print(extract_translated(sys.argv[1:]), end='')
