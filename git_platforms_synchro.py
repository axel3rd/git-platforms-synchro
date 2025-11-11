import os
import sys
import shutil
import logging
import input_parser
from git import Repo
from git_clients import GitClientFactory, GitClient

TMP_REPO_GIT_DIRECTORY = 'tmp-git-repo/'
GIT_REMOTE_TO = 'sync-to'

logger = logging.getLogger(__name__)


def log_init(level: str):
    logging.basicConfig(stream=sys.stdout,
                        format='%(message)s', level=level)
    if not any(level in s for s in ['TRACE', 'DEBUG']):
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        logging.getLogger("gitea").setLevel(logging.WARNING)


def git_clone(url: str, mirror: bool = False) -> Repo:
    if os.path.exists(TMP_REPO_GIT_DIRECTORY):
        repo_cloned = Repo(TMP_REPO_GIT_DIRECTORY)
        origin_url = repo_cloned.config_reader(
        ).get_value('remote "origin"', 'url')
        if repo_cloned.bare == mirror and origin_url == url:
            logging.debug('Reusing existing cloned repo %s', origin_url)
            return repo_cloned
        else:
            shutil.rmtree(TMP_REPO_GIT_DIRECTORY, ignore_errors=True)
    logging.debug('Cloning repo %s', url)
    repo_from_cloned = Repo.clone_from(
        url, TMP_REPO_GIT_DIRECTORY, mirror=mirror)
    return repo_from_cloned


def configure_remote_to(repo: Repo, clone_url_to: str):
    try:
        repo.remote(GIT_REMOTE_TO).set_url(clone_url_to)
    except ValueError:
        repo.create_remote(GIT_REMOTE_TO, clone_url_to)


def repo_mirror(dry_run: bool, clone_url_from: str, git_to: GitClient, org_to: str, repo: str, description: str = ''):
    if dry_run:
        logger.info(
            '  Dry-run mode, skipping repository creation and mirroring.')
        return
    git_to.create_repo(org_to, repo, description)
    clone_url_to = git_to.get_repo_clone_url(org_to, repo)
    repo_from_cloned = git_clone(clone_url_from, mirror=True)
    configure_remote_to(repo_from_cloned, clone_url_to)
    repo_from_cloned.remote(GIT_REMOTE_TO).push(mirror=True)


def repo_branch_sync(dry_run: bool, clone_url_from: str, git_to: GitClient, org_to: str, repo: str, branch: str):
    if dry_run:
        logger.info('  Dry-run mode, skipping branch synchronization.')
        return
    repo_from_cloned = git_clone(clone_url_from)
    repo_from_cloned.git.checkout(branch)
    clone_url_to = git_to.get_repo_clone_url(org_to, repo)
    configure_remote_to(repo_from_cloned, clone_url_to)
    repo_from_cloned.remote(GIT_REMOTE_TO).push()


def repo_tags_sync(dry_run: bool, clone_url_from: str, git_to: GitClient, org_to: str, repo: str):
    if dry_run:
        logger.info('  Dry-run mode, skipping tags synchronization.')
        return
    repo_from_cloned = git_clone(clone_url_from)
    clone_url_to = git_to.get_repo_clone_url(org_to, repo)
    configure_remote_to(repo_from_cloned, clone_url_to)
    repo_from_cloned.remote(GIT_REMOTE_TO).push(tags=True)


def main() -> int:
    args = input_parser.parse()
    log_init(args.log_level)
    logger.info('Starting Git Platforms Synchronization...')
    input_parser.print_args(args)

    git_from = GitClientFactory.create_client(
        args.from_url, args.from_type, args.from_login, args.from_password)
    git_to = GitClientFactory.create_client(
        args.to_url, args.to_type, args.to_login, args.to_password)

    logger.info('\n------ Processing synchronization ------')
    for repo in input_parser.reduce(git_from.get_repos(args.from_org), args.repos_include, args.repos_exclude):
        logger.info('Repository: %s', repo)
        clone_url_from = git_from.get_repo_clone_url(args.from_org, repo)
        if not git_to.has_repo(args.to_org, repo):
            logger.info(
                '  Repository does not exist on "to" plaform, will be created as mirror.')
            description = git_from.get_repo_description(args.from_org, repo)
            repo_mirror(args.dry_run, clone_url_from,
                        git_to, args.to_org, repo, description)
            continue
        branches_commits_from = git_from.get_branches(args.from_org, repo)
        branches_commits_to = git_to.get_branches(args.to_org, repo)
        branches_updated = 0
        for branch in input_parser.reduce(branches_commits_from.keys(), args.branches_include, args.branches_exclude):
            logger.info('  Branch: %s', branch)
            commit_from = branches_commits_from.get(branch, None)
            logger.info('    Commit From: %s', commit_from)
            commit_to = branches_commits_to.get(branch, None)
            logger.info('    Commit To  : %s', commit_to)
            if commit_from == commit_to:
                logger.info('    Already synchronized.')
                continue
            logger.info('    Synchronize branch...')
            branches_updated += 1
            repo_branch_sync(args.dry_run, clone_url_from,
                             git_to, args.to_org, repo, branch)
        if branches_updated == 0:
            logger.info('  All branches already synchronized, do tags only...')
            # TODO : Check tags via API, should be sync if number of tags differ
            repo_tags_sync(
                args.dry_run, clone_url_from, git_to, args.to_org, repo)

    logger.info('\nGit Platforms Synchronization finished sucessfully.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
