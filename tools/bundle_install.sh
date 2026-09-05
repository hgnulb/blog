#!/usr/bin/env bash
if [[ -z "${BASH_VERSION:-}" ]]; then
  exec bash "$0" "$@"
fi

set -euo pipefail

cd "$(dirname "$0")/.."

if bundle check >/dev/null 2>&1; then
  exit 0
fi

command -v bundle >/dev/null 2>&1 || gem install bundler --no-document

bundle install --jobs=4
