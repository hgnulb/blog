#!/usr/bin/env bash
if [[ -z "${BASH_VERSION:-}" ]]; then
  exec bash "$0" "$@"
fi

set -euo pipefail

cd "$(dirname "$0")/.."

VENV_DIR=".venv"
PYTHON_BIN="${VENV_DIR}/bin/python"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  python3 -m venv "${VENV_DIR}"
fi

"${PYTHON_BIN}" -m pip install --upgrade pip setuptools
"${PYTHON_BIN}" -m pip install -r tools/requirements.txt
