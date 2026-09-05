#!/bin/bash
set -e

branch="$(git rev-parse --abbrev-ref HEAD)"

git checkout --orphan latest_branch
git add -A
git commit -m "${1:-$(date -u +"update: %Y-%m-%d %H:%M:%S")}" --allow-empty
git branch -D "$branch"
git branch -m "$branch"
git push -f origin "$branch"
