import json
import logging
import os
from collections import defaultdict
from datetime import datetime

from feishu_api import FeishuRequest
from utils import (
    APP_ID,
    APP_SECRET,
    ARTICLE_PATH,
    extract_question_id,
    setup_colored_logger,
    tz,
    weekday_to_chinese,
)

setup_colored_logger()


def group_files_by_question_id(directory):
    grouped_files = defaultdict(list)
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            question_id = extract_question_id(filename)
            if question_id:
                grouped_files[question_id].append(filename)
    return grouped_files


def find_duplicates(grouped_files):
    return {
        question_id: sorted(files)
        for question_id, files in grouped_files.items()
        if len(files) > 1
    }


def format_content(duplicate_files):
    content_parts = []

    for files in duplicate_files.values():
        file_list = "\n".join(
            [f":CheckMark: **<font color='grey'>{file}</font>**" for file in files]
        )
        content_parts.append(f"{file_list}\n---")

    return "\n".join(content_parts)


def send_feishu_message(content):
    if content:
        now_shanghai = datetime.now(tz)
        weekday_int = now_shanghai.weekday()
        chinese_weekday = weekday_to_chinese(weekday_int)
        formatted_time = now_shanghai.strftime("%Y-%m-%d %H:%M:%S")
        current_time = f"{formatted_time} {chinese_weekday}"

        content = f":GeneralInMeetingBusy: **<font color='blue'>{current_time}</font>**\n\n{content}\n"
        payload = {
            "config": {"width_mode": "fill"},
            "header": {
                "title": {"tag": "plain_text", "content": "重复文章待处理通知"},
                "template": "blue",
                "ud_icon": {"tag": "standard_icon", "token": "announce_filled"},
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": content,
                    "text_align": "left",
                    "text_size": "normal",
                },
            ],
        }

        client = FeishuRequest(APP_ID, APP_SECRET)
        res = client.send_bot_message(json.dumps(payload))
        logging.info(
            f"sent bot message, response: \n{json.dumps(res, indent=2, ensure_ascii=False)}"
        )


def main():
    grouped_files = group_files_by_question_id(ARTICLE_PATH)
    duplicate_files = find_duplicates(grouped_files)

    logging.info("checked %s question ids in %s", len(grouped_files), ARTICLE_PATH)
    if not duplicate_files:
        logging.info("no duplicate articles found")
        return

    logging.warning("found %s duplicate question ids", len(duplicate_files))
    for question_id, files in duplicate_files.items():
        logging.warning("%s: %s", question_id, ", ".join(files))

    content = format_content(duplicate_files)
    send_feishu_message(content)


if __name__ == "__main__":
    main()
