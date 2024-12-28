import argparse
import logging

logger = logging.getLogger(__name__)


def parse():
    parser = argparse.ArgumentParser(
        description='Git Platforms Synchronization')
    parser.add_argument('--from-url', required=True,
                        help='Git "from" platform URL (Required)')
    parser.add_argument('--from-user',
                        help='Git "from" user.')
    parser.add_argument('--from-password',
                        help='Git "from" password or token.')
    parser.add_argument('--from-org',
                        help='Git "from" organization (or project).', required=True)
    parser.add_argument('--from-type',
                        help='Git "from" type (Bitbucket, Gitea, GitHub, ... ; To use when cannot be detected from URL).', default='')
    parser.add_argument('--from-proxy',
                        help='Git "from" proxy (with credentials if needed).')
    parser.add_argument('--to-url', required=True,
                        help='Git "to" platform URL (Required)')
    parser.add_argument('--to-user',
                        help='Git "to" user (Required).', required=True)
    parser.add_argument('--to-password',
                        help='Git "to" password or token (Required).', required=True)
    parser.add_argument('--to-org',
                        help='Git "to" organization (or project).', required=True)
    parser.add_argument(
        '--to-type', help='Git "to" type (Bitbucket, Gitea, GitHub, ... ; To use when cannot be detected from URL).', default='')
    parser.add_argument('--to-proxy',
                        help='Git "to" proxy (with credentials if needed).')
    parser.add_argument('--repos-include',
                        help='Repositories names patterns to include (comma separated).')
    parser.add_argument('--repos-exclude',
                        help='Repositories names patterns to exclude (comma separated).', default='\\.')
    parser.add_argument('--branches-include',
                        help='Branches names patterns to include (comma separated).')
    parser.add_argument('--branches-exclude',
                        help='Branches names patterns to exclude (comma separated).', default='\\.')
    parser.add_argument('-d', '--dry-run',
                        help='Dry-run : Just analyse which branches should be synchronized, without doning it really.', default=False)
    parser.add_argument(
        '-l', '--log-level', help='Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)', default='INFO')
    args = parser.parse_args()
    return args


def print_args(args):
    logger.info('\n------ Input arguments ------')
    logger.info('Git "from" platform URL    : %s', args.from_url)
    logger.info('Git "from" user            : %s', args.from_user)
    logger.info('Git "from" org/project     : %s', args.from_org)
    logger.info('Git "from" type            : %s', args.from_type)
    logger.info('Git "from" proxy (defined) : %s',
                args.from_proxy and len(args.from_proxy) > 0)
    logger.info('Git "to" platform URL      : %s', args.to_url)
    logger.info('Git "to" user              : %s', args.to_user)
    logger.info('Git "to" org/project       : %s', args.to_org)
    logger.info('Git "to" type              : %s', args.to_type)
    logger.info('Git "to" proxy (defined)   : %s',
                args.to_proxy and len(args.to_proxy) > 0)
    logger.info('Repositories include       : %s', args.repos_include)
    logger.info('Repositories exclude       : %s', args.repos_exclude)
    logger.info('Branches include           : %s', args.branches_include)
    logger.info('Branches exclude           : %s', args.branches_exclude)
    logger.info('Dry-run                    : %s', args.dry_run)
    logger.info('Log Level                  : %s', args.log_level)
