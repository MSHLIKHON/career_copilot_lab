# Validation and handoff

Runtime used: Linux, Python 3.12.14, Streamlit 1.49.1, scikit-learn 1.8.0,
pandas 2.2.3, NumPy 2.3.5, pypdf 6.10.0, joblib 1.5.3.

Tests cover all 20 reference task solutions, runner restrictions and limits,
input copying, model loading/prediction, train/test source-family separation,
password hashing, account isolation, lockout, stored assistance, adaptive rules,
and the actual Streamlit registration/login/task/hints/profile/history workflow.

The final test run passed 61 tests. All 20 reference solutions passed all 88
task-specific cases. The local Streamlit server started on a test port and its
health endpoint returned `ok`. Python compile checks and shell syntax validation
also passed. AppTest verifies widgets and flows, not pixel-perfect browser layout.

The test suite uses temporary databases and does not write fake students into
the delivered project. See `TEST_RESULTS.txt` for the executed run.

Windows launch scripts are provided but were not executed on Windows in this
environment. Use Python 3.12 and run RUN_TESTS_WINDOWS.bat on the target laptop.
The browser server must stay local. No production deployment or independent
security audit has been performed.
