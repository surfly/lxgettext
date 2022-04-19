import argparse
import datetime
import io
import os
import re
from collections import OrderedDict

import polib

COLOUR_GREEN = '\033[92m'
COLOUR_END = '\033[0m'

KEYWORD = "gettext"
gettext_re = re.compile("""%s\\(['"](.+?)['"]\\)""" % KEYWORD)

now = datetime.datetime.today().strftime("%Y-%m-%d %X%z")

INFO_TEMPLATE = """#: {occurrence}
msgid "{msgid}"
msgstr ""
"""


def valid_path(path):
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError("File %s does not exist" % path)
    return path


def get_args():
    parser = argparse.ArgumentParser(
        "Extract gettext records from the files using `gettext(...)` as a "
        "keyword"
    )
    parser.add_argument(
        "path",
        metavar="PATH",
        nargs="+",
        type=valid_path,
        action='store',
        help='Path to the file to extract gettext from'
    )
    parser.add_argument(
        '-p', '--prune',
        action='store_true',
        help="Remove existing entries that have a msgid that doesn't "
        "correspond to any string in the input PATHs.",
    )
    parser.add_argument(
        '-o', '--output',
        default=False,
        action='store',
        help='Path to the *po file'
    )
    parser.add_argument(
        '-v', '--version',
        default=False,
        action='store',
        help='Version of the source file'
    )
    parser.add_argument(
        '-l', '--language',
        default=False,
        action='store',
        help='Language of the source file'
    )
    parser.add_argument(
        '--verbose',
        action='store_true'
    )
    args = parser.parse_args()
    return args


def get_number_of_entries(path):
    """
    Returns number of entries in the po file
    """
    count = 0
    if os.path.exists(path):
        po = polib.pofile(path)
        count = len(po)
    return count


def update_metadata(po, args):
    """
    Update po file metadata
    """
    metadata = {
        "Project-Id-Version": args.version,
        "Report-Msgid-Bugs-To": "support@surfly.com",
        "POT-Creation-Date": now,
        "PO-Revision-Date": now,
        "Last-Translator": "Admin <support@surfly.com>",
        "Language-Team": "LANGUAGE <support@surfly.com>",
        "Language": args.language,
        "MIME-Version": "1.0",
        "Content-Type": "text/plain; charset=utf-8",
        "Content-Transfer-Encoding": "8bit"
    }
    po.metadata.update(metadata)


def get_msgids(lines):
    '''Generates (match, lineno) pairs.'''
    for i, line in enumerate(lines, start=1):
        for match in gettext_re.findall(line):
            yield (match, i)


def update_po(paths, args):
    """
    Generates po file with messages to translate
    Write data to po file
    Create new po file if it does not exist
    """

    # msgid -> set( (path, lineno) )
    matches = OrderedDict()

    for path in paths:
        if args.verbose:
            print("%s:" % path)
        with io.open(path, 'r', encoding='utf8') as f:
            for match, i in get_msgids(f):
                try:
                    matches[match].add((path, i))
                except KeyError:
                    matches[match] = set([(path, i)])

    po = polib.pofile(args.output) if os.path.exists(args.output) \
        else polib.POFile()

    # remove old occurrences
    for entry in po:
        del entry.occurrences[:]

    entries = {entry.msgid: entry for entry in po}

    # remove all POEntries from the old PO file so we can start from scratch.
    # entries (and possible translations) are retained in the entries dict.
    if args.prune:
        del po[:]

    new_entries = 0
    for match, occurrences in matches.iteritems():

        # if the string was already listed in the POFile, keep the POEntry in
        # the POFile
        try:
            entry = entries[match]
            if args.prune:
                po.append(entry)

        # if we've encountered a new string, add that to the POFile
        except KeyError:
            new_entries += 1
            entry = polib.POEntry(msgid=match, msgstr="")
            entries[match] = entry
            po.append(entry)

        entry.occurrences = list(occurrences)

    update_metadata(po, args)
    po.save(args.output)
    result = "  %s new, %s total" % (new_entries, len(matches))
    if new_entries > 0:
        result = COLOUR_GREEN + result + COLOUR_END
    if args.verbose:
        print(result)


def generate_po(data, filename):
    """
    Generates po file with messages to translate
    """

    data = data.split('\n')

    # collect matches by msgid
    matches = OrderedDict()
    for msgid, i in get_msgids(data):
        try:
            matches[msgid].add(i)
        except KeyError:
            matches[msgid] = set([i])

    # Show captured data
    return "\n".join(
        INFO_TEMPLATE.format(
            msgid=msgid,
            occurrence=", ".join("%s:%s" % (filename, i) for i in linenos),
        )
        for msgid, linenos in matches.iteritems()
    )


def main():
    args = get_args()
    if args.output:
        entries_before = get_number_of_entries(args.output)
        update_po(args.path, args)
        entries_after = get_number_of_entries(args.output)
        message = "Entries: %s / %s" % (entries_before, entries_after)
        if entries_after > entries_before:
            message = COLOUR_GREEN + message + COLOUR_END
        if args.language:
            message = '[%s] %s' % (args.language, message)
        print(message)
    else:
        for item in args.path:
            with io.open(item, "r", encoding="utf8") as f:
                print(generate_po(f.read(), item))


if __name__ == '__main__':
    main()
