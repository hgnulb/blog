import json
import logging
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from httpx import HTTPError as HttpxError
from requests.exceptions import RequestException
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from feishu_api import FeishuRequest
from md_yml_helper import MarkdownYamlHandler
from utils import (
    APP_ID,
    APP_SECRET,
    ARTICLE_PATH,
    ASSETS_PATH,
    GRAPHQL_URL,
    LEETCODE_URL,
    client,
    extract_date,
    extract_question_id,
    get_headers,
    question_tags,
    setup_colored_logger,
    tz,
    weekday_to_chinese,
    TOPIC_NAME_MAP,
    PROBLEMSET_QUESTION_LIST_QUERY,
    STUDY_PLAN_SLUGS_QUERY,
    QUESTION_DETAIL_QUERY,
    get_current_time,
    generate_random_permalink,
    Topic,
)

setup_colored_logger()

_LEVEL_THRESHOLDS = [
    (500, "L9"),
    (200, "L8"),
    (100, "L7"),
    (50, "L6"),
    (20, "L5"),
    (10, "L4"),
    (5, "L3"),
    (2, "L2"),
    (0, "L1"),
]
_ALL_LEVELS = {level for _, level in _LEVEL_THRESHOLDS}
GRAPHQL_TIMEOUT = (5, 30)
GRAPHQL_MAX_RETRIES = 3


def _get_level(frequency: int) -> str:
    for threshold, level in _LEVEL_THRESHOLDS:
        if frequency >= threshold:
            return level
    return "L1"


def _should_retry(exc):
    if isinstance(exc, RequestException):
        status = getattr(exc.response, "status_code", None)
        return status is None or status == 429 or status >= 500
    return isinstance(exc, ValueError)


@retry(
    stop=stop_after_attempt(GRAPHQL_MAX_RETRIES),
    wait=wait_exponential_jitter(initial=1, max=4),
    retry=retry_if_exception(_should_retry),
    reraise=True,
)
def _graphql_post(payload, referer):
    response = client.post(
        GRAPHQL_URL,
        json=payload,
        headers=get_headers(referer),
        timeout=GRAPHQL_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("errors"):
        raise RuntimeError(f"graphql errors: {data['errors']}")
    if "data" not in data:
        raise RuntimeError("graphql response has no data")
    return data


def _run_parallel(tasks, worker, on_success, max_workers=3, delay=(0.1, 0.3)):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {}
        for i, task in enumerate(tasks):
            if i > 0:
                time.sleep(random.uniform(*delay))
            future_map[executor.submit(worker, task)] = task
        for future in as_completed(future_map):
            on_success(future_map[future], future.result())


def _fetch_question_page(skip, limit, filters, category_slug):
    data = _graphql_post(
        payload={
            "query": PROBLEMSET_QUESTION_LIST_QUERY,
            "variables": {
                "categorySlug": category_slug,
                "skip": skip,
                "limit": limit,
                "filters": filters,
            },
        },
        referer=f"{LEETCODE_URL}/problemset/",
    )
    return data["data"]["problemsetQuestionList"]["questions"]


def _fetch_plan_slugs(plan_slug):
    data = _graphql_post(
        payload={"query": STUDY_PLAN_SLUGS_QUERY, "variables": {"planSlug": plan_slug}},
        referer=f"{LEETCODE_URL}/studyplan/{plan_slug}/",
    )
    slugs = [
        q["titleSlug"]
        for group in data["data"]["studyPlanV2Detail"]["planSubGroups"]
        for q in group["questions"]
    ]
    return list(dict.fromkeys(slugs))


def _fetch_question(title_slug):
    data = _graphql_post(
        payload={
            "query": QUESTION_DETAIL_QUERY,
            "variables": {"titleSlug": title_slug},
        },
        referer=f"{LEETCODE_URL}/problems/{title_slug}/",
    )
    q = data["data"]["question"]
    return {
        "frontendQuestionId": q["questionFrontendId"],
        "titleCn": q.get("translatedTitle") or q["title"],
        "title": q["title"],
        "titleSlug": q["titleSlug"],
        "difficulty": q["difficulty"].upper(),
        "topicTags": [
            {
                "name": t["name"],
                "nameTranslated": t.get("translatedName") or t["name"],
                "id": t["id"],
                "slug": t["slug"],
            }
            for t in q.get("topicTags", [])
        ],
    }


def _fetch_total(category_slug, filters=None):
    data = _graphql_post(
        payload={
            "query": PROBLEMSET_QUESTION_LIST_QUERY,
            "variables": {
                "categorySlug": category_slug,
                "skip": 0,
                "limit": 1,
                "filters": filters or {},
            },
        },
        referer=f"{LEETCODE_URL}/problemset/",
    )
    return data["data"]["problemsetQuestionList"]["total"]


def _load_codetop_data(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"file {file_path} does not exist")

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"failed to decode json file {file_path}, please check its format"
        ) from exc
    except OSError as exc:
        raise OSError(f"failed to read codetop data file {file_path}") from exc

    if not isinstance(data, list):
        raise ValueError(f"codetop data file {file_path} must contain a json list")

    question_to_company_dict = {}
    question_to_frequency_dict = {}
    question_to_full_info_dict = {}

    for item in data:
        if not isinstance(item, dict):
            logging.warning("skipping invalid codetop record: %r", item)
            continue
        frontend_question_id = item.get("frontend_question_id")
        if frontend_question_id is None:
            continue
        question_to_company_dict[frontend_question_id] = item.get("companys", [])
        question_to_frequency_dict[frontend_question_id] = item.get("frequency", 0)
        question_to_full_info_dict[frontend_question_id] = item

    return (
        question_to_company_dict,
        question_to_frequency_dict,
        question_to_full_info_dict,
    )


