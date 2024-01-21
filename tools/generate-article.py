import concurrent
import datetime
import json
import string
import time
from concurrent.futures import ThreadPoolExecutor

from tenacity import retry, wait_fixed, retry_if_exception_type, retry_if_result, stop_after_attempt, stop_after_delay

from login import LeetCodeLogin
from utils import *


class GenerateArticle:
    def __init__(self):
        self.filename_list = os.listdir(ARTICLE_PATH)
        self.title_slug_list = []

    @retry(wait=wait_fixed(SLEEP_TIME),
           retry=retry_if_exception_type() | retry_if_result(retry_if_result_is_none),
           reraise=True,
           stop=stop_after_attempt(RETRY_COUNT) | stop_after_delay(180))
    def get_problems(self, skip=0, limit=100):
        try:
            params = {
                'operationName': 'problemsetQuestionList',
                'query':
                    '''
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
                    ''',
                'variables': {
                    'categorySlug': '',
                    'skip': skip,
                    'limit': limit,
                    'filters': {}
                }
            }
            resp = session.post(GRAPHQL_URL, data=json.dumps(params).encode('utf-8'), headers=get_headers(f'{LEETCODE_URL}/problemset/all/'), timeout=180)
            if resp.ok:
                content = json.loads(resp.content.decode('utf-8'))
                return content
            else:
                logging.error(f'get problems failed! status code={resp.status_code}')
        except RuntimeError:
            raise Exception('get problems failed!')

    def get_all_problems(self):
        logging.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ fetch all problems start')
        start_time = time.process_time()
        has_more, skip_num, limit_num = True, 0, 100
        while has_more:
            try:
                start = time.process_time()
                content = self.get_problems(skip=skip_num, limit=limit_num)
                if not content:
                    break
                end = time.process_time()
                logging.info(f'get problems [{skip_num}, {skip_num + limit_num}) successful! cost time %.2f ms', (end - start) * 1000)
            except RuntimeError:
                logging.error('get all problems failed!')
                break
            else:
                has_more = content['data']['problemsetQuestionList']['hasMore']
                skip_num += limit_num
                questions = content['data']['problemsetQuestionList']['questions']
                if not has_more:
                    logging.info('total question count: %s', content['data']['problemsetQuestionList']['total'])
                for question in questions:
                    title = str(question.get('title', '')).strip()
                    title_cn = str(question.get('titleCn', '')).strip()
                    title_slug = question['titleSlug']
                    if title != '' or title_cn != '':
                        self.title_slug_list.append(title_slug)
        logging.info('total time: %.2f s', time.process_time() - start_time)
        logging.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ fetch all problems finish')

    @retry(wait=wait_fixed(SLEEP_TIME),
           retry=retry_if_exception_type() | retry_if_result(retry_if_result_is_none),
           reraise=True,
           stop=stop_after_attempt(RETRY_COUNT) | stop_after_delay(60))
    def get_question_data(self, title_slug):
        try:
            params = {
                'operationName': 'questionData',
                'query':
                    '''
                    query questionData($titleSlug: String!) {
                      question(titleSlug: $titleSlug) {
                        questionId
                        questionFrontendId
                        categoryTitle
                        boundTopicId
                        title
                        titleSlug
                        content
                        translatedTitle
                        translatedContent
                        isPaidOnly
                        difficulty
                        likes
                        dislikes
                        isLiked
                        similarQuestions
                        contributors {
                          username
                          profileUrl
                          avatarUrl
                          __typename
                        }
                        langToValidPlayground
                        topicTags {
                          name
                          slug
                          translatedName
                          __typename
                        }
                        companyTagStats
                        codeSnippets {
                          lang
                          langSlug
                          code
                          __typename
                        }
                        stats
                        hints
                        solution {
                          id
                          canSeeDetail
                          __typename
                        }
                        status
                        sampleTestCase
                        metaData
                        judgerAvailable
                        judgeType
                        mysqlSchemas
                        enableRunCode
                        envInfo
                        book {
                          id
                          bookName
                          pressName
                          source
                          shortDescription
                          fullDescription
                          bookImgUrl
                          pressImgUrl
                          productUrl
                          __typename
                        }
                        isSubscribed
                        isDailyQuestion
                        dailyRecordStatus
                        editorType
                        ugcQuestionId
                        style
                        exampleTestcases
                        jsonExampleTestcases
                        __typename
                      }
                    }
                    ''',
                'variables': {
                    'titleSlug': title_slug
                }
            }
            resp = session.post(GRAPHQL_URL, data=json.dumps(params).encode('utf-8'), timeout=60, headers=get_headers(f'{LEETCODE_URL}/problems/{title_slug}/'))
            if resp.ok:
                content = json.loads(resp.content.decode('utf-8'))
                return content
            else:
                logging.error(f'get question data failed! status code={resp.status_code}')
        except RuntimeError:
            raise Exception('get question data failed!')

    def generate_markdown_content(self, question):
        translated_title = question.get('translatedTitle', '').strip()
        if not translated_title:
            return
        is_liked = bool(question['isLiked'])
        if not is_liked:
            return
        question_id = question['questionFrontendId']
        question_name = translated_title
        today = datetime.date.today()
        article_name = f'LeetCode {question_id}. {question_name}.md'
        today_article_path = ARTICLE_PATH + today.strftime('%Y-%m-%d-') + article_name
        suffix = [filename for filename in self.filename_list if filename.endswith(article_name)]
        if len(suffix) > 0:
            return
        title_slug = question['titleSlug']
        difficulty = str(question.get('difficulty', 'medium')).lower()
        if difficulty == 'easy':
            difficulty_level = "简单"
        elif difficulty == 'medium':
            difficulty_level = "中等"
        elif difficulty == 'hard':
            difficulty_level = "困难"
        else:
            difficulty_level = "中等"
        question_url = f'{LEETCODE_URL}/problems/{title_slug}/'
        random_num = ''.join(map(lambda num: random.choice(string.digits), range(8)))
        similar_question_list = []
        if 'similarQuestions' in question:
            similar_questions = json.loads(question['similarQuestions'])
            for similarQuestion in similar_questions:
                similar_question_name = similarQuestion['translatedTitle'] if similarQuestion.get('translatedTitle', '') != '' else similarQuestion['title']
                similar_title_slug = similarQuestion['titleSlug']
                similar_question_list.append({
                    'question_name': str(similar_question_name).strip(),
                    'question_url': f'{LEETCODE_URL}/problems/{similar_title_slug}/',
                    'difficulty': str(similarQuestion.get('difficulty', 'medium')).title()
                })
        tags = question_tags(question, 'translatedName')
        if question_name != '' and len(tags) > 0:
            markdown_content_list = ['---', 'layout: post', f'title: LeetCode {question_id}. {question_name}', f'slug: {title_slug}', f'permalink: /{random_num}', f'categories: [{difficulty_level},LeetCode]', 'tags: [%s]' % ','.join(tags), f'difficulty: {difficulty}', 'published: true']
            markdown_content_list.extend([time.strftime('date: %Y-%m-%d %H:%M:%S', time.localtime()), '---', '', '{% include common/toc.html %}', ''])
            markdown_content_list.extend(['## 题目描述', '', f'> 🔥 [{question_id}. {question_name}]({question_url})', ''])
            markdown_content_list.extend(['## 思路分析', ''])
            markdown_content_list.extend(['> 思路描述', ''])
            markdown_content_list.extend(['## 参考代码', ''])
            markdown_content_list.extend(['```go', 'write your code here', '```', '', '```go', 'write your code here', '```'])
            markdown_content_list.extend(['<a class="button show-hidden">🍏 点击查看 Java 题解</a>', '', '```java', 'write your code here', '```'])
            if len(similar_question_list) > 0:
                markdown_content_list.extend(['', '## 相似题目', ''])
                markdown_content_list.append('| 题目                                                         | 难度   | 题解 |')
                markdown_content_list.append('| ------------------------------------------------------------ | ------ | ---- |')
                for similar_question in similar_question_list:
                    markdown_content_list.append('| [%s](%s) | %s |      |' % (similar_question['question_name'], similar_question['question_url'], similar_question['difficulty']))
            if len(markdown_content_list) > 0:
                with open(today_article_path, mode='w+', encoding='utf-8') as article:
                    article.write('\n'.join(markdown_content_list))
                logging.info('generate markdown article [%s] successful!', today.strftime(f'%Y-%m-%d-{article_name}'))

    def run(self, max_threads=10):
        self.get_all_problems()

        def fetch_question_data(title_slug):
            logging.info(f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ fetch question [{title_slug}] start')
            content = self.get_question_data(title_slug)
            if content:
                logging.info(f'get question [{title_slug}] successful!')
                self.generate_markdown_content(content['data']['question'])
            logging.info(f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ fetch question [{title_slug}] finish\n')

        with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
            for titleSlug in self.title_slug_list:
                executor.submit(fetch_question_data, titleSlug)


if __name__ == '__main__':
    logging.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ login start')
    leetCodeLogin = LeetCodeLogin()
    leetCodeLogin.login()
    logging.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ login finish')
    generateArticle = GenerateArticle()
    generateArticle.run()
