#!/usr/bin/env bash
if [[ -z "${BASH_VERSION:-}" ]]; then
  exec bash "$0" "$@"
fi

set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -d node_modules ]]; then
  exit 0
fi

if [[ -f package-lock.json ]]; then
  npm ci
else
  npm install
fi
