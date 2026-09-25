import json
import tempfile
import unittest
from pathlib import Path

from core import storage
from core.tasks import TASKS, TASK_BY_ID
from core.runner import run_tests, Interpreter, RunnerError
from core.adaptive import extract_claims, summarize, recommend, roadmap
from core.model import load_model, predict, LABELS


class TaskTests(unittest.TestCase):
    pass


def solution_test(task):
    def test(self):
        result = run_tests(task['solution'], task)
        self.assertEqual(result['status'], 'passed', result)
    return test


for item in TASKS:
    setattr(TaskTests, f"test_reference_{item['id']}", solution_test(item))


class RunnerTests(unittest.TestCase):
    def run_code(self, source):
        return run_tests(source, TASK_BY_ID['L1'])

    def test_off_by_one(self):
        r = self.run_code('def solve(n):\n    total = 0\n    for i in range(1, n):\n        total += i\n    return total')
        self.assertEqual(r['passed'], 1)
        self.assertEqual(r['status'], 'failed')

    def test_syntax_error(self):
        self.assertEqual(self.run_code('def solve(n)\n return n')['status'], 'syntax_error')

    def test_missing_function(self):
        self.assertEqual(self.run_code('def other(n):\n return n')['status'], 'unsupported')

    def test_import_blocked(self):
        self.assertEqual(self.run_code('import os\ndef solve(n):\n return 0')['status'], 'unsupported')

    def test_attribute_blocked(self):
        self.assertEqual(self.run_code('def solve(n):\n return n.__class__')['status'], 'unsupported')

    def test_file_access_blocked(self):
        r = self.run_code('def solve(n):\n return open("secret.txt")')
        self.assertIn('not allowed', r['cases'][0]['error'])

    def test_eval_blocked(self):
        self.assertEqual(self.run_code('def solve(n):\n return eval("1+1")')['passed'], 0)

    def test_infinite_loop(self):
        r = self.run_code('def solve(n):\n while True:\n  pass')
        self.assertIn('Step limit', r['cases'][0]['error'])

    def test_large_allocation(self):
        r = self.run_code('def solve(n):\n return [1] * 1000000000')
        self.assertIn('Collection limit', r['cases'][0]['error'])

    def test_large_range(self):
        r = self.run_code('def solve(n):\n return list(range(1000000000))')
        self.assertIn('Collection limit', r['cases'][0]['error'])

    def test_nested_allocation_budget(self):
        r = self.run_code('def solve(n):\n a=[1]*1000\n b=[a]*1000\n return b')
        self.assertIn('Step limit', r['cases'][0]['error'])

    def test_recursive_limit(self):
        r = self.run_code('def solve(n):\n return solve(n)')
        self.assertIn('depth limit', r['cases'][0]['error'])

    def test_function_arguments(self):
        r = self.run_code('def solve():\n return 0')
        self.assertIn('expects', r['cases'][0]['error'])

    def test_helper_function(self):
        self.assertEqual(Interpreter('def double(n):\n return n*2\ndef solve(n):\n return double(n)').call('solve', [3]), 6)

    def test_list_input_is_copied(self):
        task = {'function': 'solve', 'tests': [{'args': [[1, 2]], 'expected': 0, 'note': 'Copy'}]}
        run_tests('def solve(nums):\n nums[0]=99\n return 0', task)
        self.assertEqual(task['tests'][0]['args'], [[1, 2]])

    def test_bool_is_not_string(self):
        r = run_tests('def solve(n):\n return "True"', TASK_BY_ID['C2'])
        self.assertEqual(r['passed'], 0)

    def test_break_continue(self):
        r = Interpreter('def solve(n):\n total=0\n for i in range(n):\n  if i==1:\n   continue\n  if i==4:\n   break\n  total+=i\n return total').call('solve', [10])
        self.assertEqual(r, 5)

    def test_power_not_supported(self):
        self.assertEqual(self.run_code('def solve(n):\n return 10**10000000')['status'], 'unsupported')


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = storage.DB_PATH
        storage.DB_PATH = Path(self.temp.name) / 'test.db'
        storage.init_db()
        self.uid = storage.register('learner', 'Learner', 'testing123')

    def tearDown(self):
        storage.DB_PATH = self.old
        import gc
        gc.collect()
        self.temp.cleanup()

    def test_register_login(self):
        self.assertEqual(storage.login('LEARNER', 'testing123')['id'], self.uid)
        self.assertIsNone(storage.login('learner', 'wrong'))

    def test_password_not_plaintext(self):
        with storage.connect() as db:
            row = db.execute('SELECT * FROM users').fetchone()
        self.assertNotEqual(row['password_hash'], 'testing123')
        self.assertEqual(len(row['salt']), 32)

    def test_duplicate_user(self):
        with self.assertRaises(ValueError):
            storage.register('learner', 'Another', 'testing123')

    def test_invalid_user(self):
        with self.assertRaises(ValueError):
            storage.register("a';DROP", 'Another', 'testing123')

    def test_weak_password(self):
        with self.assertRaises(ValueError):
            storage.register('newuser', 'Another', 'short')

    def test_profile_persistence(self):
        storage.save_profile(self.uid, ['Python', 'SQL'], 'Data analysis foundations')
        self.assertEqual(storage.profile(self.uid)['claims'], ['Python', 'SQL'])

    def test_hint_cannot_be_reset(self):
        storage.assistance(self.uid, 'L1', hints=3, solution=True)
        result = storage.assistance(self.uid, 'L1', hints=0, solution=False)
        self.assertEqual(result['hints'], 3)
        self.assertEqual(result['solution_seen'], 1)

    def test_attempt_isolation_and_feedback(self):
        other = storage.register('second', 'Another', 'testing123')
        task = TASK_BY_ID['L1']
        result = run_tests(task['solution'], task)
        aid = storage.save_attempt(self.uid, 'L1', task['solution'], result, {'label': 'tests_passed'})
        self.assertEqual(len(storage.attempts(self.uid)), 1)
        self.assertEqual(storage.attempts(other), [])
        with self.assertRaises(ValueError):
            storage.report_prediction(other, aid, 'Should not be allowed')
        storage.report_prediction(self.uid, aid, 'My feedback')
        self.assertEqual(len(storage.export_user(self.uid)['feedback']), 1)

    def test_login_lockout(self):
        for _ in range(5):
            self.assertIsNone(storage.login('learner', 'wrong'))
        with self.assertRaises(ValueError):
            storage.login('learner', 'testing123')


