"""Build the pilot dataset, train both candidate classifiers, and write metrics."""

import ast
import json
import platform
import random
from pathlib import Path
from typing import Any, NamedTuple

import joblib
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from core.model import LABELS, MODEL_DIR, feature_text
from core.runner import run_tests

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

VARIANTS_PER_FAMILY = 10
NAME_POOL = [
    "value", "number", "items", "result", "counter", "index",
    "data", "answer", "limit", "first", "second", "amount",
]
SPLITS = ("train", "validation", "test")


class Family(NamedTuple):
    """One correct program, the single edit that breaks it, and a test that exposes the break."""

    label: str
    correct: str
    change: tuple  # (text to find, text to replace it with)
    args: list
    expected: Any


FAMILIES = [
    # ---- wrong_condition ----
    Family("wrong_condition", "def solve(n):\n    return n > 0", ("n > 0", "n < 0"), [4], True),
    Family("wrong_condition", "def solve(n):\n    return n % 2 == 0", ("==", "!="), [2], True),
    Family("wrong_condition", "def solve(a, b):\n    if a >= b:\n        return a\n    return b", (">=", "<="), [8, 2], 8),
    Family("wrong_condition", "def solve(n):\n    return n >= 18", (">=", ">"), [18], True),
    Family("wrong_condition", "def solve(n):\n    return n >= 0 and n <= 10", ("and", "or"), [50], False),
    Family("wrong_condition", "def solve(nums, n):\n    return n in nums", ("n in nums", "n not in nums"), [[1, 3], 3], True),
    # ---- loop_boundary ----
    Family("loop_boundary", "def solve(n):\n    total = 0\n    for i in range(1, n+1):\n        total += i\n    return total", ("n+1", "n"), [4], 10),
    Family("loop_boundary", "def solve(nums):\n    total = 0\n    for i in range(len(nums)):\n        total += nums[i]\n    return total", ("range(len(nums))", "range(len(nums)-1)"), [[2, 4, 6]], 12),
    Family("loop_boundary", "def solve(n):\n    total = 1\n    for i in range(1, n+1):\n        total *= i\n    return total", ("n+1", "n"), [4], 24),
    Family("loop_boundary", "def solve(n):\n    i = 1\n    total = 0\n    while i <= n:\n        total += i\n        i += 1\n    return total", ("i <= n", "i < n"), [3], 6),
    Family("loop_boundary", "def solve(nums):\n    total = []\n    for i in range(0, len(nums)):\n        total = total + [nums[i]]\n    return total", ("range(0, len(nums))", "range(1, len(nums))"), [[4, 7]], [4, 7]),
    Family("loop_boundary", "def solve(n):\n    total = 0\n    for i in range(n, 0, -1):\n        total += i\n    return total", ("range(n, 0, -1)", "range(n, 1, -1)"), [3], 6),
    # ---- wrong_update ----
    Family("wrong_update", "def solve(nums):\n    total = 0\n    for n in nums:\n        total += n\n    return total", ("total += n", "total = n"), [[2, 3, 4]], 9),
    Family("wrong_update", "def solve(n):\n    total = 1\n    for i in range(1, n+1):\n        total *= i\n    return total", ("total *= i", "total += i"), [4], 24),
    Family("wrong_update", "def solve(nums):\n    total = 0\n    for n in nums:\n        if n > 0:\n            total += 1\n    return total", ("total += 1", "total += n"), [[2, 4]], 2),
    Family("wrong_update", "def solve(nums):\n    total = 0\n    for n in nums:\n        total += n*n\n    return total", ("total += n*n", "total += n"), [[2, 3]], 13),
    Family("wrong_update", "def solve(nums):\n    total = []\n    for n in nums:\n        total = total + [n]\n    return total", ("total = total + [n]", "total = [n]"), [[1, 2]], [1, 2]),
    Family("wrong_update", "def solve(n):\n    total = 0\n    while n > 0:\n        total += n % 10\n        n = n // 10\n    return total", ("total += n % 10", "total = n % 10"), [123], 6),
    # ---- missing_edge_case ----
    Family("missing_edge_case", "def solve(nums):\n    if len(nums) == 0:\n        return None\n    return max(nums)", ("    if len(nums) == 0:\n        return None\n", ""), [[]], None),
    Family("missing_edge_case", "def solve(nums):\n    if len(nums) == 0:\n        return 0\n    return sum(nums) / len(nums)", ("    if len(nums) == 0:\n        return 0\n", ""), [[]], 0),
    Family("missing_edge_case", "def solve(nums):\n    if len(nums) < 2:\n        return None\n    return sorted(nums)[-2]", ("    if len(nums) < 2:\n        return None\n", ""), [[1]], None),
    Family("missing_edge_case", "def solve(n):\n    n = abs(n)\n    total = 0\n    while n > 0:\n        total += n % 10\n        n = n // 10\n    return total", ("    n = abs(n)\n", ""), [-12], 3),
    Family("missing_edge_case", "def solve(nums, k):\n    if len(nums) == 0:\n        return []\n    k = k % len(nums)\n    return nums[-k:] + nums[:-k]", ("    if len(nums) == 0:\n        return []\n", ""), [[], 2], []),
    Family("missing_edge_case", "def solve(text):\n    if len(text) == 0:\n        return None\n    return text[0]", ("    if len(text) == 0:\n        return None\n", ""), [""], None),
]

