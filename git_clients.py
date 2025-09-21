from abc import ABC
from github import Github, Auth
from gitea import Gitea, Organization, Repository, NotFoundException

MSG_EMPTY_ORG = 'Organization name cannot be empty.'
MSG_EMPTY_REPO = 'Repository name cannot be empty.'
MSG_CREATE_REPO_DESCRIPTION = 'TODO - Provide a description for this repository.'


class GitClient(ABC):

    def get_url(self) -> str:
        # Should return the base URL of the platform
        pass

    def get_repos(self, org) -> list:
        # Should return a list of repositories names
        pass

    def has_repo(self, org, repo) -> bool:
        # Should return True if the repository exists, False otherwise
        pass

    def get_branches(self, org, repo) -> dict:
        # Should return a dictionary with branch names as keys and commit hashes as values
        pass

    def create_repo(self, org, repo):
        # Should create a repository in the platform
        pass


class GitHubClient(GitClient):

    def __init__(self, url, user, password):
        self.url = url
        self.github = Github(base_url=url)

    def get_url(self) -> str:
        return self.url

    def get_repos(self, org) -> list:
        if org is None or len(org) == 0:
            raise ValueError(MSG_EMPTY_ORG)
        repos = []
        for repo in self.github.get_organization(org).get_repos():
            repos.append(repo.name)
        return repos

    def has_repo(self, org, repo) -> bool:
        if org is None or len(org) == 0:
            raise ValueError(MSG_EMPTY_ORG)
        if repo is None or len(repo) == 0:
            raise ValueError(MSG_EMPTY_REPO)
        return self.github.get_organization(org).get_repo(repo) is not None

    def get_branches(self, org, repo) -> dict:
        if org is None or len(org) == 0:
            raise ValueError(MSG_EMPTY_ORG)
        if repo is None or len(repo) == 0:
            raise ValueError(MSG_EMPTY_REPO)
        branches_commits = {}
        for branch in self.github.get_organization(org).get_repo(repo).get_branches():
            branches_commits[branch.name] = branch.commit.sha
        return branches_commits


class GiteaClient(GitClient):
    def __init__(self, url, user, password):
        self.gitea = Gitea(gitea_url=url, auth=(user, password))

    def get_url(self) -> str:
        return self.gitea.url

    def get_repos(self, org) -> list:
        if org is None or len(org) == 0:
            raise ValueError(MSG_EMPTY_ORG)
        repos = []
        for repo in Organization.request(self.gitea, org).get_repositories():
            repos.append(repo.name)
        return repos

    def has_repo(self, org, repo) -> bool:
        if org is None or len(org) == 0:
            raise ValueError(MSG_EMPTY_ORG)
        if repo is None or len(repo) == 0:
            raise ValueError(MSG_EMPTY_REPO)
        try:
            return Repository.request(self.gitea, org, repo) is not None
        except NotFoundException:
            return False

    def get_branches(self, org, repo) -> dict:
        if org is None or len(org) == 0:
            raise ValueError(MSG_EMPTY_ORG)
        if repo is None or len(repo) == 0:
            raise ValueError(MSG_EMPTY_REPO)
        branches_commits = {}
        for branch in Repository.request(self.gitea, org, repo).get_branches():
            branches_commits[branch.name] = branch.commit["id"]
        return branches_commits

    def create_repo(self, org, repo):
        Organization.request(self.gitea, org).create_repo(
            repoName=repo, description=MSG_CREATE_REPO_DESCRIPTION, autoInit=False)


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