class AdaptiveTests(unittest.TestCase):
    def attempt(self, key, status='passed', hints=0, solution=0):
        return {'task_id': key, 'result': {'status': status}, 'hints': hints, 'solution_seen': solution}

    def test_claims(self):
        self.assertEqual(extract_claims('Python, SQL and React'), ['Python', 'SQL', 'React'])

    def test_claim_boundaries(self):
        self.assertEqual(extract_claims('JavaScript'), ['JavaScript'])

    def test_initial_recommendation(self):
        self.assertEqual(recommend([])[0]['level'], 1)

    def test_failed_task_goes_easier(self):
        t, reason = recommend([self.attempt('L5', 'failed')])
        self.assertEqual(t['topic'], 'Loops')
        self.assertLess(t['level'], 3)

    def test_passed_task_not_recommended_again(self):
        self.assertNotEqual(recommend([self.attempt('C1')])[0]['id'], 'C1')

    def test_assisted_not_independent(self):
        r = summarize([self.attempt('C1', hints=1)])[0]
        self.assertEqual(r['Tasks passed'], 1)
        self.assertEqual(r['Independent passes'], 0)

    def test_solution_seen_not_independent(self):
        self.assertEqual(summarize([self.attempt('C1', solution=1)])[0]['Independent passes'], 0)

    def test_goal_gap(self):
        r = roadmap([], 'Python backend preparation')
        self.assertTrue(all(x['Independent evidence level'] == 0 for x in r))

    def test_all_completed(self):
        t, reason = recommend([self.attempt(t['id']) for t in TASKS])
        self.assertIn('All 20', reason)


class ModelTests(unittest.TestCase):
    def test_saved_model_predicts(self):
        model, error = load_model()
        self.assertIsNotNone(model, error)
        source = 'def solve(n):\n total=0\n for i in range(1,n):\n  total+=i\n return total'
        r = predict(source, run_tests(source, TASK_BY_ID['L1']), model)
        self.assertIn(r['label'], LABELS + ['uncertain'])
        self.assertTrue(0 <= r['score'] <= 1)

    def test_pass_does_not_need_model(self):
        t = TASK_BY_ID['L1']
        self.assertEqual(predict(t['solution'], run_tests(t['solution'], t), None)['label'], 'tests_passed')

    def test_dataset_families_do_not_leak(self):
        rows = json.loads((Path(__file__).resolve().parents[1] / 'data/pilot_dataset.json').read_text())
        split_sets = {s: {r['family'] for r in rows if r['split'] == s} for s in ['train','validation','test']}
        self.assertFalse(split_sets['train'] & split_sets['test'])
        self.assertFalse(split_sets['train'] & split_sets['validation'])
        self.assertFalse(split_sets['test'] & split_sets['validation'])
        for split in split_sets:
            self.assertEqual({r['label'] for r in rows if r['split'] == split}, set(LABELS))


if __name__ == '__main__':
    unittest.main()
