#!/bin/bash
set -e

git config --local user.name "${1:-hgnulb}"
git config --local user.email "${2:-hgnulb@163.com}"
git config --local core.autocrlf input
git config --local pull.rebase true
git config --local fetch.prune true
git config --local core.quotepath false
git config --local alias.up "!git remote update -p; git merge --ff-only @{u}"
git fetch --all --prune
git branch --set-upstream-to="origin/$(git rev-parse --abbrev-ref HEAD)" HEAD 2>/dev/null || true
