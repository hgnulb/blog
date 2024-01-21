sh lint-md.sh
sh tools/git-config.sh
if [ -n "$(git status --porcelain)" ]; then
  git up &&
    git add -A &&
    git commit -am "no message" &&
    git push origin gh-pages
else
  echo "no changes"
fi