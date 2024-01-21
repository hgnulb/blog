sh lint-md.sh
sh tools/git-config.sh
git checkout --orphan latest_branch
git add -A
git commit -am "no message"
git branch -D gh-pages
git branch -m gh-pages
git push -f origin gh-pages
