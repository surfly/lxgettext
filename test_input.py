import unittest

from lxgettext import generate_po


class TestInputData(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
