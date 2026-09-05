import json
import logging
from datetime import datetime

from feishu_api import FeishuRequest
from utils import APP_ID, APP_SECRET, setup_colored_logger, tz, weekday_to_chinese

setup_colored_logger()


def main():
    now_shanghai = datetime.now(tz)
    weekday_int = now_shanghai.weekday()
    chinese_weekday = weekday_to_chinese(weekday_int)
    formatted_time = now_shanghai.strftime("%Y-%m-%d %H:%M:%S")
    current_time = f"{formatted_time} {chinese_weekday}"
    content = f":GeneralInMeetingBusy: **<font color='blue'>{current_time}</font>**\n\n:Hundred: **<font color='orange'>你的博客部署成功啦~</font>**\n"
    payload = {
        "config": {"width_mode": "fill"},
        "header": {
            "title": {"tag": "plain_text", "content": "deploy notify"},
            "template": "green",
            "ud_icon": {"tag": "standard_icon", "token": "announce_filled"},
        },
        "elements": [
            {
                "tag": "markdown",
                "content": content,
                "text_align": "left",
                "text_size": "normal",
            }
        ],
    }
    client = FeishuRequest(APP_ID, APP_SECRET)
    res = client.send_bot_message(json.dumps(payload))
    logging.info(
        f"send bot message, res: \n{json.dumps(res, indent=2, ensure_ascii=False)}"
    )


if __name__ == "__main__":
    main()
