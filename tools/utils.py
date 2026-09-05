import enum
import logging
import os
import random
from datetime import datetime

import colorlog
import pytz
import requests
from dotenv import load_dotenv

client = requests.Session()
client.encoding = "utf-8"
tz = pytz.timezone("Asia/Shanghai")

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 "
    "Safari/537.36"
)
LEETCODE_URL = "https://leetcode.cn"
SIGN_IN_URL = f"{LEETCODE_URL}/accounts/login/"
GRAPHQL_URL = f"{LEETCODE_URL}/graphql/"

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLE_PATH = os.path.join(ROOT_DIR, "_posts")
ASSETS_PATH = os.path.join(ROOT_DIR, "assets")
IMAGE_PATH = os.path.join(ROOT_DIR, "assets", "images", "post-list")

load_dotenv()

PROJECT_ACCESS_TOKEN = os.getenv("PROJECT_ACCESS_TOKEN")
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")

STUDY_PLAN_SLUGS_QUERY = """
query studyPlanV2Detail($planSlug: String!) {
  studyPlanV2Detail(planSlug: $planSlug) {
    planSubGroups {
      questions { titleSlug }
    }
  }
}
"""

QUESTION_DETAIL_QUERY = """
query questionData($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionFrontendId
    title
    translatedTitle
    titleSlug
    difficulty
    topicTags { name translatedName id slug }
  }
}
"""

PROBLEMSET_QUESTION_LIST_QUERY = """
query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
  problemsetQuestionList(
    categorySlug: $categorySlug
    limit: $limit
    skip: $skip
    filters: $filters
  ) {
    hasMore
    total
    questions {
      acRate
      difficulty
      freqBar
      frontendQuestionId
      isFavor
      paidOnly
      solutionNum
      status
      title
      titleCn
      titleSlug
      topicTags {
        name
        nameTranslated
        id
        slug
      }
      extra {
        hasVideoSolution
        topCompanyTags {
          imgUrl
          slug
          numSubscribed
        }
      }
    }
  }
}
"""


class Topic(enum.Enum):
    LEETCODE_75 = "leetcode-75"
    TOP_100 = "top-100-liked"
    TOP_150 = "top-interview-150"
    INTERVIEW_GOLDEN = "cracking-the-coding-interview"
    CODING_INTERVIEWS_SPECIAL = "coding-interviews-special"


TOPIC_NAME_MAP = {
    Topic.LEETCODE_75: "LeetCode 75",
    Topic.TOP_100: "LeetCode 热题 100",
    Topic.TOP_150: "面试经典 150 题",
    Topic.INTERVIEW_GOLDEN: "程序员面试金典（第 6 版）",
    Topic.CODING_INTERVIEWS_SPECIAL: "119 经典题变种挑战",
}


def setup_colored_logger():
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )

    handler = colorlog.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(handler)


def get_headers(referer):
    return {
        "User-Agent": USER_AGENT,
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Referer": referer,
    }


def question_tags(question):
    tags = []
    for topic_tag in question.get("topicTags", []):
        tag = topic_tag.get("nameTranslated") or topic_tag.get("name", "").strip()
        if tag:
            tags.append(tag)
    return tags


def is_valid_question_id(question_id):
    value = str(question_id or "").strip()
    if value.isdigit():
        return True

    prefixes = ("面试题 ", "LCP ", "LCR ", "LCS ", "补充题")
    for prefix in prefixes:
        if not value.startswith(prefix):
            continue

        number = value.removeprefix(prefix)
        major_text, separator, minor_text = number.partition(".")
        if not major_text.isdigit() or (separator and not minor_text.isdigit()):
            break
        return True

    offer_prefix = "剑指 Offer "
    if value.startswith(offer_prefix):
        number = value.removeprefix(offer_prefix).replace(" ", "")
        major_text, separator, part_text = number.partition("-")
        part = {"I": 1, "II": 2, "III": 3}.get(part_text, 0)
        if major_text.isdigit() and (not separator or part):
            return True

    return False


def extract_question_id(filename):
    marker = "LeetCode "
    _, separator, remainder = filename.partition(marker)
    if not separator:
        return None

    interview_prefix = "面试题 "
    if remainder.startswith(interview_prefix):
        major, dot, remainder = remainder.removeprefix(interview_prefix).partition(".")
        minor, title_separator, _ = remainder.partition(".")
        if dot and title_separator and major.isdigit() and minor.isdigit():
            return f"面试题 {int(major):02d}.{int(minor):02d}"
        return None

    extra_prefix = "补充题 "
    if remainder.startswith(extra_prefix):
        number, title_separator, _ = remainder.removeprefix(extra_prefix).partition(".")
        if title_separator and number.isdigit():
            return f"补充题{number}"
        return None

    question_id, title_separator, _ = remainder.partition(".")
    question_id = question_id.strip()
    if not title_separator or not is_valid_question_id(question_id):
        return None
    return question_id


def extract_date(title):
    date_text = title[:10]
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError:
        return None
    return date_text


def weekday_to_chinese(weekday_int):
    week_mapping = [
        "星期一",
        "星期二",
        "星期三",
        "星期四",
        "星期五",
        "星期六",
        "星期日",
    ]
    return week_mapping[weekday_int]


def unique_question_level(items):
    priority = {"已掌握": 1, "需复习": 2, "需加强": 3, "未掌握": 4}
    marked = [x for x in items if x in priority]
    if not marked:
        return items
    top = max(marked, key=priority.get)
    return [x for x in items if x not in priority] + [top]


def get_current_time(output_format="%Y-%m-%d %H:%M:%S"):
    return datetime.now().strftime(output_format)


def convert_iso_to_normal_time(iso_time_str, output_format="%Y-%m-%d %H:%M:%S"):
    try:
        dt = datetime.fromisoformat(iso_time_str.replace("Z", "+00:00"))
        return dt.strftime(output_format)
    except ValueError:
        return get_current_time()


def generate_random_permalink():
    return f"{random.randint(10000000, 99999999)}"
