from abc import ABC
from github import Github
from gitea import Gitea, Organization, Repository, NotFoundException

MSG_EMPTY_ORG = 'Organization name cannot be empty.'
MSG_EMPTY_REPO = 'Repository name cannot be empty.'
MSG_CREATE_REPO_DESCRIPTION = 'TODO - Provide a description for this repository.'


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

    def get_repo_clone_url(self, org: str, repo: str) -> str:
        # Should return the clone URL of the repository
        pass

    def create_repo(self, org: str, repo: str):
        # Should create a repository in the platform
        pass


class GitHubClient(GitClient):

    def __init__(self, url, login_or_token: str, password: str):
        self.url = url
        self.github = Github(
            base_url=url, login_or_token=login_or_token, password=password)

    def get_url(self) -> str:
        return self.url

    def get_repos(self, org: str) -> list:
        if org is None or len(org) == 0:
            raise ValueError(MSG_EMPTY_ORG)
        repos = []
        for repo in self.github.get_organization(org).get_repos():
            repos.append(repo.name)
        return repos

    def has_repo(self, org: str, repo: str) -> bool:
        if org is None or len(org) == 0:
            raise ValueError(MSG_EMPTY_ORG)
        if repo is None or len(repo) == 0:
            raise ValueError(MSG_EMPTY_REPO)
        return self.github.get_organization(org).get_repo(repo) is not None

    def get_repo_clone_url(self, org: str, repo: str) -> str:
        if org is None or len(org) == 0:
            raise ValueError(MSG_EMPTY_ORG)
        if repo is None or len(repo) == 0:
            raise ValueError(MSG_EMPTY_REPO)
        return self.github.get_organization(org).get_repo(repo).clone_url

    def get_branches(self, org: str, repo: str) -> dict:
        if org is None or len(org) == 0:
            raise ValueError(MSG_EMPTY_ORG)
        if repo is None or len(repo) == 0:
            raise ValueError(MSG_EMPTY_REPO)
        branches_commits = {}
        for branch in self.github.get_organization(org).get_repo(repo).get_branches():
            branches_commits[branch.name] = branch.commit.sha
        return branches_commits

    def create_repo(self, org: str, repo: str, description: str = MSG_CREATE_REPO_DESCRIPTION):
        if org is None or len(org) == 0:
            raise ValueError(MSG_EMPTY_ORG)
        if repo is None or len(repo) == 0:
            raise ValueError(MSG_EMPTY_REPO)
        self.github.get_organization(org).create_repo(
            name=repo, description=description, auto_init=False)


class GiteaClient(GitClient):
    def __init__(self, url, user, password):
        self.gitea = Gitea(gitea_url=url, auth=(user, password))

    def get_url(self) -> str:
        return self.gitea.url

    def get_repos(self, org: str) -> list:
        if org is None or len(org) == 0:
            raise ValueError(MSG_EMPTY_ORG)
        repos = []
        for repo in Organization.request(self.gitea, org).get_repositories():
            repos.append(repo.name)
        return repos

    def has_repo(self, org: str, repo: str) -> bool:
        if org is None or len(org) == 0:
            raise ValueError(MSG_EMPTY_ORG)
        if repo is None or len(repo) == 0:
            raise ValueError(MSG_EMPTY_REPO)
        try:
            return Repository.request(self.gitea, org, repo) is not None
        except NotFoundException:
            return False

    def get_repo_clone_url(self, org: str, repo: str) -> str:
        if org is None or len(org) == 0:
            raise ValueError(MSG_EMPTY_ORG)
        if repo is None or len(repo) == 0:
            raise ValueError(MSG_EMPTY_REPO)
        return Repository.request(self.gitea, org, repo).clone_url

    def get_branches(self, org: str, repo: str) -> dict:
        if org is None or len(org) == 0:
            raise ValueError(MSG_EMPTY_ORG)
        if repo is None or len(repo) == 0:
            raise ValueError(MSG_EMPTY_REPO)
        branches_commits = {}
        for branch in Repository.request(self.gitea, org, repo).get_branches():
            branches_commits[branch.name] = branch.commit["id"]
        return branches_commits

    def create_repo(self, org: str, repo: str, description: str = MSG_CREATE_REPO_DESCRIPTION):
        Organization.request(self.gitea, org).create_repo(
            repoName=repo, description=description, autoInit=False)


class BitbucketClient(GitClient):
    def __init__(self, url, user, password):
        raise NotImplementedError('Not implemented yet')


class GitClientFactory:
    @staticmethod
    def create_client(url, type, user, password):
        if 'github'.casefold() == type.casefold() or 'github' in url:
            return GitHubClient(url, user, password)
        elif 'gitea'.casefold() == type.casefold() or 'gitea' in url:
            return GiteaClient(url, user, password)
        elif 'bitbucket'.casefold() == type.casefold() or 'bitbucket' in url:
            return BitbucketClient(url, user, password)
        else:
            raise ValueError(
                f'Type "{type}" not supported or not detected from URL "{url}".')
