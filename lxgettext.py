import argparse
import datetime
import os
import re

import polib

COLOUR_GREEN = '\033[92m'
COLOUR_END = '\033[0m'

gettext_re = re.compile("""\gettext\(['"](.+?)['"]\)""")

now = datetime.datetime.today().strftime("%Y-%m-%d %X%z")

INFO_TEMPLATE = """#: {occurrence}
msgid "{msgid}"
"""


def valid_path(path):
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError("File %s does not exist" % path)
    return path


def get_args():
    parser = argparse.ArgumentParser("Extract gettext records from the files using `gettext(...)` as a keyword")
    parser.add_argument(
        "path",
        metavar="PATH",
        nargs="+",
        type=valid_path,
        action='store',
        help='Path to the file to extract gettext from'
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
    args = parser.parse_args()
    return args


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


def is_new_entry(msgid, po_obj):
    """
    Check if the entry already exists in po file
    """
    result = True
    for entry in po_obj:
        if entry.msgid == msgid:
            result = False
            break
    return result


def get_occurrences(msgid, data, filename):
    """
    Get message position in the source file
    """
    occurrences = []
    if msgid in data:
        pos = 0
        while pos != -1:
            pos = data.find(msgid, pos + 1)
            if pos != -1:
                line = data[:pos].count("\n")
                occurrences.append((filename, line))
    return occurrences


def update_occurrences(po_obj, data, filename):
    """
    Update message occurrence
    """
    for entry in po_obj:
        occurrences = get_occurrences(entry.msgid, data, filename)
        if occurrences:
            entry.occurrences = occurrences


def generate_po(data, filename, args):
    """
    Generates po file with messages to translate
    """
    matches = gettext_re.findall(data)
    new_entries = 0

    if args.output:
        # Write data to po file
        #
        # Create new po file if it does not exist
        if not os.path.exists(args.output):
            po = polib.POFile()
            po.save(args.output)

        po = polib.pofile(args.output)
        for match in matches:
            if is_new_entry(match, po):
                new_entries = new_entries + 1
                entry = polib.POEntry(msgid=match, msgstr="")
                po.append(entry)
        update_occurrences(po, data, filename)
        update_metadata(po, args)
        po.save()
        result = "  %s new, %s total" % (new_entries, len(matches))
        if new_entries > 0:
            result = COLOUR_GREEN + result + COLOUR_END
        return result
    else:
        # Show captured data
        info = ""
        for match in matches:
            occurrence = get_occurrences(match, data, filename)
            info = info + INFO_TEMPLATE.format(
                occurrence=", ".join("%s:%s" % (fn, ln) for (fn, ln) in occurrence),
                msgid=match
            )
        return info


def main(args):
    for item in args.path:
        print("%s:" % item)
        with open(item, "rb") as f:
            data = f.read()
        result = generate_po(data, item, args)
        print(result)


if __name__ == '__main__':
    args = get_args()
    main(args)
