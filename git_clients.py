from abc import ABC
import re
from github import Github, Auth, GithubException
from gitea import Gitea, Organization, Repository, NotFoundException

MSG_EMPTY_ORG = 'Organization name cannot be empty.'
MSG_EMPTY_REPO = 'Repository name cannot be empty.'
MSG_CREATE_REPO_DESCRIPTION = 'TODO - Provide a description for this repository.'


def check_input(param: str, message: str):
    if param is None or len(param) == 0:
        raise ValueError(message)


def check_inputs(org: str, repo: str = None):
    check_input(org, MSG_EMPTY_ORG)
    check_input(repo, MSG_EMPTY_REPO)


class GitClient(ABC):

    def get_url(self) -> str:
        # Should return the base URL of the platform
        pass

    def get_repos(self, org: str) -> list:
        # Should return a list of repositories names
        pass

    def has_repo(self, org: str, repo: str) -> bool:
        # Should return True if the repository exists, False otherwise
        pass

    def get_branches(self, org: str, repo: str) -> dict:
        # Should return a dictionary with branch names as keys and commit hashes as values
        pass

    def get_repo_description(self, org: str, repo: str) -> str:
        # Should return the description of the repository
        pass

    def get_repo_clone_url(self, org: str, repo: str) -> str:
        # Should return the clone URL of the repository
        pass

    def create_repo(self, org: str, repo: str):
        # Should create a repository in the platform
        pass


class GitHubClient(GitClient):

    def __init__(self, url, login_or_token: str, password: str = None):
        self.url = url
        auth = None
        if login_or_token is not None:
            if re.match(r'^gh._\w+$', login_or_token):
                auth = Auth.Token(login_or_token)
            elif password is not None:
                auth = Auth.Login(login_or_token, password)
        self.github = Github(base_url=url, auth=auth)

    def get_url(self) -> str:
        return self.url

    def get_repos(self, org: str) -> list:
        check_input(org, MSG_EMPTY_ORG)
        repos = []
        for repo in self.github.get_organization(org).get_repos():
            repos.append(repo.name)
        return repos

    def has_repo(self, org: str, repo: str) -> bool:
        check_inputs(org, repo)
        try:
            return self.github.get_organization(org).get_repo(repo) is not None
        except GithubException as e:
            if e.status == 404:
                return False
            raise e

    def get_repo_description(self, org: str, repo: str) -> str:
        check_inputs(org, repo)
        return self.github.get_organization(org).get_repo(repo).description

    def get_repo_clone_url(self, org: str, repo: str) -> str:
        check_inputs(org, repo)
        return self.github.get_organization(org).get_repo(repo).clone_url

    def get_branches(self, org: str, repo: str) -> dict:
        check_inputs(org, repo)
        branches_commits = {}
        for branch in self.github.get_organization(org).get_repo(repo).get_branches():
            branches_commits[branch.name] = branch.commit.sha
        return branches_commits

    def create_repo(self, org: str, repo: str, description: str = MSG_CREATE_REPO_DESCRIPTION):
        check_inputs(org, repo)
        # Warning, does not work for 'user' accounts, only for 'org' accounts
        # Use github.get_user().create_repo() for that case
        self.github.get_organization(org).create_repo(
            name=repo, description=description, auto_init=False)


class GiteaClient(GitClient):

    def __init__(self, url: str, login_or_token: str, password: str = None):
        self.gitea = Gitea(gitea_url=url, auth=(login_or_token, password))

    def get_url(self) -> str:
        return self.gitea.url

    def get_repos(self, org: str) -> list:
        check_input(org, MSG_EMPTY_ORG)
        repos = []
        for repo in Organization.request(self.gitea, org).get_repositories():
            repos.append(repo.name)
        return repos

    def has_repo(self, org: str, repo: str) -> bool:
        check_inputs(org, repo)
        try:
            return Repository.request(self.gitea, org, repo) is not None
        except NotFoundException:
            return False

    def get_repo_description(self, org: str, repo: str) -> str:
        check_inputs(org, repo)
        return Repository.request(self.gitea, org, repo).description

    def get_repo_clone_url(self, org: str, repo: str) -> str:
        check_inputs(org, repo)
        return Repository.request(self.gitea, org, repo).clone_url

    def get_branches(self, org: str, repo: str) -> dict:
        check_inputs(org, repo)
        branches_commits = {}
        for branch in Repository.request(self.gitea, org, repo).get_branches():
            branches_commits[branch.name] = branch.commit["id"]
        return branches_commits

    def create_repo(self, org: str, repo: str, description: str = MSG_CREATE_REPO_DESCRIPTION):
        Organization.request(self.gitea, org).create_repo(
            repoName=repo, description=description, autoInit=False)


class BitbucketClient(GitClient):
    def __init__(self, url: str, login_or_token: str, password: str = None):
        raise NotImplementedError('Not implemented yet')


class GitClientFactory:
    @staticmethod
    def create_client(url, type: str, login_or_token: str, password: str = None) -> GitClient:
        if 'github'.casefold() == type.casefold() or 'github' in url:
            return GitHubClient(url, login_or_token, password)
        elif 'gitea'.casefold() == type.casefold() or 'gitea' in url:
            return GiteaClient(url, login_or_token, password)
        elif 'bitbucket'.casefold() == type.casefold() or 'bitbucket' in url:
            return BitbucketClient(url, login_or_token, password)
        else:
            raise ValueError(
                f'Type "{type}" not supported or not detected from URL "{url}".')
