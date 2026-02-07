import os
import sys
import logging
import modules.input_parser as input_parser
from git import Repo
from modules.git_clients import GitClientFactory, GitClient
from modules.utils import TMP_REPO_GIT_DIRECTORY, delete_temporary_repo_git_directory

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


def set_git_credentials(username: str, password: str):
    if not username and not password:
        os.environ.pop('GIT_ASKPASS')
        os.environ.pop('GIT_USERNAME')
        os.environ.pop('GIT_PASSWORD')
        return

    working_dir = os.path.dirname(os.path.realpath(__file__))

    os.environ['GIT_ASKPASS'] = os.path.join(working_dir, 'modules', 'git_askpass.py')
    if username:
        os.environ['GIT_USERNAME'] = username
    if password:
        os.environ['GIT_PASSWORD'] = password


def git_clone(url: str, mirror: bool = False, disable_ssl_verify: bool = False, proxy: str = None) -> Repo:
    if os.path.exists(TMP_REPO_GIT_DIRECTORY):
        repo_cloned = Repo(TMP_REPO_GIT_DIRECTORY)
        origin_url = repo_cloned.remote('origin').url
        if repo_cloned.bare == mirror and origin_url == url:
            # If already cloned, consider proxy & ssl verify are correct
            logging.debug('Reusing existing cloned repo %s', origin_url)
            return repo_cloned
        else:
            delete_temporary_repo_git_directory()
    logging.debug('Cloning repo %s', url)
    options = []
    if disable_ssl_verify:
        options += ['--config http.sslVerify=false']
    if proxy:
        options += ['--config http.proxy={} --config https.proxy={}'.format(proxy, proxy)]
    repo_from_cloned = Repo.clone_from(url, TMP_REPO_GIT_DIRECTORY, mirror=mirror, allow_unsafe_options=True, multi_options=options)
    return repo_from_cloned


def configure_remote_to(repo: Repo, clone_url_to: str, proxy: str = '', ssl_verify: bool = True):
    try:
        repo.remote(GIT_REMOTE_TO).set_url(clone_url_to)
    except ValueError:
        repo.create_remote(GIT_REMOTE_TO, clone_url_to)
    repo.config_writer().set_value(GIT_CONFIG_HTTP_PREFIX + ' "' + clone_url_to + '"', 'sslVerify', str(ssl_verify).lower()).release()
    repo.config_writer().set_value(GIT_CONFIG_HTTP_PREFIX + ' "' + clone_url_to + '"', 'proxy', proxy if proxy is not None else '').release()
    # For pushing big files
    repo.config_writer().set_value(GIT_CONFIG_HTTP_PREFIX + ' "' + clone_url_to + '"', 'postBuffer', '524288000').release()


def repo_mirror(create_repo: bool, dry_run: bool, clone_url_from: str, login_from: str, password_from: str, proxy_from: str, disable_ssl_verify_from: bool,
                git_to: GitClient, proxy_to: str, disable_ssl_verify_to: bool, org_to: str, repo: str, description: str = ''):
    if dry_run:
        logger.info('  Dry-run mode, skipping repository creation and mirroring.')
        return
    if create_repo:
        git_to.create_repo(org_to, repo, description)
    clone_url_to = git_to.get_repo_clone_url(org_to, repo)
    set_git_credentials(login_from, password_from)
    repo_from_cloned = git_clone(url=clone_url_from, mirror=True, disable_ssl_verify=disable_ssl_verify_from, proxy=proxy_from)
    configure_remote_to(repo_from_cloned, clone_url_to, proxy_to, not disable_ssl_verify_to)
    set_git_credentials(git_to.get_login_or_token(), git_to.get_password())
    repo_from_cloned.remote(GIT_REMOTE_TO).push(mirror=True).raise_if_error()


def repo_tags_sync(args, clone_url_from: str, git_from: GitClient, git_to: GitClient, repo: str, branches_updated: int) -> bool:
    if args.dry_run:
        logger.info('  Dry-run mode, skipping tags synchronization.')
        return False

    tags_commits_from = git_from.get_tags(args.from_org, repo)
    tags_commits_to = git_to.get_tags(args.to_org, repo)
    if branches_updated > 0 or len(tags_commits_from) == len(tags_commits_to):
        return False

    logger.info('  All branches already synchronized, do tags only...')
    set_git_credentials(git_from.get_login_or_token(), git_from.get_password())
    repo_from_cloned = git_clone(url=clone_url_from, disable_ssl_verify=args.from_disable_ssl_verify, proxy=args.from_proxy)
    clone_url_to = git_to.get_repo_clone_url(args.to_org, repo)
    configure_remote_to(repo_from_cloned, clone_url_to, args.to_proxy, not args.to_disable_ssl_verify)
    set_git_credentials(git_to.get_login_or_token(), git_to.get_password())
    repo_from_cloned.remote(GIT_REMOTE_TO).push(tags=True).raise_if_error()
    return True


