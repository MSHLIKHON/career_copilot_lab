"""Trained model evaluation and metrics lab page."""

import json
import pandas as pd
import streamlit as st

from core.model import MODEL_DIR


def render_model_lab() -> None:
    st.caption("TRAINING AND EVALUATION")
    st.title("Our trained mistake classifier")
    path = MODEL_DIR / "metrics.json"
    if not path.exists():
        st.warning("No trained model found. Run python train.py in the project folder.")
    else:
        metrics = json.loads(path.read_text(encoding="utf-8"))
        st.warning(metrics["warning"])
        st.write("**Approach:** Character TF-IDF + Logistic Regression. Linear SVM is a comparison baseline.")
        st.write("**Training input:** Submitted code and runtime error types. **Output:** One of four likely logic-mistake categories.")
        st.write("**Syntax errors:** Deterministic parser feedback, not a trained AI category.")
        st.write(metrics["split_policy"])
        a, b, c = st.columns(3)
        a.metric("Generated samples", metrics["dataset_size"])
        b.metric("Source families", metrics["family_count"])
        c.metric("Human-reviewed real samples", 0)
        rows = [
            {
                "Model": name,
                "Partition": split,
                "Accuracy": data["accuracy"],
                "Macro F1": data["macro_f1"],
                "Macro recall": data["macro_recall"],
            }
            for name, results in metrics["models"].items()
            for split, data in results.items()
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.subheader("Test confusion matrix: Logistic Regression")
        st.caption("Rows = actual mutation label. Columns = predicted label.")
        st.dataframe(
            pd.DataFrame(
                metrics["models"]["logistic_regression"]["test"]["confusion_matrix"],
                index=metrics["labels"],
                columns=metrics["labels"],
            ),
            width="stretch",
        )
        st.write(metrics["deployment_reason"])
        st.caption(
            "Low model scores (<0.45) produce an uncertain result. Unseen/multiple mistakes may be misclassified. "
            "Independent human-reviewed data is required before claiming generalisation."
        )
        st.download_button("Download evaluation report", path.read_bytes(), "evaluation_metrics.json", "application/json")
    st.subheader("Reproduce training")
    st.code("python train.py\npython -m unittest discover -s tests -v", language="bash")
    st.write("Training writes data/pilot_dataset.json, models/classifier.joblib and models/metrics.json. Never load model files from unknown sources.")
