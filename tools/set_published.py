import logging
import os
from typing import Optional

from md_yml_helper import MarkdownYamlHandler
from utils import ARTICLE_PATH, setup_colored_logger

setup_colored_logger()


def _normalize_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return None


def _prompt_int(label: str) -> Optional[int]:
    while True:
        raw = input(label).strip()
        if not raw:
            print("请输入数字。")
            continue
        try:
            value = int(raw)
        except ValueError:
            print("请输入有效的整数。")
            continue
        return value


def _prompt_bool(label: str, default: bool = True) -> bool:
    while True:
        raw = input(label).strip().lower()
        if not raw:
            return default
        if raw in {"true", "1", "yes", "y", "t"}:
            return True
        if raw in {"false", "0", "no", "n", "f"}:
            return False
        print("请输入 true/false，或直接回车使用默认值。")


def set_published_by_frequency(
    directory: str,
    min_freq: int,
    max_freq: int,
    publish: bool = True,
):
    total = 0
    updated = 0
    unchanged = 0
    skipped = 0
    failed = 0

    for filename in os.listdir(directory):
        if not filename.endswith(".md"):
            continue
        total += 1
        md_path = os.path.join(directory, filename)
        try:
            md_yaml = MarkdownYamlHandler(md_path)
        except (FileNotFoundError, ValueError, TypeError) as e:
            failed += 1
            logging.warning("skip %s: %s", filename, e)
            continue

        freq_value = md_yaml.get("frequency")
        if freq_value is None:
            skipped += 1
            logging.info("skip %s: missing frequency", filename)
            continue

        try:
            freq_int = int(freq_value)
        except (TypeError, ValueError):
            skipped += 1
            logging.info("skip %s: invalid frequency=%s", filename, freq_value)
            continue

        if not (min_freq <= freq_int <= max_freq):
            continue

        old_published = _normalize_bool(md_yaml.get("published"))
        new_published = publish

        if old_published == new_published:
            unchanged += 1
            continue

        updated += 1
        md_yaml.set("published", "true" if new_published else "false")
        md_yaml.save()

    logging.info(
        "done. total=%s updated=%s unchanged=%s skipped=%s failed=%s",
        total,
        updated,
        unchanged,
        skipped,
        failed,
    )


def main():
    print("请输入 frequency 范围（闭区间），用于设置 published：")
    min_freq = _prompt_int("min frequency: ")
    max_freq = _prompt_int("max frequency: ")
    while min_freq > max_freq:
        print("min 不能大于 max，请重新输入。")
        min_freq = _prompt_int("min frequency: ")
        max_freq = _prompt_int("max frequency: ")

    publish = _prompt_bool("publish (true=发布/false=不发布, 默认true): ", default=True)

    set_published_by_frequency(
        directory=ARTICLE_PATH,
        min_freq=min_freq,
        max_freq=max_freq,
        publish=publish,
    )


if __name__ == "__main__":
    main()