def repo_branch_sync(dry_run: bool, clone_url_from: str, login_from: str, password_from: str, proxy_from: str, disable_ssl_verify_from: bool,
                     git_to: GitClient, proxy_to: str, disable_ssl_verify_to: bool, org_to: str, repo: str, branch: str):
    if dry_run:
        logger.info('    Dry-run mode, skipping branch synchronization.')
        return
    set_git_credentials(login_from, password_from)
    repo_from_cloned = git_clone(url=clone_url_from, disable_ssl_verify=disable_ssl_verify_from, proxy=proxy_from)
    repo_from_cloned.git.checkout(branch)
    clone_url_to = git_to.get_repo_clone_url(org_to, repo)
    configure_remote_to(repo_from_cloned, clone_url_to, proxy_to, not disable_ssl_verify_to)
    set_git_credentials(git_to.get_login_or_token(), git_to.get_password())
    repo_from_cloned.remote(GIT_REMOTE_TO).push().raise_if_error()


def repo_branches_sync(args, branches_commits_from: dict, branches_commits_to: dict,
                       clone_url_from: str, repo: str, git_to: GitClient) -> tuple[int, int]:
    """
    Main branches process sync

    Returns:
        int: Number of branches scanned
        int: Numner of branches updated
    """
    branches_scanned = branches_updated = 0
    for branch in input_parser.reduce(branches_commits_from.keys(), args.branches_include, args.branches_exclude):
        branches_scanned += 1
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
        repo_branch_sync(args.dry_run, clone_url_from, args.from_login, args.from_password, args.from_proxy, args.from_disable_ssl_verify,
                         git_to, args.to_proxy, args.to_disable_ssl_verify, args.to_org, repo, branch)
    return branches_scanned, branches_updated


def main() -> int:
    delete_temporary_repo_git_directory()
    args = input_parser.parse()
    log_init(args.log_level)
    logger.info('Starting Git Platforms Synchronization...')
    input_parser.print_args(args)

    git_from = GitClientFactory.create_client(
        args.from_url,
        args.from_type,
        args.from_login,
        args.from_password,
        not args.from_disable_ssl_verify,
        args.from_proxy)
    git_to = GitClientFactory.create_client(args.to_url, args.to_type, args.to_login, args.to_password, not args.to_disable_ssl_verify, args.to_proxy)

    logger.info('\n------ Processing synchronization ------')
    total_repos_scanned = total_repos_updated = total_branches_scanned = total_branches_updated = 0

    # Loop on repositories to update depending includes/excludes
    for repo in input_parser.reduce(git_from.get_repos(args.from_org), args.repos_include, args.repos_exclude):
        logger.info('Repository: %s', repo)
        total_repos_scanned += 1
        clone_url_from = git_from.get_repo_clone_url(args.from_org, repo)

        # New repo to create and mirror
        if not git_to.has_repo(args.to_org, repo):
            logger.info('  Repository does not exist on "to" plaform, create as mirror...')
            total_repos_updated += 1
            description = git_from.get_repo_description(args.from_org, repo)
            repo_mirror(True, args.dry_run, clone_url_from, args.from_login, args.from_password, args.from_proxy, args.from_disable_ssl_verify,
                        git_to, args.to_proxy, args.to_disable_ssl_verify, args.to_org, repo, args.to_description_prefix + (description if description is not None else ''))
            continue

        # Branches on "from", skip if no commits
        branches_commits_from = git_from.get_branches(args.from_org, repo)
        if len(branches_commits_from) == 0:
            logger.info('  Repository has no branches on "from" platform, skipping.')
            continue

        # Branches on "to", mirror repo if empty
        branches_commits_to = git_to.get_branches(args.to_org, repo)
        if len(branches_commits_to) == 0:
            logger.info('  Repository has no branches on "to" platform, synchronize as mirror...')
            total_repos_updated += 1
            repo_mirror(
                False,
                args.dry_run,
                clone_url_from,
                args.from_login,
                args.from_password,
                args.from_proxy,
                args.from_disable_ssl_verify,
                git_to,
                args.to_proxy,
                args.to_disable_ssl_verify,
                args.to_org,
                repo)
            continue

        # Sync branches
        branches_scanned, branches_updated = repo_branches_sync(args, branches_commits_from, branches_commits_to, clone_url_from, repo, git_to)
        total_branches_scanned += branches_scanned

        # Sync tags if no branches updated and needed (nbr tags diff between "from" and "to")
        tag_updated = repo_tags_sync(args, clone_url_from, git_from, git_to, repo, branches_updated)

        # Items updated calculation
        if branches_updated > 0 or tag_updated:
            total_repos_updated += 1
            total_branches_updated += branches_updated

    delete_temporary_repo_git_directory()
    logger.info('\nGit Platforms Synchronization finished sucessfully. Repos updated: {}/{}. Branches updated: {}/{}.'.format(total_repos_updated,
                total_repos_scanned, total_branches_updated, total_branches_scanned))
    return 0


if __name__ == '__main__':
    sys.exit(main())
