import json
import logging
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import requests
from httpx import HTTPError as HttpxError
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from feishu_api import FeishuRequest
from utils import (
    APP_ID,
    APP_SECRET,
    ASSETS_PATH,
    convert_iso_to_normal_time,
    get_current_time,
    setup_colored_logger,
    tz,
    weekday_to_chinese,
)

setup_colored_logger()

QUESTIONS_URL = "https://codetop.cc/api/questions/?page={page}"
COMPANY_QUESTIONS_URL = (
    "https://codetop.cc/api/questions/?company={company_id}&page={page}"
)
COMPANIES_URL = "https://codetop.cc/api/companies/"
TIMEOUT = (5, 20)
MAX_RETRIES = 5
PAGE_SIZE = 20


def _should_retry(exc):
    if isinstance(exc, requests.RequestException):
        status = getattr(exc.response, "status_code", None)
        return status is None or status == 429 or status >= 500
    return isinstance(exc, ValueError)


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential_jitter(initial=5, max=120),
    retry=retry_if_exception(_should_retry),
    reraise=True,
)
def request_json(url):
    response = requests.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def get_total_pages(url):
    count = int(request_json(url.format(page=1))["count"])
    return (count + PAGE_SIZE - 1) // PAGE_SIZE


def run_parallel(pages, worker, max_workers, label="page"):
    completed = 0
    total = len(pages)
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(worker, page): page for page in pages}
        for future in as_completed(futures):
            page = futures[future]
            try:
                data = future.result()
                results.extend(data)
                completed += 1
                logging.info(
                    "fetched %s %d/%d (%d items)", label, completed, total, len(data)
                )
            except Exception:
                logging.exception(
                    "failed to fetch %s %d/%d", label, completed + 1, total
                )
                completed += 1
                raise
    return results


def build_question_map(items):
    result = {}
    for item in items:
        question_id = item.get("leetcode", {}).get("frontend_question_id")
        if question_id:
            result[str(question_id)] = {
                "frontend_question_id": str(question_id),
                "evaluation_time": convert_iso_to_normal_time(
                    item.get("time") or get_current_time()
                ),
                "frequency": item.get("value", 0),
                "companys": [],
            }
    return result


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False
        ) as file:
            temp_path = file.name
            json.dump(data, file, ensure_ascii=False, indent=4)
        os.replace(temp_path, path)
    except OSError:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
        raise


def send_codetop_notify():
    now = datetime.now(tz)
    current_time = f"{now:%Y-%m-%d %H:%M:%S} {weekday_to_chinese(now.weekday())}"
    content = (
        f":GeneralInMeetingBusy: **<font color='blue'>{current_time}</font>**\n\n"
        ":FINGERHEART: **<font color='orange'>"
        "你已成功获取 CodeTop 网站的数据啦~</font>**\n"
    )
    payload = {
        "config": {"width_mode": "fill"},
        "header": {
            "title": {"tag": "plain_text", "content": "获取 CodeTop 网站数据通知"},
            "template": "indigo",
            "ud_icon": {"tag": "standard_icon", "token": "announce_filled"},
        },
        "elements": [{"tag": "markdown", "content": content}],
    }
    res = FeishuRequest(APP_ID, APP_SECRET).send_bot_message(json.dumps(payload))
    logging.info(
        "sent bot message, res: \n%s",
        json.dumps(res, indent=2, ensure_ascii=False),
    )


def main():
    companies = request_json(COMPANIES_URL)
    total_pages = get_total_pages(QUESTIONS_URL)
    logging.info("fetching %d pages of questions...", total_pages)
    question_items = run_parallel(
        range(1, total_pages + 1),
        lambda page: request_json(QUESTIONS_URL.format(page=page)).get("list", []),
        max_workers=2,
        label="page",
    )
    question_map = build_question_map(question_items)
    if not question_map:
        raise RuntimeError("no codetop questions fetched")
    logging.info("fetched %d unique questions", len(question_map))

    for company in companies:
        company_id = company.get("id")
        company_name = company.get("name")
        if company_id is None or not company_name:
            continue
        if company_name == "bilibili":
            company_name = "哔哩哔哩"

        url = COMPANY_QUESTIONS_URL.format(company_id=company_id, page="{page}")
        company_total_pages = get_total_pages(url)
        logging.info("fetching %d pages for %s...", company_total_pages, company_name)
        items = run_parallel(
            range(1, company_total_pages + 1),
            lambda page: request_json(url.format(page=page)).get("list", []),
            max_workers=1,
            label=f"page for {company_name}",
        )
        for item in items:
            question_id = str(
                item.get("leetcode", {}).get("frontend_question_id") or ""
            )
            if question_id in question_map:
                company_list = question_map[question_id]["companys"]
                if company_name not in company_list:
                    company_list.append(company_name)

    output_path = Path(ASSETS_PATH) / "data" / "codetop_data.json"
    write_json(output_path, list(question_map.values()))
    logging.info("wrote %d questions to %s", len(question_map), output_path)

    try:
        send_codetop_notify()
    except (HttpxError, RuntimeError, ValueError, KeyError):
        logging.exception("data saved, but notification failed")


if __name__ == "__main__":
    main()
