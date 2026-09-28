"""Mistake-category classifier: feature building, model loading, prediction."""

import json
from pathlib import Path

import joblib
import sklearn

MODEL_DIR = Path(__file__).resolve().parents[1] / "models"
METRICS_PATH = MODEL_DIR / "metrics.json"
CLASSIFIER_PATH = MODEL_DIR / "classifier.joblib"

LABELS = ["wrong_condition", "loop_boundary", "wrong_update", "missing_edge_case"]

MESSAGES = {
    "wrong_condition": "Review comparison operators and True/False conditions.",
    "loop_boundary": "Check where the loop starts and stops. range excludes its stop value.",
    "wrong_update": "Check how the result or counter changes inside the loop.",
    "missing_edge_case": "Review empty input, zero, negative values and other task boundaries.",
}

MAX_CODE_CHARS = 12000
UNCERTAINTY_THRESHOLD = 0.45


def _build_response(label, message, score=None, **extra):
    """Assemble a prediction dict in one consistent shape."""
    return {"label": label, "score": score, "message": message, **extra}


def feature_text(code, result):
    """Join the (truncated) source with the first token of each runtime error."""
    error_heads = " ".join(
        case.get("error", "").split(":")[0]
        for case in result.get("cases", [])
        if case.get("error")
    )
    return code[:MAX_CODE_CHARS] + "\n runtime_errors " + error_heads


def load_model():
    """Return (model, error_message). The model is None when it cannot be used."""
    if not METRICS_PATH.exists() or not CLASSIFIER_PATH.exists():
        return None, "Model is missing. Run python train.py."

    metadata = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    if metadata["sklearn_version"] != sklearn.__version__:
        return None, "Model library version changed. Run python train.py to rebuild locally."

    # Only load this project's locally trained artifact, never an uploaded pickle.
    return joblib.load(CLASSIFIER_PATH), ""


def predict(code, result, model):
    """Turn a test-run result into a feedback dict, using the model only when needed."""
    status = result["status"]

    if status == "passed":
        return _build_response(
            "tests_passed",
            "All supplied tests passed. This does not prove correctness for every possible input.",
        )

    if status in ("syntax_error", "unsupported"):
        return _build_response(
            status,
            result["message"] + " This is runner feedback, not an ML prediction.",
        )

    if model is None:
        return _build_response(
            "model_unavailable",
            "Train the model first. Test evidence is still available.",
        )

    probabilities = model.predict_proba([feature_text(code, result)])[0]
    best = int(probabilities.argmax())
    score = float(probabilities[best])
    label = str(model.classes_[best])

    if score < UNCERTAINTY_THRESHOLD:
        return _build_response(
            "uncertain",
            "The model is uncertain. Inspect failed test cases; no reliable mistake category is available.",
            score,
            suggested_label=label,
        )

    return _build_response(
        label,
        MESSAGES[label] + " This is a likely category, not a confirmed diagnosis.",
        score,
    )
