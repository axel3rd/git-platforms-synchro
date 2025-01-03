from github import Github, Auth
from gitea import Gitea, Organization, Repository

MSG_EMPTY_ORG = 'Organization name cannot be empty.'
MSG_EMPTY_REPO = 'Repository name cannot be empty.'


class GitHubClient:

    def __init__(self, url, user, password):
        self.github = Github(
            base_url=url)

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


class GiteaClient:
    def __init__(self, url, user, password):
        self.gitea = Gitea(gitea_url=url, auth=(user, password))

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
        return Repository.request(self.gitea, org, repo) is not None

    def get_branches(self, org, repo) -> dict:
        if org is None or len(org) == 0:
            raise ValueError(MSG_EMPTY_ORG)
        if repo is None or len(repo) == 0:
            raise ValueError(MSG_EMPTY_REPO)
        branches_commits = {}
        for branch in Repository.request(self.gitea, org, repo).get_branches():
            branches_commits[branch.name] = branch.commit["id"]
        return branches_commits


class BitbucketClient:
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
