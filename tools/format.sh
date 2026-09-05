#!/bin/bash
set -eu

# 检查 prettier
if [ ! -f node_modules/.bin/prettier ]; then
  echo "Installing prettier..."
  npm install --save-dev prettier --silent
fi

# 检查 black
if [ ! -x "$(command -v black)" ]; then
  echo "Installing black..."
  pip install black -q
fi

# 格式化 JS/TS/CSS/SCSS/Markdown/JSON/YAML
node_modules/.bin/prettier --write --cache --cache-strategy content --log-level warn \
  --ignore-path .prettierignore \
  "**/*.{js,ts,css,scss,md,json,yml,yaml}"

# 格式化 Python
black -q --exclude='/(node_modules|_site|\.git|\.agents|\.claude|\.jekyll-cache|vendor)/' .

echo "Format complete."
