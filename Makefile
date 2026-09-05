USER_NAME ?= hgnulb
USER_EMAIL ?= hgnulb@163.com
COMMIT_MSG ?= $(shell date -u +"update: %Y-%m-%d %H:%M:%S")
PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

.PHONY: format install install_node install_ruby install_python \
	build_js dev prod build \
	git_config git_push git_cleanup \
	get_codetop_data generate_leetcode_article generate_emoji_scss \
	create_article_template cleanup_workflow cleanup_unused_image \
	check_duplicates set_published notify_deploy

format:
	bash tools/format.sh

install: install_node install_ruby install_python

install_node:
	bash tools/npm_install.sh

install_ruby:
	bash tools/bundle_install.sh

install_python:
	bash tools/python_install.sh

dev: install_node install_ruby
	bash tools/jekyll_serve.sh

build_js:
	npm run build:js:prod

prod: install_node install_ruby build_js
	JEKYLL_ENV=production bundle exec jekyll serve --config _config.yml,_config_prod.yml

build: install_node install_ruby build_js
	JEKYLL_ENV=production bundle exec jekyll build --config _config.yml,_config_prod.yml

# Git
git_config:
	bash tools/git_config.sh "$(USER_NAME)" "$(USER_EMAIL)"
git_push: git_config
	bash tools/git_push.sh "$(COMMIT_MSG)"
git_cleanup: git_config
	bash tools/git_cleanup.sh

# Python
get_codetop_data:
	$(PYTHON) tools/get_codetop_data.py
generate_leetcode_article:
	$(PYTHON) tools/generate_leetcode_article.py
generate_emoji_scss:
	$(PYTHON) tools/generate_emoji_scss.py
create_article_template:
	$(PYTHON) tools/create_article_template.py
cleanup_workflow:
	$(PYTHON) tools/cleanup_workflow.py
cleanup_unused_image:
	$(PYTHON) tools/cleanup_unused_image.py
check_duplicates:
	$(PYTHON) tools/check_duplicates.py
set_published:
	$(PYTHON) tools/set_published.py
notify_deploy:
	$(PYTHON) tools/notify_deploy.py
