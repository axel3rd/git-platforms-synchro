from github import Github


class GitHubClient:

    def __init__(self, url):
        self.url = url
        self.github = Github(base_url=url)

    def get_repos(self, org):
        if org is None or len(org) == 0:
            raise ValueError('Organization name cannot be empty.')
        repos = []
        for repo in self.github.get_organization(org).get_repos():
            repos.append(repo.name)
        return repos


class GiteaClient:
    def __init__(self, url):
        self.url = url

    def get_repos(self, org):
        raise NotImplementedError('Not implemented yet')


class BitbucketClient:
    def __init__(self, url):
        self.url = url

    def get_repos(self, org):
        raise NotImplementedError('Not implemented yet')


class GitClientFactory:
    @staticmethod
    def create_client(url, type):
        if 'github'.casefold() == type.casefold() or 'github' in url:
            return GitHubClient(url)
        elif 'gitea'.casefold() == type.casefold() or 'gitea' in url:
            return GiteaClient(url)
        elif 'bitbucket'.casefold() == type.casefold() or 'bitbucket' in url:
            return BitbucketClient(url)
        else:
            raise ValueError(
                f'Type "{type}" not supported or not detected from URL "{url}".')
