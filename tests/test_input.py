# coding: utf8
# flake8: E501

import contextlib
import os
import shutil
import tempfile
import unittest

from lxgettext.lxgettext import generate_po, get_msgids, update_po


class TestInput(unittest.TestCase):
    def setUp(self):
        self.path = "__init__.py"

    def test_lonely_warrior_dq(self):
        data = """gettext("Warrior")"""
        expected = 'msgid "Warrior"'
        result = generate_po(data, self.path)
        self.assertIn(expected, result)

    def test_lonely_warrior_sq(self):
        data = """gettext('Warrior')"""
        expected = 'msgid "Warrior"'
        result = generate_po(data, self.path)
        self.assertIn(expected, result)

    def test_sentence(self):
        data = """gettext('I want ice cream')"""
        expected = 'msgid "I want ice cream"'
        result = generate_po(data, self.path)
        self.assertIn(expected, result)

    def test_quotes(self):
        data = """gettext('H"O"T')"""
        expected = 'msgid "H"O"T"'
        result = generate_po(data, self.path)
        self.assertIn(expected, result)

    def test_widget(self):
        data = """blockPage(Surfly.i18n.gettext('Cobrowsing session is opened in a separate tab.') + " " +"""
        expected = 'msgid "Cobrowsing session is opened in a separate tab."'
        result = generate_po(data, self.path)
        self.assertIn(expected, result)

    def test_widget2(self):
        data = """
                blockPage(Surfly.i18n.gettext('Cobrowsing session is opened in a separate tab.') + " " +
                Surfly.i18n.gettext('Please do not close this window while it is active.'),
        """
        result = generate_po(data, self.path)
        self.assertIn('msgid "Cobrowsing session is opened in a separate tab."', result)
        self.assertIn('msgid "Please do not close this window while it is active."', result)

    def test_double(self):
        data = """
                gettext("Lonely")
                gettext("Warrior")
        """
        result = generate_po(data, self.path)
        self.assertIn('msgid "Warrior"', result)
        self.assertIn('msgid "Lonely"', result)

    def test_double2(self):
        data = """
                :aria-label="open.publishing ? $gettext('Leave videochat') : $gettext('Join videochat')">
        """
        result = generate_po(data, self.path)
        self.assertIn('msgid "Leave videochat"', result)
        self.assertIn('msgid "Join videochat"', result)

    def test_double_string(self):
        data = """
    if (!this.options.ui_off && !this.$store.state.delayedEnd) {
        let msg = this.$gettext('You have an active cobrowsing session, are you sure you want to close this window?');
        e.returnValue = msg;
        return msg;
                }
        """
        result = generate_po(data, self.path)
        self.assertIn(
            'msgid "You have an active cobrowsing session, are you sure you want to close this window?"', result
        )

    def test_space(self):
        data = """gettext("Warrior")"""
        expected = 'msgid "Warrior"'
        result = generate_po(data, self.path)
        self.assertIn(expected, result)

    def test_utf(self):
        data = """gettext("банана")"""
        expected = 'msgid "банана"'
        result = generate_po(data, self.path)
        self.assertIn(expected, result)


class TestOccurrences(unittest.TestCase):
    def test_simple(self):
        data = '''
            gettext('banana')
        '''
        expected = [('banana', 2)]

        lines = data.split('\n')
        result = list(get_msgids(lines))
        self.assertEqual(expected, result)

    def test_multiple(self):
        data = '''
            gettext('banana')
            gettext("banana")
        '''
        expected = [('banana', 2), ('banana', 3)]

        lines = data.split('\n')
        result = list(get_msgids(lines))
        self.assertEqual(expected, result)

    def test_fake(self):
        data = '''
            Here are some fake instances with name banana
            var a = gottext("banana");
            let x = gettext "banana";
            const b = gettext(banana);
            var banana;
        '''
        expected = []

        lines = data.split('\n')
        result = list(get_msgids(lines))
        self.assertEqual(expected, result)


@contextlib.contextmanager
def tmpfile(contents=None):
    try:
        with tempfile.NamedTemporaryFile('w', delete=False) as f:
            filepath = f.name
            if contents is not None:
                f.write(contents)
        yield filepath
    finally:
        os.remove(filepath)


@contextlib.contextmanager
def tmpdir():
    try:
        dirname = tempfile.mkdtemp()
        yield dirname
    finally:
        shutil.rmtree(dirname)


