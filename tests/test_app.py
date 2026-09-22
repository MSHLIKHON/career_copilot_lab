import tempfile
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from core import storage

ROOT = Path(__file__).resolve().parents[1]


class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = storage.DB_PATH
        storage.DB_PATH = Path(self.temp.name) / 'app.db'
        self.app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=30).run()

    def tearDown(self):
        storage.DB_PATH = self.old
        self.temp.cleanup()

    def button(self, label):
        return next(x for x in self.app.button if x.label == label)

    def test_full_student_journey(self):
        self.assertFalse(self.app.exception)
        # Exercise registration and sign-in through the actual widgets.
        fields = {x.label: x for x in self.app.text_input}
        fields['Your name'].set_value('Demo Learner')
        fields['Choose username'].set_value('demostudent')
        fields['Choose password'].set_value('demoPassword123')
        fields['Confirm password'].set_value('demoPassword123')
        self.app.checkbox[0].check()
        self.button('Create account').click().run()
        self.assertFalse(self.app.exception)
        fields = {x.label: x for x in self.app.text_input}
        fields['Username'].set_value('demostudent')
        fields['Password'].set_value('demoPassword123')
        self.button('Sign in').click().run()
        self.assertFalse(self.app.exception)
        self.assertIn('Welcome', self.app.title[0].value)
        self.app.sidebar.radio[0].set_value('Practice').run()
        self.app.selectbox[0].set_value('L1').run()
        self.button('Load a buggy example').click().run()
        self.button('Run tests & save attempt').click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(len(storage.attempts(self.app.session_state.user['id'])), 1)
        self.button('Show next hint').click().run()
        self.button('Reveal reference solution').click().run()
        from core.tasks import TASK_BY_ID
        self.app.text_area(key='editor_L1').set_value(TASK_BY_ID['L1']['solution'])
        self.button('Run tests & save attempt').click().run()
        history = storage.attempts(self.app.session_state.user['id'])
        self.assertEqual(history[-1]['result']['status'], 'passed')
        self.assertEqual(history[-1]['hints'], 1)
        self.assertEqual(history[-1]['solution_seen'], 1)
        for page in ['Overview', 'My skills & CV', 'Learning roadmap', 'History', 'Runner help']:
            self.app.sidebar.radio[0].set_value(page).run()
            self.assertFalse(self.app.exception, page)
        self.app.sidebar.radio[0].set_value('My skills & CV').run()
        self.app.text_area[0].set_value('I use Python, SQL and React.')
        self.button('Extract skill keywords').click().run()
        self.button('Save skill profile').click().run()
        self.assertEqual(storage.profile(self.app.session_state.user['id'])['claims'], ['Python', 'SQL', 'React'])
        self.button('Sign out').click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.title[0].value, 'Career Copilot Lab')


if __name__ == '__main__':
    unittest.main()
