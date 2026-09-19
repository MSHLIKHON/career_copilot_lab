"""Check local dependencies and train a compatible model before launching."""
import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    if not (3, 11) <= sys.version_info[:2] <= (3, 13):
        raise SystemExit("Please use Python 3.12 (supported: 3.11-3.13).")
    required = {"streamlit": "1.49.1", "scikit-learn": "1.8.0", "pandas": None,
                "numpy": None, "pypdf": None, "joblib": None}
    install = False
    for package, version in required.items():
        try:
            installed = importlib.metadata.version(package)
            if version and installed != version:
                install = True
        except importlib.metadata.PackageNotFoundError:
            install = True
    if install:
        print("Installing project packages. Internet is needed for this first setup.", flush=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")], check=True)
    import sklearn
    metrics = ROOT / "models" / "metrics.json"
    retrain = not (ROOT / "models" / "classifier.joblib").exists()
    try:
        retrain = retrain or json.loads(metrics.read_text())["sklearn_version"] != sklearn.__version__
    except (OSError, ValueError, KeyError):
        retrain = True
    if retrain:
        print("Training the local pilot classifier...", flush=True)
        subprocess.run([sys.executable, str(ROOT / "train.py")], cwd=ROOT, check=True)
    print("Ready. Open http://localhost:8501 after the server starts.", flush=True)


if __name__ == "__main__":
    main()
