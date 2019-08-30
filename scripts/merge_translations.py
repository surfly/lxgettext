#!/usr/bin/env python3
'''
merge_translations.py <output_locale_dir> <input_locale_dir>...
compile several django projects' PO files into one
'''

import polib

from functools import reduce
from operator import iconcat
from pathlib import Path
from sys import argv, exit

default_metadata = {
    "Project-Id-Version": "PACKAGE VERSION",
    "Report-Msgid-Bugs-To": "",
    "POT-Creation-Date": "2019-08-02 09:27+0000",
    "PO-Revision-Date": "YEAR-MO-DA HO:MI+ZONE",
    "Last-Translator": "FULL NAME <EMAIL@ADDRESS>",
    "Language-Team": "LANGUAGE <LL@li.org>",
    "Language": "",
    "MIME-Version": "1.0",
    "Content-Type": "text/plain; charset=UTF-8",
    "Content-Transfer-Encoding": "8bit",
}


class Stats():
    def __init__(self):
        self.empty_merges = 0
        self.trivial_merges = 0
        self.conflict_merges = 0

    def __str__(self):
        w = max(len(str(x)) for x in (self.empty_merges, self.trivial_merges, self.conflict_merges))
        return '\n'.join([
            f"Strings with no translations: {self.empty_merges:{w}}",
            f"Strings with one translation: {self.trivial_merges:{w}}",
            f"Strings with > 1 translation: {self.conflict_merges:{w}}",
        ])

    def __add__(self, other):
        ret = self.__class__()
        ret.empty_merges = self.empty_merges + other.empty_merges
        ret.trivial_merges = self.trivial_merges + other.trivial_merges
        ret.conflict_merges = self.conflict_merges + other.conflict_merges
        return ret


def combine_strings(strings: [str]) -> str or None:
    return '\n'.join(s for s in strings if s)


def combine_flags(flag_lists: [str]) -> list([str]):
    return list(reduce(lambda x, y: x.union(y), (set(fl) for fl in flag_lists)))


def choose_string(keyname: str, key: str, choices: list([str])):
    while True:
        print(f"There's more than one {keyname} available for the string:", f'"{key}"', sep='\n', end='\n\n')

        for i, choice in enumerate(choices):
            print(f'{i + 1}:', f'"{choice}"', sep='\n', end='\n\n')

        chosen = None
        while chosen is None:
            try:
                num = input("Which one? (or respond 'e' to edit) ").strip().lower()
                if num == 'e':
                    print(
                        f"Type a new {keyname} (without surrounding quotes). End by pressing",
                        f"Return/Enter twice. For an empty {keyname}, just press Return/Enter now.",
                        "You'll get a chance to confirm before submitting.",
                        "",
                        f"Enter {keyname}:",
                        sep='\n'
                    )

                    lines = []
                    chosen = None
                    while not lines or lines[-1]:
                        lines.append(input())
                    chosen = '\n'.join(lines[:-1])
                else:
                    chosen = choices[int(num) - 1]
            except (ValueError, IndexError):
                print(f"...sorry, what? Type a {keyname} number or 'e' and press Return/Enter.")

        print(f"New {keyname} is:", f'"{chosen}"', sep='\n')
        choice = input("\nOkay? [y/N] ").strip().lower()
        if choice == 'y':
            print('-' * 80)
            return chosen
        else:
            continue


def choose_translation(entries: [polib.POEntry], plural=False, stats=None) -> str:
    '''
    Given a list of PO file entries with the same msgid, return some string
    to use as a msgstr. If there's only one truthy msgstr/msgstr_plural,
    return it. Otherwise, prompt the user to choose one.
    '''

    assert(entries)

    # DEBUG msgids have to be the same
    assert(all(entries[0].msgid == e.msgid for e in entries))
    assert(all(entries[0].msgid_plural == e.msgid_plural for e in entries))

    # extract translation strings
    attr = 'msgstr_plural' if plural else 'msgstr'
    translations = sorted(set(getattr(e, attr) for e in entries if getattr(e, attr)))

    # trivial cases
    if len(translations) == 0:
        if stats:
            stats.empty_merges += 1
        return ''
    elif len(translations) == 1:
        if stats:
            stats.trivial_merges += 1
        return translations[0]

    # if there's more than one unique translation, we must consult the user
    translation = choose_string('translation', entries[0].msgid, translations)
    if stats:
        stats.conflict_merges += 1
    return translation


