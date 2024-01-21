import sys

from github import Github

from utils import *

logging.basicConfig(level=logging.INFO)
TOKEN = sys.argv[1]


class CleanUpWorkflow:
    def __init__(self):
        self.token = TOKEN

    def run(self):
        logging.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ workflow cleanup start')
        github = Github(self.token)
        headers = {'Accept': 'application/vnd.github.v3', 'Authorization': f'token {self.token}'}
        for repo in github.get_user().get_repos():
            workflow_runs = repo.get_workflow_runs()
            for workflow_run in workflow_runs:
                resp = requests.delete(url=workflow_run.url, headers=headers)
                if resp.status_code == 204:
                    logging.info(f'successfully deleted {workflow_run.id} workflow!')
        logging.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ workflow cleanup finish')


if __name__ == '__main__':
    cleanUpWorkflow = CleanUpWorkflow()
    cleanUpWorkflow.run()
