import argparse
import io
import json
import os
import pprint

import polib

COLOUR_GREEN = '\033[92m'
COLOUR_END = '\033[0m'


def valid_path(path):
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError("File %s does not exist" % path)
    return path


def get_args():
    parser = argparse.ArgumentParser("Convert po file to the simple JSON file")
    parser.add_argument(
        "path",
        metavar="PATH",
        type=valid_path,
        action='store',
        help='Path to the po file'
    )
    parser.add_argument(
        '-o', '--output',
        default=False,
        action='store',
        help='Path to the *json file'
    )
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    po = polib.pofile(args.path)
    po_dict = {}
    for entry in po:
        if len(entry.msgstr) > 0:
            po_dict[entry.msgid] = entry.msgstr
    if args.output:
        with io.open(args.output, "w", encoding="utf8") as f:
            data = json.dumps(po_dict, f, ensure_ascii=False, sort_keys=True)
            f.write(unicode(data))
        print(COLOUR_GREEN + "%s: %s empty" % (args.output, len(po) - len(po_dict)) + COLOUR_END)
    else:
        pprint.pprint(po_dict)


if __name__ == '__main__':
    main()
