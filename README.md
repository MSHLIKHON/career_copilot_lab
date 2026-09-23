# Career Copilot Lab

Team NO AI · AI Skill Verification & Adaptive Practice · Local classroom prototype

Start with **START_HERE_BANGLA.md** for a Windows beginner's guide.

## Quick start

Windows: install Python 3.12, extract the archive, and double-click `START_WINDOWS.bat`.

macOS/Linux (Python 3.11-3.13):

```bash
bash start.sh
```

Manual isolated setup:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python bootstrap.py
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Open `http://localhost:8501`. Create an account to enter your workspace immediately;
use Sign in on later visits. There are no hard-coded credentials.
First installation requires internet. Once installed, app and model run offline.

## Delivered features

| Requirement | Implementation |
| --- | --- |
| Sign-up/sign-in | Local SQLite accounts, salted PBKDF2-HMAC-SHA256, throttled failures, 30-minute inactivity sign-out |
| CV skill claims | Paste text or upload text-based PDF/TXT; keyword extraction with user confirmation; Python evidence separate from claims |
| Practical skill tests | 20 original Python tasks, 4 topics, 3 levels, 88 deterministic test cases |
| Code execution | Budgeted custom AST interpreter, no native eval/exec, no file/network/attribute access |
| Own trained AI | Character TF-IDF + Logistic Regression; actual saved model and reproducible training code |
| Algorithm comparison | Linear SVM comparison; held-out validation/test metrics and confusion matrix |
| Mistake feedback | Four likely categories; explicit uncertainty below 0.45 model score; syntax/unsupported feedback is deterministic |
| Hint ladder | Three task-specific hints plus reference solution; assistance permanently recorded per task |
| Adaptive practice | Rules based on failure, task level, topic, completed work and learner goal |
| Progress memory | Per-user attempts, submitted code, test evidence, hints and predictions saved to SQLite |
| Roadmap & gap view | Goal-level targets versus independent task evidence; no invented job matching percentage |
| Practice projects | Three guided project briefs; explicitly not automatically graded |
| Review loop | Learner reports on predictions, stored for review and included in personal export |
| Export | Full personal history JSON and model evaluation JSON download |
| Delivery | Source, dataset, model artifacts, tests, setup scripts, Bangla guide and model card |

## Project files

- `app.py`: Streamlit interface, profile, practice, reports and navigation.
- `core/tasks.py`: task specifications, tests, hints and reference solutions.
- `core/runner.py`: restricted interpreter and deterministic evaluator.
- `core/model.py`: trusted local model loading and prediction.
- `core/adaptive.py`: progress, keyword claims and recommendation rules.
- `core/storage.py`: SQLite persistence, authentication and feedback ownership.
- `train.py`: generated pilot data, TF-IDF pipeline, model fitting and evaluation.
- `data/pilot_dataset.json`: 240 generated labeled examples; no personal information.
- `models/`: trained artifacts and metrics. Only load trusted locally generated artifacts.
- `tests/`: unit tests and Streamlit AppTest end-to-end user journey.
- `docs/`: technical limits and validation notes.

`data/career.db` is created on your machine at first use. It is not included in the ZIP.
Back up this file privately with the app stopped. Do not commit a database containing student data.

## Training and evaluation

```bash
python train.py
python -m unittest discover -s tests -v
```

Training is CPU-only and downloads no external model. The default experiment has
24 authored mutation families with 10 variable-renamed examples per family.
Families stay together: 16 train (160 rows), 4 validation (40), 4 test (40).
The vectorizer is fit on the train only. Deployed Logistic Regression is fixed before
evaluation; SVM results are a comparison, not a basis to tune on the test set.

Synthetic family separation does not eliminate all semantic similarity. Some
families share loop patterns. These results are pilot debugging measurements,
not estimates of general student-population performance. See `docs/MODEL_CARD.md`.

## Limits and honest claims

This implements the scoped Python lab prototype, not every future idea in earlier
brainstorming. No SQL/React runner, GPT/Gemini integration, OCR, fine-tuned transformer,
learned adaptive-success predictor, real CV-job classifier, cloud sync or production
hosting is included. CV mapping and adaptation are rule-based. The only learned
component is the mistake classifier.

Passing the included tests is evidence for those inputs only. It cannot prove
expertise, authorship, independence from external help or suitability for hiring.
The app flags assistance it knows about; copied code from another source cannot
be detected. Do not describe it as proctoring or cheat detection.

The interpreter deliberately supports only documented Python constructs. It is
not an audited public sandbox. Keep the server bound to 127.0.0.1. CV files are
parsed by a third-party library, so use trusted small files only. Passwords are
hashed, but SQLite contents are not encrypted at rest. OS-level file access can
read or modify all local data.

## Team

- MD Shyed Hasan Likhon — 0112330688
- Rahat — 112330518
- Naimur — 112330546
- Srijon — 112330621
- Name to be added — 112330396

## Technical references

- [scikit-learn: avoiding leakage with pipelines](https://scikit-learn.org/stable/common_pitfalls.html)
- [Streamlit application testing](https://docs.streamlit.io/develop/api-reference/app-testing)
- [Python AST reference](https://docs.python.org/3/library/ast.html)

Use assistance according to your course rules. Review labels and understand the
Implementation before presenting results as your team's project.
