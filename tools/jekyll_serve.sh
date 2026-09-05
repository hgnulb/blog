#!/usr/bin/env bash
[[ -z "${BASH_VERSION:-}" ]] && exec bash "$0" "$@"
set -euo pipefail
cd "$(dirname "$0")/.."

lsof -ti:4000 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 0.5

trap 'jobs -p | xargs kill 2>/dev/null || true' EXIT INT TERM

npm run watch:js &
sleep 6
bundle exec jekyll serve --watch
