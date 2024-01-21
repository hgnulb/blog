import sys
from tenacity import retry, stop_after_attempt, stop_after_delay, wait_fixed, retry_if_exception_type, retry_if_result
from utils import *

LEETCODE_PASSWORD = sys.argv[1]


def is_login_successful():
    return session.cookies.get('LEETCODE_SESSION') is not None


class LeetCodeLogin:
    def __init__(self):
        self.username = USER_NAME
        self.password = LEETCODE_PASSWORD

    @retry(
        wait=wait_fixed(SLEEP_TIME),
        retry=(retry_if_exception_type(Exception) | retry_if_result(lambda result: result is None)),
        reraise=True,
        stop=(stop_after_attempt(RETRY_COUNT) | stop_after_delay(180))
    )
    def login(self):
        try:
            login_data = {
                'login': self.username,
                'password': self.password
            }
            resp = session.post(SIGN_IN_URL, data=login_data, headers=dict(Referer=SIGN_IN_URL), allow_redirects=False)
            if resp.ok:
                if is_login_successful():
                    logging.info('login successful!')
                    return session.cookies.get('LEETCODE_SESSION')
                else:
                    logging.error('login failed!')
            else:
                logging.error(f'login failed! status code={resp.status_code}')
        except Exception as e:
            logging.error(f'login error! err={e}')
            raise Exception('login failed!')


if __name__ == "__main__":
    leetcode_login = LeetCodeLogin()
    leetcode_login.login()