SPLIT_POLICY = "Disjoint source families: 16 train, 4 validation, 4 test. Renamed copies stay together."
DATA_WARNING = (
    "Generated pilot data, no human-reviewed real student test set. "
    "Renamed variants are correlated. Scores do not establish real-world accuracy."
)
DEPLOYMENT_REASON = "Fixed before evaluation; supports probability scores. Scores are not calibrated confidence."


class Rename(ast.NodeTransformer):
    """Rewrite variable and argument names according to a mapping."""

    def __init__(self, mapping):
        self.mapping = mapping

    def visit_Name(self, node):
        node.id = self.mapping.get(node.id, node.id)
        return node

    def visit_arg(self, node):
        node.arg = self.mapping.get(node.arg, node.arg)
        return node


def assign_split(family_index):
    """Each class has six families: four train, one validation, one test."""
    slot = family_index % 6
    if slot < 4:
        return "train"
    if slot == 4:
        return "validation"
    return "test"


def collect_local_names(tree):
    """Names that are function arguments or assigned to, in sorted order."""
    arg_names = {node.arg for node in ast.walk(tree) if isinstance(node, ast.arg)}
    stored_names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    return sorted(arg_names | stored_names)


def make_dataset():
    rows = []
    for index, family in enumerate(FAMILIES):
        broken = family.correct.replace(*family.change, 1)
        assert broken != family.correct

        witness_task = {
            "function": "solve",
            "tests": [{"args": family.args, "expected": family.expected, "note": "Mutation witness"}],
        }
        assert run_tests(family.correct, witness_task)["status"] == "passed", family.correct

        for variant in range(VARIANTS_PER_FAMILY):
            tree = ast.parse(broken)
            names = collect_local_names(tree)
            rng = random.Random(1000 + variant)
            picks = rng.sample(NAME_POOL, len(names))
            mapping = {name: pick + str(variant) for name, pick in zip(names, picks)}

            source = ast.unparse(Rename(mapping).visit(tree))
            result = run_tests(source, witness_task)
            assert result["status"] == "failed", (index, source, result)

            rows.append({
                "id": f"f{index:02d}-v{variant:02d}",
                "family": f"f{index:02d}",
                "split": assign_split(index),
                "code": source,
                "label": family.label,
                "args": family.args,
                "expected": family.expected,
                "result": result,
                "source": "original_generated_mutation",
                "human_reviewed": False,
            })
    return rows


def to_features(rows):
    return [feature_text(row["code"], row["result"]) for row in rows]


def evaluate(model, rows):
    actual = [row["label"] for row in rows]
    predicted = model.predict(to_features(rows))
    return {
        "accuracy": float(accuracy_score(actual, predicted)),
        "macro_f1": float(f1_score(actual, predicted, labels=LABELS, average="macro", zero_division=0)),
        "macro_recall": float(recall_score(actual, predicted, labels=LABELS, average="macro", zero_division=0)),
        "confusion_matrix": confusion_matrix(actual, predicted, labels=LABELS).tolist(),
    }


def build_pipeline(estimator):
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 5), max_features=12000)
    return Pipeline([("tfidf", vectorizer), ("classifier", estimator)])


def main():
    rows = make_dataset()
    DATA_DIR.mkdir(exist_ok=True)
    MODEL_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "pilot_dataset.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

    partitions = {split: [row for row in rows if row["split"] == split] for split in SPLITS}
    train_rows = partitions["train"]

    candidates = {
        "logistic_regression": LogisticRegression(max_iter=1500, random_state=42, class_weight="balanced"),
        "linear_svm": LinearSVC(random_state=42, class_weight="balanced"),
    }
    artifact_names = {
        "logistic_regression": "classifier.joblib",
        "linear_svm": "comparison_svm.joblib",
    }

    report = {
        "sklearn_version": sklearn.__version__,
        "python_version": platform.python_version(),
        "dataset_size": len(rows),
        "family_count": len(FAMILIES),
        "labels": LABELS,
        "split_counts": {split: len(part) for split, part in partitions.items()},
        "split_policy": SPLIT_POLICY,
        "warning": DATA_WARNING,
        "deployed_model": "logistic_regression",
        "deployment_reason": DEPLOYMENT_REASON,
        "models": {},
    }

    for name, estimator in candidates.items():
        pipeline = build_pipeline(estimator)
        pipeline.fit(to_features(train_rows), [row["label"] for row in train_rows])
        report["models"][name] = {split: evaluate(pipeline, partitions[split]) for split in ("validation", "test")}
        joblib.dump(pipeline, MODEL_DIR / artifact_names[name])

    (MODEL_DIR / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
