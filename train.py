
import ast
import json
from pathlib import Path
import platform
import random
import joblib
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, f1_score, recall_score, confusion_matrix
from core.model import LABELS, feature_text, MODEL_DIR
from core.runner import run_tests

ROOT = Path(__file__).resolve().parent

FAMILIES = [
 ("wrong_condition", "def solve(n):\n    return n > 0", ("n > 0", "n < 0"), [4], True),
 ("wrong_condition", "def solve(n):\n    return n % 2 == 0", ("==", "!="), [2], True),
 ("wrong_condition", "def solve(a, b):\n    if a >= b:\n        return a\n    return b", (">=", "<="), [8, 2], 8),
 ("wrong_condition", "def solve(n):\n    return n >= 18", (">=", ">"), [18], True),
 ("wrong_condition", "def solve(n):\n    return n >= 0 and n <= 10", ("and", "or"), [50], False),
 ("wrong_condition", "def solve(nums, n):\n    return n in nums", ("n in nums", "n not in nums"), [[1, 3], 3], True),
 ("loop_boundary", "def solve(n):\n    total = 0\n    for i in range(1, n+1):\n        total += i\n    return total", ("n+1", "n"), [4], 10),
 ("loop_boundary", "def solve(nums):\n    total = 0\n    for i in range(len(nums)):\n        total += nums[i]\n    return total", ("range(len(nums))", "range(len(nums)-1)"), [[2, 4, 6]], 12),
 ("loop_boundary", "def solve(n):\n    total = 1\n    for i in range(1, n+1):\n        total *= i\n    return total", ("n+1", "n"), [4], 24),
 ("loop_boundary", "def solve(n):\n    i = 1\n    total = 0\n    while i <= n:\n        total += i\n        i += 1\n    return total", ("i <= n", "i < n"), [3], 6),
 ("loop_boundary", "def solve(nums):\n    total = []\n    for i in range(0, len(nums)):\n        total = total + [nums[i]]\n    return total", ("range(0, len(nums))", "range(1, len(nums))"), [[4, 7]], [4, 7]),
 ("loop_boundary", "def solve(n):\n    total = 0\n    for i in range(n, 0, -1):\n        total += i\n    return total", ("range(n, 0, -1)", "range(n, 1, -1)"), [3], 6),
 ("wrong_update", "def solve(nums):\n    total = 0\n    for n in nums:\n        total += n\n    return total", ("total += n", "total = n"), [[2, 3, 4]], 9),
 ("wrong_update", "def solve(n):\n    total = 1\n    for i in range(1, n+1):\n        total *= i\n    return total", ("total *= i", "total += i"), [4], 24),
 ("wrong_update", "def solve(nums):\n    total = 0\n    for n in nums:\n        if n > 0:\n            total += 1\n    return total", ("total += 1", "total += n"), [[2, 4]], 2),
 ("wrong_update", "def solve(nums):\n    total = 0\n    for n in nums:\n        total += n*n\n    return total", ("total += n*n", "total += n"), [[2, 3]], 13),
 ("wrong_update", "def solve(nums):\n    total = []\n    for n in nums:\n        total = total + [n]\n    return total", ("total = total + [n]", "total = [n]"), [[1, 2]], [1, 2]),
 ("wrong_update", "def solve(n):\n    total = 0\n    while n > 0:\n        total += n % 10\n        n = n // 10\n    return total", ("total += n % 10", "total = n % 10"), [123], 6),
 ("missing_edge_case", "def solve(nums):\n    if len(nums) == 0:\n        return None\n    return max(nums)", ("    if len(nums) == 0:\n        return None\n", ""), [[]], None),
 ("missing_edge_case", "def solve(nums):\n    if len(nums) == 0:\n        return 0\n    return sum(nums) / len(nums)", ("    if len(nums) == 0:\n        return 0\n", ""), [[]], 0),
 ("missing_edge_case", "def solve(nums):\n    if len(nums) < 2:\n        return None\n    return sorted(nums)[-2]", ("    if len(nums) < 2:\n        return None\n", ""), [[1]], None),
 ("missing_edge_case", "def solve(n):\n    n = abs(n)\n    total = 0\n    while n > 0:\n        total += n % 10\n        n = n // 10\n    return total", ("    n = abs(n)\n", ""), [-12], 3),
 ("missing_edge_case", "def solve(nums, k):\n    if len(nums) == 0:\n        return []\n    k = k % len(nums)\n    return nums[-k:] + nums[:-k]", ("    if len(nums) == 0:\n        return []\n", ""), [[], 2], []),
 ("missing_edge_case", "def solve(text):\n    if len(text) == 0:\n        return None\n    return text[0]", ("    if len(text) == 0:\n        return None\n", ""), [""], None),
]


