#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"

is_supported() {
  "$1" -c 'import sys; raise SystemExit(0 if (3, 11) <= sys.version_info[:2] <= (3, 13) else 1)' >/dev/null 2>&1
}

if [ -x .venv/bin/python ]; then
  if ! is_supported .venv/bin/python; then
    echo "The existing .venv uses an unsupported Python version."
    echo "Remove .venv, install Python 3.12 (supported: 3.11-3.13), then run this script again."
    exit 1
  fi
else
  python_cmd=""
  for candidate in python3.12 python3.13 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1 && is_supported "$candidate"; then
      python_cmd="$candidate"
      break
    fi
  done
  if [ -z "$python_cmd" ]; then
    echo "Python 3.12 is recommended (supported: 3.11-3.13). Install it and try again."
    exit 1
  fi
  "$python_cmd" -m venv .venv
fi
.venv/bin/python bootstrap.py
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
