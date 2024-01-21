import logging
import os
import random

import pytz as pytz
import requests

logging.basicConfig(level=logging.INFO)
session = requests.Session()
session.encoding = 'utf-8'
tz = pytz.timezone('Asia/Shanghai')

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
LEETCODE_URL = 'https://leetcode.cn'
SIGN_IN_URL = f'{LEETCODE_URL}/accounts/login/'
GRAPHQL_URL = f'{LEETCODE_URL}/graphql/'
SLEEP_TIME = random.randint(5, 10)
RETRY_COUNT = 3
ROOT_DIR = os.path.abspath(os.path.dirname(os.getcwd()))
ARTICLE_PATH = f'{ROOT_DIR}/_posts/'
IMAGE_PATH = f'{ROOT_DIR}/assets/post-list/images'
USER_NAME = 'hgnulb'


def get_headers(referer):
    headers = {
        'User-Agent': USER_AGENT,
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Referer': referer,
    }
    return headers


def question_tags(question, key='nameTranslated'):
    tags = []
    if 'topicTags' in question:
        topic_tags = question['topicTags']
        for topicTag in topic_tags:
            tag = topicTag.get(key, topicTag.get('name', '')).strip()
            if tag:
                tags.append(tag)
    return tags


def retry_if_result_is_none(result):
    return result is None
