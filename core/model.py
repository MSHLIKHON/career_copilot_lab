import json
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


def feature_text(code, result):
    errors = " ".join(c.get("error", "").split(":")[0] for c in result.get("cases", []) if c.get("error"))
    return code[:12000] + "\n runtime_errors " + errors


def load_model():
    meta_path = MODEL_DIR / "metrics.json"
    if not meta_path.exists() or not (MODEL_DIR / "classifier.joblib").exists():
        return None, "Model is missing. Run python train.py."
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    if metadata["sklearn_version"] != sklearn.__version__:
        return None, "Model library version changed. Run python train.py to rebuild locally."
    # Only load this project's locally trained artifact, never an uploaded pickle.
    return joblib.load(MODEL_DIR / "classifier.joblib"), ""


def predict(code, result, model):
    if result["status"] == "passed":
        return {"label": "tests_passed", "score": None, "message": "All supplied tests passed. This does not prove correctness for every possible input."}
    if result["status"] in ("syntax_error", "unsupported"):
        return {"label": result["status"], "score": None, "message": result["message"] + " This is runner feedback, not an ML prediction."}
    if model is None:
        return {"label": "model_unavailable", "score": None, "message": "Train the model first. Test evidence is still available."}
    probabilities = model.predict_proba([feature_text(code, result)])[0]
    index = int(probabilities.argmax())
    score = float(probabilities[index])
    label = str(model.classes_[index])
    if score < 0.45:
        return {"label": "uncertain", "suggested_label": label, "score": score,
                "message": "The model is uncertain. Inspect failed test cases; no reliable mistake category is available."}
    return {"label": label, "score": score, "message": MESSAGES[label] + " This is a likely category, not a confirmed diagnosis."}