def _rename_file(file_path, new_name, keep_directory=True):
    source_path = Path(file_path)
    new_path = source_path.with_name(new_name) if keep_directory else Path(new_name)
    try:
        source_path.rename(new_path)
        logging.warning("renamed file: %s -> %s", source_path, new_path)
    except FileNotFoundError:
        logging.error("renamed file, err: %s not found", source_path)
    except PermissionError:
        logging.error("renamed file, err: permission denied for %s", source_path)
    except OSError:
        logging.exception("renamed file, err: %s", source_path)


def _build_article_lines(
    question_id,
    question_name,
    title_slug,
    difficulty_level,
    difficulty,
    tags,
    question_url,
    random_num,
    published,
):
    return [
        "---",
        "layout: post",
        f"title: LeetCode {question_id}. {question_name}",
        f"slug: {title_slug}",
        f"question_id: {question_id}",
        "frequency: 0",
        f"permalink: /:year/{random_num}",
        f"categories: [{difficulty_level},LeetCode]",
        f'tags: [{",".join(tags)}]',
        f"difficulty: {difficulty}",
        "top: false",
        "solved: false",
        f"published: {published}",
        time.strftime("date: %Y-%m-%d %H:%M:%S", time.localtime()),
        "---",
        "",
        "## 题目描述",
        "",
        f"> ✅ [{question_id}. {question_name}]({question_url})",
        "",
        "## 题意分析",
        "",
        "## 解法一：方法名称",
        "",
        "### 核心思路",
        "",
        "### 解题步骤",
        "",
        "### 代码实现",
        "",
        "```java",
        "write your code here",
        "```",
        "",
        "```go",
        "write your code here",
        "```",
        "",
        "### 复杂度分析",
        "",
        "### 关键点总结",
        "",
        "## 解法对比",
        "",
        "## 易错点总结",
        "",
        "## 相似题目",
    ]


