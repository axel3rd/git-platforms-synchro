import re
from abc import ABC
try:
    from atlassian import Bitbucket
    BITBUCKET_AVAILABLE = True
except ImportError:
    BITBUCKET_AVAILABLE = False
try:
    from gitea import Gitea, Organization, User, Repository, NotFoundException
    GITEA_AVAILABLE = True
except ImportError:
    GITEA_AVAILABLE = False
try:
    from gitlab import Gitlab, GitlabError
    import requests
    GITLAB_AVAILABLE = True
except ImportError:
    GITLAB_AVAILABLE = False
try:
    from github import Github, Auth, GithubException
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False


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

    def get_tags(self, org: str, repo: str) -> dict:
        # Should return a dictionary with tag names as keys and commit hashes as values
        pass

    def get_repo_description(self, org: str, repo: str) -> str:
        # Should return the description of the repository
        pass

    def get_repo_clone_url(self, org: str, repo: str) -> str:
        # Should return the clone URL of the repository
        pass

    def create_repo(self, org: str, repo: str, description: str = MSG_CREATE_REPO_DESCRIPTION):
        # Should create a repository in the platform
        pass


class BitbucketClient(GitClient):

    def __init__(self, url: str, login_or_token: str = None, password: str = None, ssl_verify: bool = True, proxy: str = None):
        self.bitbucket = Bitbucket(
            url=url, username=login_or_token, password=password, verify_ssl=ssl_verify)
        self.bitbucket._session.proxies = {'http': proxy, 'https': proxy}

    def get_url(self) -> str:
        return self.bitbucket.url

    def get_repos(self, org: str) -> list:
        check_input(org, MSG_EMPTY_ORG)
        repos = []
        for repo in self.bitbucket.repo_all_list(org):
            repos.append(repo['slug'])
        return repos

    def has_repo(self, org: str, repo: str) -> bool:
        check_inputs(org, repo)
        return self.bitbucket.repo_exists(org, repo)

    def get_repo_description(self, org: str, repo: str) -> str:
        check_inputs(org, repo)
        return self.bitbucket.get_repo(org, repo)['description']

    def get_repo_clone_url(self, org: str, repo: str) -> str:
        check_inputs(org, repo)
        for link in self.bitbucket.get_repo(org, repo)['links']['clone']:
            if 'http' == link['name']:
                return link['href']
        raise ValueError('Cannot not found http clone link')

    def get_branches(self, org: str, repo: str) -> dict:
        check_inputs(org, repo)
        branches_commits = {}
        for branch in self.bitbucket.get_branches(org, repo, details=False):
            branches_commits[branch['displayId']] = branch['latestCommit']
        return branches_commits

    def get_tags(self, org: str, repo: str) -> dict:
        check_inputs(org, repo)
        tags_commits = {}
        for tag in self.bitbucket.get_tags(org, repo, limit=0):
            tags_commits[tag['displayId']] = tag['latestCommit']
        return tags_commits

    def create_repo(self, org: str, repo: str, description: str = MSG_CREATE_REPO_DESCRIPTION):
        check_inputs(org, repo)
        self.bitbucket.create_repo(org, repo)
        self.bitbucket.update_repo(org, repo, description=description)


class GiteaClient(GitClient):

    def __init__(self, url: str, login_or_token: str = None, password: str = None, ssl_verify: bool = True, proxy: str = None):
        self.gitea = Gitea(gitea_url=url, auth=(
            login_or_token, password), verify=ssl_verify, proxy=proxy)

    def get_url(self) -> str:
        return self.gitea.url

    def get_repos(self, org: str) -> list:
        check_input(org, MSG_EMPTY_ORG)
        repos = []
        for repo in User.request(self.gitea, org).get_repositories():
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
        # 'Repository.request(self.gitea, org, repo).get_branches()' currently does not support pagination
        results = self.gitea.requests_get_paginated(
            '/repos/%s/%s/branches' % (org, repo))
        for result in results:
            branches_commits[result['name']] = result['commit']['id']
        return branches_commits

    def get_tags(self, org: str, repo: str) -> dict:
        check_inputs(org, repo)
        tags_commits = {}
        results = self.gitea.requests_get_paginated(
            '/repos/%s/%s/tags' % (org, repo))
        for result in results:
            tags_commits[result['name']] = result['id']
        return tags_commits

    def create_repo(self, org: str, repo: str, description: str = MSG_CREATE_REPO_DESCRIPTION):
        check_inputs(org, repo)
        try:
            Organization.request(self.gitea, org).create_repo(
                repoName=repo, description=description, autoInit=False)
        except NotFoundException:
            User.request(self.gitea, org).create_repo(
                repoName=repo, description=description, autoInit=False)


