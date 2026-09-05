import logging
import os
import sys
from datetime import datetime

from utils import (
    ARTICLE_PATH,
    setup_colored_logger,
    get_current_time,
    generate_random_permalink,
)

setup_colored_logger()


def sanitize_filename(name: str) -> str:
    return name.translate(str.maketrans("", "", '\\/*?:"<>|'))


def create_md_file(title, categories, tags):
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")

    safe_title = sanitize_filename(title)
    file_name = f"{current_date}-{safe_title}.md"
    permalink = generate_random_permalink()

    content = f"""---
	layout: post
	title: {title}
	permalink: /:year/{permalink}
	categories: [{categories}]
	tags: [{tags}]
top: false
solved: false
published: true
date: {get_current_time()}
---

"""
    save_path = os.path.join(ARTICLE_PATH, file_name)
    os.makedirs(ARTICLE_PATH, exist_ok=True)

    try:
        with open(save_path, "w", encoding="utf-8") as file:
            file.write(content)
        logging.info("文件【%s】已创建！", file_name)
    except OSError:
        logging.exception("文件保存时发生错误")


def safe_input(prompt: str) -> str:
    sys.stdout.write(prompt)
    sys.stdout.flush()
    return input().strip()


def main():
    title = safe_input("请输入文章标题: ")
    categories = safe_input("请输入文章分类(用逗号分隔): ")
    tags = safe_input("请输入文章标签(用逗号分隔): ")

    if not title or not categories or not tags:
        logging.error("所有字段都不允许为空！")
        return

    categories = ", ".join(c.strip() for c in categories.split(","))
    tags = ", ".join(t.strip() for t in tags.split(","))

    create_md_file(title, categories, tags)


if __name__ == "__main__":
    main()
