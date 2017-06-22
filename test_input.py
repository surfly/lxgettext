import unittest

from lxgettext import generate_po


class TestInput(unittest.TestCase):
    def setUp(self):
        class Args:
            output = None
            path = "__init__.py"

        self.args = Args()

    def test_lonely_warrior_dq(self):
        data = """gettext("Warrior")"""
        expected = 'msgid "Warrior"'
        result = generate_po(data, self.args.path, self.args)
        self.assertIn(expected, result)

    def test_lonely_warrior_sq(self):
        data = """gettext('Warrior')"""
        expected = 'msgid "Warrior"'
        result = generate_po(data, self.args.path, self.args)
        self.assertIn(expected, result)

    def test_sentence(self):
        data = """gettext('I want ice cream')"""
        expected = 'msgid "I want ice cream"'
        result = generate_po(data, self.args.path, self.args)
        self.assertIn(expected, result)

    def test_quotes(self):
        data = """gettext('H"O"T')"""
        expected = 'msgid "H"O"T"'
        result = generate_po(data, self.args.path, self.args)
        self.assertIn(expected, result)

    def test_widget(self):
        data = """blockPage(Surfly.i18n.gettext('Cobrowsing session is opened in a separate tab.') + " " +"""
        expected = 'msgid "Cobrowsing session is opened in a separate tab."'
        result = generate_po(data, self.args.path, self.args)
        self.assertIn(expected, result)

    def test_widget2(self):
        data = """
                blockPage(Surfly.i18n.gettext('Cobrowsing session is opened in a separate tab.') + " " +
                Surfly.i18n.gettext('Please do not close this window while it is active.'),
        """
        result = generate_po(data, self.args.path, self.args)
        self.assertIn('msgid "Cobrowsing session is opened in a separate tab."', result)
        self.assertIn('msgid "Please do not close this window while it is active."', result)

    def test_double(self):
        data = """
                gettext("Lonely")
                gettext("Warrior")
        """
        result = generate_po(data, self.args.path, self.args)
        self.assertIn('msgid "Warrior"', result)
        self.assertIn('msgid "Lonely"', result)

    def test_double2(self):
        data = """
                :aria-label="open.publishing ? $gettext('Leave videochat') : $gettext('Join videochat')">
        """
        result = generate_po(data, self.args.path, self.args)
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
        result = generate_po(data, self.args.path, self.args)
        self.assertIn('msgid "You have an active cobrowsing session, are you sure you want to close this window?"', result)


if __name__ == '__main__':
    unittest.main()