class GitLabClient(GitClient):

    def __init__(self, url, login_or_token: str = None, password: str = None, ssl_verify: bool = True, proxy: str = None):
        self.url = url
        session = None
        private_token = None
        http_username = None
        http_password = None
        if login_or_token.startswith('glpat-') and len(login_or_token) > 55:
            private_token = login_or_token
        elif password is not None:
            http_username = login_or_token
            http_password = password
        if proxy is not None:
            session = requests.Session()
            session.proxies.update({'http': proxy, 'https': proxy})

        self.gitlab = Gitlab(
            self.url,
            http_username=http_username,
            http_password=http_password,
            private_token=private_token,
            ssl_verify=ssl_verify,
            session=session)

    def get_url(self) -> str:
        return self.url

    def get_repos(self, org: str) -> list:
        check_input(org, MSG_EMPTY_ORG)
        repos = []
        for repo in self.gitlab.users.list(username=org)[0].projects.list(all=True, include_subgroups=True):
            repos.append(repo.name)
        return repos

    def has_repo(self, org: str, repo: str) -> bool:
        check_inputs(org, repo)
        try:
            return self.gitlab.projects.get(str(org + '/' + repo)) is not None
        except GitlabError as e:
            if e.response_code == 404:
                return False
            raise e

    def get_repo_description(self, org: str, repo: str) -> str:
        check_inputs(org, repo)
        return self.gitlab.projects.get(str(org + '/' + repo)).description

    def get_repo_clone_url(self, org: str, repo: str) -> str:
        check_inputs(org, repo)
        return self.gitlab.projects.get(str(org + '/' + repo)).http_url_to_repo

    def get_branches(self, org: str, repo: str) -> dict:
        check_inputs(org, repo)
        branches_commits = {}
        for branch in self.gitlab.projects.get(str(org + '/' + repo)).branches.list():
            branches_commits[branch.name] = branch.commit['id']
        return branches_commits

    def get_tags(self, org: str, repo: str) -> dict:
        check_inputs(org, repo)
        tags_commits = {}
        for tag in self.gitlab.projects.get(str(org + '/' + repo)).tags.list():
            tags_commits[tag.name] = tag.commit['id']
        return tags_commits

    def create_repo(self, org: str, repo: str, description: str = MSG_CREATE_REPO_DESCRIPTION):
        check_inputs(org, repo)
        self.gitlab.projects.create({
            'name': repo,
            'description': description,
            'visibility': 'private'
        })


class GitHubClient(GitClient):

    def __init__(self, url, login_or_token: str = None, password: str = None, ssl_verify: bool = True, proxy: str = None):
        if proxy is not None:
            raise NotImplementedError(
                'Proxy not implemented yet for GitHubClient (PyGithub#2426). Please use HTTP_PROXY/HTTPS_PROXY/NO_PROXY environment variables.')
        self.url = url
        auth = None
        if login_or_token is not None:
            if re.match(r'^gh._\w+$', login_or_token):
                auth = Auth.Token(login_or_token)
            elif password is not None:
                auth = Auth.Login(login_or_token, password)
        self.github = Github(base_url=url, auth=auth, verify=ssl_verify)

    def get_url(self) -> str:
        return self.url

    def get_repos(self, org: str) -> list:
        check_input(org, MSG_EMPTY_ORG)
        repos = []
        for repo in self.github.get_user(org).get_repos():
            repos.append(repo.name)
        return repos

    def has_repo(self, org: str, repo: str) -> bool:
        check_inputs(org, repo)
        try:
            return self.github.get_user(org).get_repo(repo) is not None
        except GithubException as e:
            if e.status == 404:
                return False
            raise e

    def get_repo_description(self, org: str, repo: str) -> str:
        check_inputs(org, repo)
        return self.github.get_user(org).get_repo(repo).description

    def get_repo_clone_url(self, org: str, repo: str) -> str:
        check_inputs(org, repo)
        return self.github.get_user(org).get_repo(repo).clone_url

    def get_branches(self, org: str, repo: str) -> dict:
        check_inputs(org, repo)
        branches_commits = {}
        for branch in self.github.get_user(org).get_repo(repo).get_branches():
            branches_commits[branch.name] = branch.commit.sha
        return branches_commits

    def get_tags(self, org: str, repo: str) -> dict:
        check_inputs(org, repo)
        tags_commits = {}
        for tag in self.github.get_user(org).get_repo(repo).get_tags():
            tags_commits[tag.name] = tag.commit.sha
        return tags_commits

    def create_repo(self, org: str, repo: str, description: str = MSG_CREATE_REPO_DESCRIPTION):
        check_inputs(org, repo)
        try:
            self.github.get_organization(org).create_repo(
                name=repo, description=description, auto_init=False)
        except GithubException as e:
            if e.status == 404:
                # Use github.get_user().create_repo() for that case (get_user(xxx) does not have create_repo())
                self.github.get_user().create_repo(
                    name=repo, description=description, auto_init=False)
            else:
                raise e


class GitClientFactory:
    @staticmethod
    def create_client(url, type: str, login_or_token: str = None, password: str = None, ssl_verify: bool = True, proxy: str = None) -> GitClient:
        if BITBUCKET_AVAILABLE and ('bitbucket'.casefold() == type.casefold() or 'bitbucket' in url):
            return BitbucketClient(url, login_or_token, password, ssl_verify, proxy)
        elif GITEA_AVAILABLE and ('gitea'.casefold() == type.casefold() or 'gitea' in url):
            return GiteaClient(url, login_or_token, password, ssl_verify, proxy)
        elif GITHUB_AVAILABLE and ('github'.casefold() == type.casefold() or 'github' in url):
            return GitHubClient(url, login_or_token, password, ssl_verify, proxy)
        elif GITLAB_AVAILABLE and ('gitlab'.casefold() == type.casefold() or 'gitlab' in url):
            return GitLabClient(url, login_or_token, password, ssl_verify, proxy)
        else:
            raise ValueError(
                f'Type "{type}" not supported or not detected from URL "{url}". Or python client dependency not installed - Bitbucket (atlassian-python-api): {BITBUCKET_AVAILABLE}, Gitea (py-gitea): {GITEA_AVAILABLE}, GitLab (python-gitlab): {GITLAB_AVAILABLE}, GitHub (PyGithub): {GITHUB_AVAILABLE}.')
