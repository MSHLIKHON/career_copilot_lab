"""Run tests and save the genuine output for the delivery report."""
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                        cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
(root / "docs" / "TEST_RESULTS.txt").write_text(result.stdout, encoding="utf-8")
print(result.stdout)
raise SystemExit(result.returncode)
