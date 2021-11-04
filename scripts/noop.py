#!/usr/bin/env python3
# flake8: noqa
'''Usage:
  msgids.py POFILE [POFILE2] > NEW_POFILE

For each untranslated string, copy the msgid to the msgstr. If a second pofile
is mentioned on the command line, use the first one to determine which strings
are untranslated, but use the second one to actually produce the output.'''

import polib
import sys


def get_untranslated(filename: str) -> set:
    po = polib.pofile(filename)


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
    if len(sys.argv) not in (2, 3):
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    # load the original pofile, which will be edited to create the new one
    new_po = polib.pofile(sys.argv[-1])

    # determine which strings count as untranslated
    base_po = new_po if len(sys.argv) == 2 else polib.pofile(sys.argv[1])
    untranslated = set(entry.msgid for entry in base_po if not entry.msgstr)

    translated = []
    noopped = []
    new = []

    # noopify untranslated entries
    for entry in new_po:
        if entry.msgstr:
            translated.append(entry)
        elif entry.msgid in untranslated:
            entry.msgstr = entry.msgid
            noopped.append(entry)
        else:
            new.append(entry)

    # write new file to stdout
    print(new_po)

    print(f'{len(noopped)} entries no-opped. {len(new)} new strings left to translate. {len(translated)} entries already had translations.\n\nNew, untranslated entries:', file=sys.stderr)
    for entry in new:
        print(f'  - {repr(entry.msgid)[1:-1]}', file=sys.stderr)
    print('\nNo-opped entries:', file=sys.stderr)
    for entry in noopped:
        print(f'  - {repr(entry.msgid)[1:-1]}', file=sys.stderr)