class TestFilesystem(unittest.TestCase):

    class Args(object):
        def __init__(self, output, prune=False):
            self.output = output
            self.prune = prune
            self.version = 'test'
            self.language = 'xx'

    def assertContents(self, expected, result):
        # get the PO file after the header
        _, _, result = result.partition("\n\n")

        # ignore indentation in expected string
        if expected:
            lines = expected.strip().split('\n')
            expected = ''.join(line.lstrip() + '\n' for line in lines)

        return self.assertEqual(expected, result)

    def test_new(self):
        source = '''
            gettext('test');
        '''
        expected = '''
            #: {sourcepath}:2
            msgid "test"
            msgstr ""
        '''

        with tmpfile(source) as sourcepath:
            expected = expected.format(sourcepath=sourcepath)
            with tmpdir() as outpath:
                outpath = os.path.join(outpath, 'xx.po')
                update_po([sourcepath], self.Args(outpath, prune=True))
                with open(outpath, 'r') as f:
                    result = f.read()

        self.assertContents(expected, result)

    def test_empty_add(self):
        old_po = ''
        source = '''
            gettext('test');
        '''
        expected = '''
            #: {sourcepath}:2
            msgid "test"
            msgstr ""
        '''

        with tmpfile(source) as sourcepath:
            expected = expected.format(sourcepath=sourcepath)
            with tmpfile(old_po) as popath:
                update_po([sourcepath], self.Args(popath, prune=True))
                with open(popath, 'r') as f:
                    result = f.read()

        self.assertContents(expected, result)

    def test_existing_add(self):
        old_po = '''
            #: oldsource:100
            msgid "already here"
            msgstr "ereh ydaerla"
        '''
        source = '''
            gettext('already here');
            gettext('to be added');
        '''
        expected = '''
            #: {sourcepath}:2
            msgid "already here"
            msgstr "ereh ydaerla"

            #: {sourcepath}:3
            msgid "to be added"
            msgstr ""
        '''

        with tmpfile(source) as sourcepath:
            expected = expected.format(sourcepath=sourcepath)
            with tmpfile(old_po) as popath:
                update_po([sourcepath], self.Args(popath, prune=True))
                with open(popath, 'r') as f:
                    result = f.read()

        self.assertContents(expected, result)

    def test_existing_prune_partial(self):
        old_po = '''
            #: oldsource:100
            msgid "test"
            msgstr "tset"

            #: oldsource:200
            msgid "removed"
            msgstr "devomer"
        '''
        source = '''
            gettext('test');
        '''
        expected = '''
            #: {sourcepath}:2
            msgid "test"
            msgstr "tset"
        '''

        with tmpfile(source) as sourcepath:
            expected = expected.format(sourcepath=sourcepath)
            with tmpfile(old_po) as popath:
                update_po([sourcepath], self.Args(popath, prune=True))
                with open(popath, 'r') as f:
                    result = f.read()

        self.assertContents(expected, result)

    def test_multifile(self):
        old_po = '''
            #: oldsource:100
            msgid "test2"
            msgstr "2tset"

            #: oldsource:200
            msgid "removed"
            msgstr "devomer"
        '''
        sources = [
            "~" * 100,
            "gettext('test1');",
            "gettext('test2');",
            "gettext('test3');",
            "",
        ]
        expected = '''
            #: {2}:1
            msgid "test2"
            msgstr "2tset"

            msgid "removed"
            msgstr "devomer"

            #: {1}:1
            msgid "test1"
            msgstr ""

            #: {3}:1
            msgid "test3"
            msgstr ""
        '''

        with tmpdir() as dpath:

            # create each source file
            spaths = [os.path.join(dpath, "%d.js" % i) for i, _ in enumerate(sources)]
            expected = expected.format(*spaths)
            for source, spath in zip(sources, spaths):
                with open(spath, 'w') as f:
                    f.write(source)

            # write old PO file
            popath = os.path.join(dpath, 'xx.po')
            with open(popath, 'w') as f:
                f.write(old_po)

            # update PO file using new source files
            update_po(spaths, self.Args(popath))

            # check PO output
            with open(popath, 'r') as f:
                result = f.read()
            self.assertContents(expected, result)

    def test_multifile_prune(self):
        old_po = '''
            #: oldsource:100
            msgid "test1"
            msgstr "1tset"

            #: oldsource:200
            msgid "removed"
            msgstr "devomer"
        '''
        sources = [
            "",
            "gettext('test0');",
            "gettext('test1');",
            "gettext('test2');",
            "",
        ]
        expected = '''
            #: {1}:1
            msgid "test0"
            msgstr ""

            #: {2}:1
            msgid "test1"
            msgstr "1tset"

            #: {3}:1
            msgid "test2"
            msgstr ""
        '''

        with tmpdir() as dpath:

            # create each source file
            spaths = [os.path.join(dpath, "%d.js" % i) for i, _ in enumerate(sources)]
            expected = expected.format(*spaths)
            for source, spath in zip(sources, spaths):
                with open(spath, 'w') as f:
                    f.write(source)

            # write old PO file
            popath = os.path.join(dpath, 'xx.po')
            with open(popath, 'w') as f:
                f.write(old_po)

            # update PO file using new source files
            update_po(spaths, self.Args(popath, prune=True))

            # check PO output
            with open(popath, 'r') as f:
                result = f.read()
            self.assertContents(expected, result)

    def test_existing_prune_all(self):
        old_po = '''
            #: oldsource:2
            msgid "removed"
            msgstr "devomer"
        '''
        source = ''
        expected = ''

        with tmpfile(old_po) as path:
            update_po(source, self.Args(path, prune=True))
            with open(path, 'r') as f:
                result = f.read()

        self.assertContents(expected, result)


if __name__ == '__main__':
    unittest.main()
