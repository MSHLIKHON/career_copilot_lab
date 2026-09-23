import json
import math
from pathlib import Path
import joblib
import sklearn

MODEL_DIR = Path(__file__).resolve().parents[1] / "models"
LABELS = ["wrong_condition", "loop_boundary", "wrong_update", "missing_edge_case"]
MESSAGES = {
    "wrong_condition": "Review comparison operators and True/False conditions.",
    "loop_boundary": "Check where the loop starts and stops. range excludes its stop value.",
    "wrong_update": "Check how the result or counter changes inside the loop.",
    "missing_edge_case": "Review empty input, zero, negative values and other task boundaries.",
}

REQUIRED_METRIC_FIELDS = {
    "sklearn_version", "dataset_size", "family_count", "labels", "split_policy",
    "warning", "deployment_reason", "models",
}


def feature_text(code, result):
    errors = " ".join(c.get("error", "").split(":")[0] for c in result.get("cases", []) if c.get("error"))
    return code[:12000] + "\n runtime_errors " + errors


def load_metrics():
    meta_path = MODEL_DIR / "metrics.json"
    if not meta_path.exists():
        return None, "Model metadata is missing. Run python train.py."
    try:
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, "Model metadata is unreadable. Run python train.py to rebuild it."
    if not isinstance(metadata, dict) or not REQUIRED_METRIC_FIELDS.issubset(metadata):
        return None, "Model metadata is incomplete. Run python train.py to rebuild it."
    if (metadata.get("labels") != LABELS or not isinstance(metadata.get("models"), dict) or
            "logistic_regression" not in metadata["models"]):
        return None, "Model metadata does not match this app. Run python train.py to rebuild it."
    try:
        for results in metadata["models"].values():
            for split in ("validation", "test"):
                report = results[split]
                for metric in ("accuracy", "macro_f1", "macro_recall", "confusion_matrix"):
                    report[metric]
                matrix = report["confusion_matrix"]
                if (not isinstance(matrix, list) or len(matrix) != len(LABELS) or
                        any(not isinstance(row, list) or len(row) != len(LABELS) for row in matrix)):
                    raise TypeError("invalid confusion matrix")
    except (KeyError, TypeError):
        return None, "Model evaluation data is incomplete. Run python train.py to rebuild it."
    return metadata, ""


def load_model():
    model_path = MODEL_DIR / "classifier.joblib"
    metadata, error = load_metrics()
    if error or not model_path.exists():
        return None, error or "Model is missing. Run python train.py."
    if metadata["sklearn_version"] != sklearn.__version__:
        return None, "Model library version changed. Run python train.py to rebuild locally."
    # Only load this project's locally trained artifact, never an uploaded pickle.
    try:
        model = joblib.load(model_path)
        classes = [str(label) for label in model.classes_]
        if set(classes) != set(LABELS) or not callable(model.predict_proba):
            raise ValueError("unexpected model interface")
    except Exception:
        return None, "The local model artifact is unreadable or incompatible. Run python train.py to rebuild it."
    return model, ""


def predict(code, result, model, model_error=""):
    if result["status"] == "passed":
        return {"label": "tests_passed", "score": None, "message": "All supplied tests passed. This does not prove correctness for every possible input."}
    if result["status"] in ("syntax_error", "unsupported"):
        return {"label": result["status"], "score": None, "message": result["message"] + " This is runner feedback, not an ML prediction."}
    if model is None:
        message = model_error or "Train the model first."
        return {"label": "model_unavailable", "score": None, "message": message + " Test evidence is still available."}
    try:
        probabilities = model.predict_proba([feature_text(code, result)])[0]
        index = int(probabilities.argmax())
        score = float(probabilities[index])
        label = str(model.classes_[index])
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError("invalid score")
    except Exception:
        return {"label": "model_unavailable", "score": None,
                "message": "The local model could not make a prediction. Rebuild it with python train.py. Test evidence is still available."}
    if label not in MESSAGES:
        return {"label": "model_unavailable", "score": None,
                "message": "The local model returned an unknown category. Rebuild it with python train.py. Test evidence is still available."}
    if score < 0.45:
        return {"label": "uncertain", "suggested_label": label, "score": score,
                "message": "The model is uncertain. Inspect failed test cases; no reliable mistake category is available."}
    return {"label": label, "score": score, "message": MESSAGES[label] + " This is a likely category, not a confirmed diagnosis."}
