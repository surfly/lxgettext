# coding: utf8
# flake8: E501

import contextlib
import os
import shutil
import tempfile
import unittest

from lxgettext.lxgettext import generate_po, get_occurrences, update_po


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
        data = "\n\ngettext('banana')\n"
        msgid = "banana"
        expected = [('file.js', 3)]
        result = get_occurrences(msgid, data, "file.js")
        self.assertEqual(expected, result)

    def test_multiple(self):
        data = "\n\ngettext('banana')\ngettext('banana')\n"
        msgid = "banana"
        expected = [('file.js', 3), ('file.js', 4)]
        result = get_occurrences(msgid, data, "file.js")
        self.assertEqual(expected, result)

    def test_fake(self):
        data = """
        There is a fake instance with name banana
        var a = gettext("banana");
        var banana;
        """
        msgid = "banana"
        expected = [('file.js', 3)]
        result = get_occurrences(msgid, data, "file.js")
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

    def assertHasLines(self, expected, result):
        '''
        Assert that result contains contiguous lines in `expected` ignoring
        indentation.
        '''
        lines = expected.strip().split('\n')
        expected = '\n'.join(line.strip() for line in lines)
        return self.assertIn(expected, result)

    def test_new(self):
        source = '''
            gettext('test');
        '''
        expected = '''
            #: test:2
            msgid "test"
            msgstr ""
        '''

        with tmpdir() as d:
            path = os.path.join(d, 'xx.po')
            update_po(source, 'test', self.Args(path, prune=True))
            with open(path, 'r') as f:
                result = f.read()

        self.assertHasLines(expected, result)

    def test_empty_add(self):
        source = '''
            gettext('test');
        '''
        expected = '''
            #: test:2
            msgid "test"
            msgstr ""
        '''

        with tmpfile() as path:
            update_po(source, 'test', self.Args(path, prune=True))
            with open(path, 'r') as f:
                result = f.read()

        self.assertHasLines(expected, result)

    def test_existing_add(self):
        old_po = '''
            #: test:100
            msgid "already here"
            msgstr "ereh ydaerla"
        '''
        source = '''
            gettext('already here');
            gettext('to be added');
        '''
        expected = '''
            #: test:2
            msgid "already here"
            msgstr "ereh ydaerla"

            #: test:3
            msgid "to be added"
            msgstr ""
        '''

        with tmpfile(old_po) as path:
            update_po(source, 'test', self.Args(path, prune=True))
            with open(path, 'r') as f:
                result = f.read()

        self.assertHasLines(expected, result)

    def test_existing_prune_partial(self):
        old_po = '''
            #: test:100
            msgid "test"
            msgstr "tset"

            #: test:200
            msgid "removed"
            msgstr "devomer"
        '''
        source = '''
            gettext('test');
        '''
        expected = '''
            #: test:2
            msgid "test"
            msgstr "tset"
        '''

        with tmpfile(old_po) as path:
            update_po(source, 'test', self.Args(path, prune=True))
            with open(path, 'r') as f:
                result = f.read()

        self.assertHasLines(expected, result)

    def test_existing_prune_all(self):
        old_po = '''
            msgid "removed"
            msgstr "devomer"
        '''
        source = '''
        '''

        with tmpfile(old_po) as path:
            update_po(source, 'test', self.Args(path, prune=True))
            with open(path, 'r') as f:
                result = f.read()

        self.assertNotIn('msgid "removed"', result)


if __name__ == '__main__':
    unittest.main()