def send_leetcode_notification():
    now_shanghai = datetime.now(tz)
    weekday_int = now_shanghai.weekday()
    chinese_weekday = weekday_to_chinese(weekday_int)
    formatted_time = now_shanghai.strftime("%Y-%m-%d %H:%M:%S")
    current_time = f"{formatted_time} {chinese_weekday}"
    content = (
        f":GeneralInMeetingBusy: **<font color='blue'>{current_time}</font>**\n\n:CheckMark: **<font "
        f"color='purple'>你已成功获取 LeetCode 网站的数据啦~</font>**\n"
    )
    payload = {
        "config": {"width_mode": "fill"},
        "header": {
            "title": {"tag": "plain_text", "content": "获取 LeetCode 网站数据通知"},
            "template": "turquoise",
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
    res = FeishuRequest(APP_ID, APP_SECRET).send_bot_message(json.dumps(payload))
    logging.info(
        f"send bot message, res: \n{json.dumps(res, indent=2, ensure_ascii=False)}"
    )


def _build_filename_dict() -> dict:
    result = {}
    for filename in os.listdir(ARTICLE_PATH):
        if not filename.endswith(".md"):
            continue
        qid = extract_question_id(filename)
        if qid:
            result[qid] = filename
    return result


def _apply_codetop_categories(md_yaml, frequency: int, solved: bool):
    if solved:
        md_yaml.append("categories", ["CodeTop", "CodeTop-I"])
        md_yaml.remove("categories", ["CodeTop-II"])
    else:
        md_yaml.append("categories", ["CodeTop", "CodeTop-II"])
        md_yaml.remove("categories", ["CodeTop-I"])

    level = _get_level(frequency)
    md_yaml.append("categories", [level])
    md_yaml.remove("categories", list(_ALL_LEVELS - {level}))


class GenerateLeetCodeArticle:

    def __init__(self):
        self.today = datetime.today()
        self.today_prefix = self.today.strftime("%Y-%m-%d-")
        (
            self.question_to_company_dict,
            self.question_to_frequency_dict,
            self.question_to_full_info_dict,
        ) = _load_codetop_data(os.path.join(ASSETS_PATH, "data", "codetop_data.json"))
        self.filename_dict = _build_filename_dict()

    def _get_companies(self, question_id):
        return self.question_to_company_dict.get(question_id, [])

    def _get_frequency(self, question_id):
        return self.question_to_frequency_dict.get(question_id, 0)

    def _get_full_info(self, question_id):
        return self.question_to_full_info_dict.get(question_id, {})

    def fetch_all_questions(
        self, topic=None, category_slug="all-code-essentials", limit=100, max_workers=3
    ):
        filters = {}
        if topic:
            filters = {"listId": topic.value}

        total = _fetch_total(category_slug, filters)
        logging.warning(
            "total questions to fetch: %s (topic=%s, filters=%s)", total, topic, filters
        )

        def on_success(skip, questions):
            for q in questions:
                self._sync_article(q, topic)
            logging.info("fetched %s questions for skip=%s", len(questions), skip)

        _run_parallel(
            tasks=list(range(0, total, limit)),
            worker=lambda skip: _fetch_question_page(
                skip, limit, filters, category_slug
            ),
            on_success=on_success,
            max_workers=max_workers,
            delay=(0.2, 0.5),
        )
        self.filename_dict = _build_filename_dict()

    def fetch_study_plan_questions(self, topic, max_workers=3):
        if not topic:
            return
        plan_slug = topic.value
        logging.warning("fetching study plan: %s", plan_slug)
        slugs = _fetch_plan_slugs(plan_slug)
        logging.warning("total questions in study plan [%s]: %s", plan_slug, len(slugs))

        def on_success(slug, question):
            self._sync_article(question, topic)
            logging.info("fetched question: %s", slug)

        _run_parallel(
            tasks=slugs,
            worker=_fetch_question,
            on_success=on_success,
            max_workers=max_workers,
        )
        self.filename_dict = _build_filename_dict()

    def _apply_question_metadata(self, md_yaml, question_id: str, extra_tags=None):
        company_list = self._get_companies(question_id)
        all_tags = list(extra_tags or []) + company_list
        md_yaml.append("tags", all_tags)

        evaluation_time = self._get_full_info(question_id).get("evaluation_time")
        if evaluation_time:
            md_yaml.set("date", evaluation_time)

        category_list = md_yaml.get("categories")
        if category_list and "已掌握" in category_list:
            md_yaml.set("solved", "true")

        solved = md_yaml.get("solved")
        if solved != "true" and solved is not True:
            md_yaml.remove("categories", ["已掌握"])

        frequency = int(self._get_frequency(question_id))
        md_yaml.set("frequency", frequency)
        if frequency:
            md_yaml.set("published", "true")
            is_solved = solved == "true" or solved is True
            _apply_codetop_categories(md_yaml, frequency, is_solved)

    def _update_article(
        self,
        old_filename,
        topic,
        new_tags,
        question_id,
        article_name,
        slug,
        difficulty,
        difficulty_level,
    ):
        md_path = Path(ARTICLE_PATH) / old_filename
        md_yaml = MarkdownYamlHandler(md_path)

        if not question_id:
            return

        categories = []
        if topic:
            categories.append(TOPIC_NAME_MAP[topic])

        prefix_to_question = {
            "面试题": "程序员面试金典（第 6 版）",
            "LCR": "LCR",
            "LCP": "LCP",
            "LCS": "LCS",
        }
        question_flag = next(
            (
                flag
                for prefix, flag in prefix_to_question.items()
                if question_id.startswith(prefix)
            ),
            None,
        )
        if question_flag:
            if question_id.startswith("面试题"):
                categories.append(question_flag)
            else:
                new_tags.append(question_flag)

            if question_id.startswith("面试题") or (
                question_id.startswith("LCR") and "LCR 001" <= question_id <= "LCR 119"
            ):
                md_yaml.set("published", "true")
            else:
                md_yaml.set("published", "false")

        self._apply_question_metadata(md_yaml, question_id, new_tags)

        md_yaml.setnx("layout", "post")
        md_yaml.set("title", article_name)
        md_yaml.set("slug", slug)
        md_yaml.set("question_id", question_id)
        md_yaml.set("difficulty", difficulty)
        md_yaml.remove("categories", ["简单", "中等", "困难"])
        md_yaml.append("categories", [difficulty_level])
        md_yaml.append("categories", categories)
        md_yaml.setnx("top", "false")
        md_yaml.setnx("solved", "false")
        md_yaml.setnx("published", "true")
        md_yaml.setnx("date", get_current_time())

        md_yaml.save()
        new_title = f"{extract_date(old_filename)}-{article_name}.md"
        if new_title != old_filename:
            _rename_file(md_path, new_title)

    def _sync_article(self, question, topic):
        title_cn = question.get("titleCn", "").strip()
        if not title_cn:
            return

        question_id = question["frontendQuestionId"]
        if not topic:
            frequency = int(self._get_frequency(question_id))
            if not frequency:
                return

        question_name = title_cn
        article_name = f"LeetCode {question_id}. {question_name}"
        title_slug = question["titleSlug"]
        difficulty = question.get("difficulty", "MEDIUM").lower()
        difficulty_level = {"easy": "简单", "medium": "中等", "hard": "困难"}.get(
            difficulty, "中等"
        )
        question_url = f"{LEETCODE_URL}/problems/{title_slug}/"
        tags = question_tags(question)

        matched_filename = self.filename_dict.get(question_id)
        if matched_filename:
            self._update_article(
                matched_filename,
                topic,
                tags,
                question_id,
                article_name,
                title_slug,
                difficulty,
                difficulty_level,
            )
            return

        lines = _build_article_lines(
            question_id,
            question_name,
            title_slug,
            difficulty_level,
            difficulty,
            tags,
            question_url,
            generate_random_permalink(),
            "true",
        )

        new_filename = f"{self.today_prefix}{article_name}.md"
        with open(
            os.path.join(ARTICLE_PATH, new_filename), mode="w+", encoding="utf-8"
        ) as f:
            f.write("\n".join(lines))
        self.filename_dict[question_id] = new_filename
        logging.info("generate markdown article [%s] successful!", new_filename)

    def update_front_matter(self):
        for filename in os.listdir(ARTICLE_PATH):
            if not filename.endswith(".md"):
                continue

            md_path = Path(ARTICLE_PATH) / filename
            md_yaml = MarkdownYamlHandler(md_path)

            md_yaml.setnx("layout", "post")
            md_yaml.setnx("frequency", 0)
            md_yaml.setnx("top", "false")
            md_yaml.setnx("solved", "false")
            md_yaml.setnx("published", "true")
            md_yaml.setnx("date", get_current_time())

            question_id = str(md_yaml.get("question_id") or "")
            if not question_id:
                continue

            if question_id.startswith("LCR"):
                md_yaml.set("published", "true")
                if "LCR 001" <= question_id <= "LCR 119":
                    md_yaml.append(
                        "categories", ["剑指 Offer", "剑指 Offer（专项突击版）"]
                    )
                elif "LCR 120" <= question_id <= "LCR 194":
                    md_yaml.append(
                        "categories", ["剑指 Offer", "剑指 Offer（第 2 版）"]
                    )

            self._apply_question_metadata(md_yaml, question_id)

            md_yaml.save()


def main():
    generate_leetcode_article = GenerateLeetCodeArticle()
    generate_leetcode_article.fetch_all_questions()
    generate_leetcode_article.fetch_study_plan_questions(topic=Topic.LEETCODE_75)
    generate_leetcode_article.fetch_study_plan_questions(topic=Topic.TOP_100)
    generate_leetcode_article.fetch_study_plan_questions(topic=Topic.TOP_150)
    generate_leetcode_article.fetch_study_plan_questions(topic=Topic.INTERVIEW_GOLDEN)
    generate_leetcode_article.fetch_study_plan_questions(
        topic=Topic.CODING_INTERVIEWS_SPECIAL
    )
    generate_leetcode_article.update_front_matter()
    try:
        send_leetcode_notification()
    except (HttpxError, RuntimeError, ValueError, KeyError):
        logging.exception("articles were updated, but the leetcode notification failed")


if __name__ == "__main__":
    main()
