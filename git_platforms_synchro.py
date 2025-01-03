import sys
import logging
import input_parser
from git_clients import GitClientFactory

logger = logging.getLogger(__name__)


def log_init(level: str):
    logging.basicConfig(stream=sys.stdout,
                        format='%(message)s', level=level)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)


def main() -> int:
    args = input_parser.parse()
    log_init(args.log_level)
    logger.info('Starting Git Platforms Synchronization...')
    input_parser.print_args(args)

    git_from = GitClientFactory.create_client(
        args.from_url, args.from_type, args.from_user, args.from_password)
    git_to = GitClientFactory.create_client(
        args.to_url, args.to_type, args.to_user, args.to_password)

    logger.info('\n------ Processing synchronization ------')
    for repo in input_parser.reduce(git_from.get_repos(args.from_org), args.repos_include, args.repos_exclude):
        logger.info('Repository: %s', repo)
        if not git_to.has_repo(args.to_org, repo):
            logger.info(
                '  Repository do not exist of "to" plaform, should be created as mirror.')
        branches_commits_from = git_from.get_branches(args.from_org, repo)
        branches_commits_to = git_to.get_branches(args.from_org, repo)
        # logger.debug('  Branches/commit: %s', branches_commits_from)
        for branch in input_parser.reduce(branches_commits_from.keys(), args.branches_include, args.branches_exclude):
            logger.info('  Branch: %s', branch)
            commit_from = branches_commits_from.get(branch, None)
            logger.info('    Commit From: %s', commit_from)
            commit_to = branches_commits_to.get(branch, None)
            logger.info('    Commit To  : %s', commit_to)
            if commit_from == commit_to:
                logger.info('    Already synchronized, nothing to do.')

        # TODO: Manage tags !!!

    logger.info('\nGit Platforms Synchronization finished sucessfully.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
