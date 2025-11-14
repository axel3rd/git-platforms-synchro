import os
import sys
import shutil
import logging
import input_parser
from git import Repo
from git_clients import GitClientFactory, GitClient

TMP_REPO_GIT_DIRECTORY = 'tmp-git-repo/'
GIT_CONFIG_HTTP_PREFIX = 'http'
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


def git_clone(url: str, mirror: bool = False, disable_ssl_verify: bool = False, proxy: str = None) -> Repo:
    if os.path.exists(TMP_REPO_GIT_DIRECTORY):
        repo_cloned = Repo(TMP_REPO_GIT_DIRECTORY)
        origin_url = repo_cloned.remote('origin').url
        if repo_cloned.bare == mirror and origin_url == url:
            # If already cloned, consider proxy & ssl verify are correct
            logging.debug('Reusing existing cloned repo %s', origin_url)
            return repo_cloned
        else:
            shutil.rmtree(TMP_REPO_GIT_DIRECTORY, ignore_errors=True)
    logging.debug('Cloning repo %s', url)
    options = []
    if disable_ssl_verify:
        options += ['--config http.sslVerify=false']
    if proxy:
        options += [
            '--config http.proxy={} --config https.proxy={}'.format(proxy, proxy)]
    repo_from_cloned = Repo.clone_from(
        url, TMP_REPO_GIT_DIRECTORY, mirror=mirror, allow_unsafe_options=True, multi_options=options)
    return repo_from_cloned


def configure_remote_to(repo: Repo, clone_url_to: str, proxy: str = '', ssl_verify: bool = True):
    try:
        repo.remote(GIT_REMOTE_TO).set_url(clone_url_to)
    except ValueError:
        repo.create_remote(GIT_REMOTE_TO, clone_url_to)
    repo.config_writer().set_value(GIT_CONFIG_HTTP_PREFIX + ' "' + clone_url_to + '"',
                                   'sslVerify', str(ssl_verify).lower()).release()
    repo.config_writer().set_value(GIT_CONFIG_HTTP_PREFIX + ' "' + clone_url_to + '"',
                                   'proxy', proxy if proxy is not None else '').release()
    # For pushing big files
    repo.config_writer().set_value(GIT_CONFIG_HTTP_PREFIX + ' "' + clone_url_to +
                                   '"', 'postBuffer', '524288000').release()


def repo_mirror(create_repo: bool, dry_run: bool, clone_url_from: str,  proxy_from: str, disable_ssl_verify_from: bool, git_to: GitClient,  proxy_to: str, disable_ssl_verify_to: bool, org_to: str, repo: str, description: str = ''):
    if dry_run:
        logger.info(
            '  Dry-run mode, skipping repository creation and mirroring.')
        return
    if create_repo:
        git_to.create_repo(org_to, repo, description)
    clone_url_to = git_to.get_repo_clone_url(org_to, repo)
    repo_from_cloned = git_clone(
        url=clone_url_from, mirror=True, disable_ssl_verify=disable_ssl_verify_from, proxy=proxy_from)
    configure_remote_to(repo_from_cloned, clone_url_to,
                        proxy_to, not disable_ssl_verify_to)
    repo_from_cloned.remote(GIT_REMOTE_TO).push(mirror=True)


def repo_branch_sync(dry_run: bool, clone_url_from: str, proxy_from: str, disable_ssl_verify_from: bool,  git_to: GitClient,  proxy_to: str, disable_ssl_verify_to: bool, org_to: str, repo: str, branch: str):
    if dry_run:
        logger.info('  Dry-run mode, skipping branch synchronization.')
        return
    repo_from_cloned = git_clone(
        url=clone_url_from, disable_ssl_verify=disable_ssl_verify_from, proxy=proxy_from)
    repo_from_cloned.git.checkout(branch)
    clone_url_to = git_to.get_repo_clone_url(org_to, repo)
    configure_remote_to(repo_from_cloned, clone_url_to,
                        proxy_to, not disable_ssl_verify_to)
    repo_from_cloned.remote(GIT_REMOTE_TO).push()