class Rename(ast.NodeTransformer):
    def __init__(self, mapping):
        self.mapping = mapping

    def visit_Name(self, node):
        node.id = self.mapping.get(node.id, node.id)
        return node

    def visit_arg(self, node):
        node.arg = self.mapping.get(node.arg, node.arg)
        return node


def make_dataset():
    rows = []
    for family, (label, correct, change, args, expected) in enumerate(FAMILIES):
        broken = correct.replace(*change, 1)
        assert broken != correct
        sample_task = {"function": "solve", "tests": [{"args": args, "expected": expected, "note": "Mutation witness"}]}
        assert run_tests(correct, sample_task)["status"] == "passed", correct
        for variant in range(10):
            tree = ast.parse(broken)
            names = sorted({n.arg for n in ast.walk(tree) if isinstance(n, ast.arg)} |
                           {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)})
            rng = random.Random(1000 + variant)
            replacements = rng.sample(["value", "number", "items", "result", "counter", "index", "data", "answer", "limit", "first", "second", "amount"], len(names))
            mapping = {name: replacement + str(variant) for name, replacement in zip(names, replacements)}
            source = ast.unparse(Rename(mapping).visit(tree))
            result = run_tests(source, sample_task)
            assert result["status"] == "failed", (family, source, result)
            # Each class has six families: four train, one validation, one test.
            split = "train" if family % 6 < 4 else "validation" if family % 6 == 4 else "test"
            rows.append({"id": f"f{family:02d}-v{variant:02d}", "family": f"f{family:02d}",
                         "split": split, "code": source, "label": label, "args": args,
                         "expected": expected, "result": result,
                         "source": "original_generated_mutation", "human_reviewed": False})
    return rows


def evaluate(model, rows):
    actual = [r["label"] for r in rows]
    predicted = model.predict([feature_text(r["code"], r["result"]) for r in rows])
    return {"accuracy": float(accuracy_score(actual, predicted)),
            "macro_f1": float(f1_score(actual, predicted, labels=LABELS, average="macro", zero_division=0)),
            "macro_recall": float(recall_score(actual, predicted, labels=LABELS, average="macro", zero_division=0)),
            "confusion_matrix": confusion_matrix(actual, predicted, labels=LABELS).tolist()}


def main():
    rows = make_dataset()
    (ROOT / "data").mkdir(exist_ok=True)
    MODEL_DIR.mkdir(exist_ok=True)
    (ROOT / "data" / "pilot_dataset.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    partitions = {s: [r for r in rows if r["split"] == s] for s in ("train", "validation", "test")}
    candidates = {"logistic_regression": LogisticRegression(max_iter=1500, random_state=42, class_weight="balanced"),
                  "linear_svm": LinearSVC(random_state=42, class_weight="balanced")}
    report = {"sklearn_version": sklearn.__version__, "python_version": platform.python_version(),
              "dataset_size": len(rows), "family_count": len(FAMILIES), "labels": LABELS,
              "split_counts": {s: len(v) for s, v in partitions.items()},
              "split_policy": "Disjoint source families: 16 train, 4 validation, 4 test. Renamed copies stay together.",
              "warning": "Generated pilot data, no human-reviewed real student test set. Renamed variants are correlated. Scores do not establish real-world accuracy.",
              "deployed_model": "logistic_regression", "deployment_reason": "Fixed before evaluation; supports probability scores. Scores are not calibrated confidence.",
              "models": {}}
    for name, estimator in candidates.items():
        pipe = Pipeline([("tfidf", TfidfVectorizer(analyzer="char", ngram_range=(2, 5), max_features=12000)), ("classifier", estimator)])
        pipe.fit([feature_text(r["code"], r["result"]) for r in partitions["train"]], [r["label"] for r in partitions["train"]])
        report["models"][name] = {s: evaluate(pipe, partitions[s]) for s in ("validation", "test")}
        if name == "logistic_regression":
            joblib.dump(pipe, MODEL_DIR / "classifier.joblib")
        else:
            joblib.dump(pipe, MODEL_DIR / "comparison_svm.joblib")
    (MODEL_DIR / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
