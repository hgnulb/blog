#!/bin/bash
set -e

COMMIT_MSG=${1:-$(date -u +"update: %Y-%m-%d %H:%M:%S")}
branch="$(git rev-parse --abbrev-ref HEAD)"

if [[ -z "$(git status --porcelain)" ]]; then
  echo "no changes"
  exit 0
fi

git add -A
git commit -m "$COMMIT_MSG"
git fetch origin "$branch"
git rebase "origin/$branch"
git push origin "$branch"