def combine_poentries(entries: list([polib.POEntry]), stats=None) -> polib.POEntry or None:
    '''Might require user input in non-trivial cases!'''

    # trivial cases
    assert(entries)
    if len(entries) == 1:
        # caution: this is not a new object!
        if stats:
            stats.trivial_merges += 1
        return entries[0]

    # DEBUG msgids have to be the same
    assert(all(entries[0].msgid == e.msgid for e in entries))
    assert(all(entries[0].msgid_plural == e.msgid_plural for e in entries))

    return polib.POEntry(
        msgid=entries[0].msgid,
        # msgid_plural=
        msgstr=choose_translation(entries, stats=stats),
        # msgstr_plural=
        msgctxt=combine_strings(e.msgctxt for e in entries),
        obsolete=all(e.obsolete for e in entries),
        # encoding=
        comment=combine_strings(e.comment for e in entries),
        tcomment=combine_strings(e.tcomment for e in entries),
        occurrences=reduce(iconcat, (e.occurrences for e in entries), []),
        flags=combine_flags(e.flags for e in entries),
        previous_msgctxt=combine_strings(e.previous_msgctxt for e in entries),
        previous_msgid=combine_strings(e.previous_msgid for e in entries),
        previous_msgid_plural=combine_strings(e.previous_msgid_plural for e in entries),
        # linenum=
    )


def combine_headers(po_files: [polib.POFile], language=None) -> polib.POFile:
    '''Combines the headers of several PO files into a new, empty PO file.'''
    ret = polib.POFile()

    # populate with default metadata
    ret.metadata.update(default_metadata)
    if language:
        ret.metadata["Language"] = language

    headers = dict()
    for po_file in po_files:
        for k, v in po_file.ordered_metadata():
            if k not in default_metadata:
                try:
                    headers[k].append(v)
                except KeyError:
                    headers[k] = [v]

    for k, v in headers.items():
        v = sorted(set(v))
        ret.metadata[k] = v[0] if len(v) == 1 else choose_string('header value', k, v)

    return ret


def combine_pofiles(po_files: list([polib.POFile]), language=None, stats=None) -> polib.POFile:
    '''Combines on-disk PO files (headers and entries) into a new PO file.'''
    new_po_file = combine_headers(po_files, language=language)

    translations = dict()
    for po_file in po_files:
        for entry in po_file:

            # FIXME: implement merging plural forms
            if entry.msgid_plural:
                raise NotImplementedError(
                    "Merging plural forms is not implemented yet."
                    + f' Offending entry is in {po_file.fpath} under msgid "{entry.msgid}".'
                )

            try:
                translations[entry.msgid].append(entry)
            except KeyError:
                translations[entry.msgid] = [entry]

    new_po_file.extend(combine_poentries(es, stats=stats) for es in translations.values())

    # sort alphabetically: ignore case, but lowercase wins ties against upper
    # e.g. apple, Apple, aztec, Banana, carrot, Echo, email, eMail, ...
    new_po_file.sort(key=lambda x: x.msgid, reverse=True)
    new_po_file.sort(key=lambda x: x.msgid.lower())

    return new_po_file


def get_languages(locale_paths: [Path]) -> list(['ISO 639-1 language code']):
    return sorted(set(
        p.name
        for locale_path in locale_paths
        for p in Path(locale_path).iterdir()
        if p.is_dir()
    ))


if __name__ == "__main__":
    if len(argv) < 3:
        print(__doc__.strip())
        exit(2)

    new_locale_path = Path(argv[1])
    if new_locale_path.exists():
        print("Output directory", new_locale_path, "already exists!")
        exit(3)

    locale_paths = [Path(x) for x in argv[2:]]
    if not locale_paths:
        raise IndexError()

    # all source locales must be existing files
    for locale_path in locale_paths:
        if not locale_path.exists():
            print("Input directory", locale_path, "does not exist!")
            exit(1)

    try:
        languages = get_languages(locale_paths)

        totals = Stats()
        outputs = dict()
        for language in languages:
            langstat = Stats()

            po_paths = [f / language / 'LC_MESSAGES' / 'django.po' for f in locale_paths]
            po_files = [polib.pofile(str(p)) for p in po_paths if p.exists()]

            outputs[language] = combine_pofiles(po_files, language=language, stats=langstat)

            print(f"{language.upper()} SUMMARY", langstat, '', '-' * 80, '', sep='\n')
            totals += langstat

        print("OVERALL SUMMARY", totals, '=' * 80, '', f"Writing files to {new_locale_path}...", sep='\n')

    except KeyboardInterrupt:
        print("\nExiting cleanly...")
        exit(0)

    try:
        for language, pofile in outputs.items():
            new_pofile_path = new_locale_path / language / 'LC_MESSAGES'
            new_pofile_path.mkdir(parents=True, exist_ok=False)
            new_pofile_path /= 'django.po'
            with new_pofile_path.open('x') as f:
                f.write(str(pofile))
    except KeyboardInterrupt:
        pass

    print("Done!")