def repo_tags_sync(dry_run: bool, clone_url_from: str, proxy_from: str, disable_ssl_verify_from: bool,  git_to: GitClient,  proxy_to: str, disable_ssl_verify_to: bool, org_to: str, repo: str):
    if dry_run:
        logger.info('  Dry-run mode, skipping tags synchronization.')
        return
    repo_from_cloned = git_clone(
        url=clone_url_from, disable_ssl_verify=disable_ssl_verify_from, proxy=proxy_from)
    clone_url_to = git_to.get_repo_clone_url(org_to, repo)
    configure_remote_to(repo_from_cloned, clone_url_to,
                        proxy_to, not disable_ssl_verify_to)
    repo_from_cloned.remote(GIT_REMOTE_TO).push(tags=True)


def main() -> int:
    args = input_parser.parse()
    log_init(args.log_level)
    logger.info('Starting Git Platforms Synchronization...')
    input_parser.print_args(args)

    git_from = GitClientFactory.create_client(
        args.from_url, args.from_type, args.from_login, args.from_password, not args.from_disable_ssl_verify, args.from_proxy)
    git_to = GitClientFactory.create_client(
        args.to_url, args.to_type, args.to_login, args.to_password, not args.to_disable_ssl_verify, args.to_proxy)

    logger.info('\n------ Processing synchronization ------')
    total_repos_scanned = total_repos_updated = total_branches_scanned = total_branches_updated = 0
    for repo in input_parser.reduce(git_from.get_repos(args.from_org), args.repos_include, args.repos_exclude):
        logger.info('Repository: %s', repo)
        total_repos_scanned += 1
        clone_url_from = git_from.get_repo_clone_url(args.from_org, repo)

        if not git_to.has_repo(args.to_org, repo):
            logger.info(
                '  Repository does not exist on "to" plaform, will be created as mirror.')
            total_repos_updated += 1
            description = git_from.get_repo_description(args.from_org, repo)
            repo_mirror(True, args.dry_run, clone_url_from, args.from_proxy, args.from_disable_ssl_verify,
                        git_to, args.to_proxy, args.to_disable_ssl_verify, args.to_org, repo, args.to_description_prefix + (description if description is not None else ''))
            continue

        branches_commits_from = git_from.get_branches(args.from_org, repo)
        if len(branches_commits_from) == 0:
            logger.info(
                '  Repository has no branches on "from" platform, skipping.')
            continue

        branches_commits_to = git_to.get_branches(args.to_org, repo)
        if len(branches_commits_to) == 0:
            logger.info(
                '  Repository has no branches on "to" platform, will be mirrored.')
            total_repos_updated += 1
            repo_mirror(False, args.dry_run, clone_url_from, args.from_proxy, args.from_disable_ssl_verify,
                        git_to, args.to_proxy, args.to_disable_ssl_verify, args.to_org, repo)
            continue

        branches_updated = 0
        for branch in input_parser.reduce(branches_commits_from.keys(), args.branches_include, args.branches_exclude):
            total_branches_scanned += 1
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
            repo_branch_sync(args.dry_run, clone_url_from, args.from_proxy, args.from_disable_ssl_verify,
                             git_to, args.to_proxy, args.to_disable_ssl_verify, args.to_org, repo, branch)

        tags_commits_from = git_from.get_tags(args.from_org, repo)
        tags_commits_to = git_to.get_tags(args.to_org, repo)
        if branches_updated == 0 and len(tags_commits_from) != len(tags_commits_to):
            logger.info('  All branches already synchronized, do tags only...')
            repo_tags_sync(
                args.dry_run, clone_url_from, args.from_proxy, args.from_disable_ssl_verify, git_to, args.to_proxy, args.to_disable_ssl_verify, args.to_org, repo)

        if branches_updated > 0 or len(tags_commits_from) > len(tags_commits_to):
            total_repos_updated += 1
            total_branches_updated += branches_updated

    logger.info('\nGit Platforms Synchronization finished sucessfully. Repos updated: {}/{}. Branches updated: {}/{}.'.format(
        total_repos_updated, total_repos_scanned, total_branches_updated, total_branches_scanned))
    return 0


if __name__ == '__main__':
    sys.exit(main())
