import importlib.metadata
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
    from core.model import load_model
    model, model_error = load_model()
    retrain = model is None
    if retrain:
        print(f"Training the local pilot classifier... ({model_error})", flush=True)
        subprocess.run([sys.executable, str(ROOT / "train.py")], cwd=ROOT, check=True)
    print("Ready. Open http://localhost:8501 after the server starts.", flush=True)


if __name__ == "__main__":
    main()
