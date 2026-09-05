import logging
from typing import Any

from github import Github
from github.GithubException import GithubException

from utils import PROJECT_ACCESS_TOKEN, setup_colored_logger

setup_colored_logger()


class CleanUpWorkflow:
    def __init__(self, repo_name: str) -> None:
        self.token = PROJECT_ACCESS_TOKEN
        self.repo_name = repo_name
        self.github = Github(self.token)
        self.repo = self.github.get_repo(self.repo_name)

    def run(self) -> None:
        logging.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ workflow cleanup start")
        if self.repo.permissions.admin:
            self.cleanup_workflow_runs()
        else:
            logging.warning("no permissions for repository: %s", self.repo_name)
        logging.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ workflow cleanup finish")

    def cleanup_workflow_runs(self) -> None:
        workflow_runs = self.repo.get_workflow_runs()
        sorted_runs = sorted(
            workflow_runs, key=lambda run: run.created_at, reverse=True
        )

        if len(sorted_runs) > 5:
            for workflow_run in sorted_runs[5:]:
                self.delete_workflow_run(workflow_run)

    @staticmethod
    def delete_workflow_run(workflow_run: Any) -> None:
        try:
            workflow_run.delete()
            logging.info("successfully deleted workflow %s!", workflow_run.id)
        except GithubException:
            logging.exception("failed to delete workflow %s", workflow_run.id)


if __name__ == "__main__":
    repos = ["hgnulb/myblog"]
    for repo in repos:
        try:
            cleanup_workflow = CleanUpWorkflow(repo_name=repo)
            cleanup_workflow.run()
        except GithubException:
            logging.exception("failed to cleanup %s", repo)
