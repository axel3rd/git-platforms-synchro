import re
import argparse
import logging

logger = logging.getLogger(__name__)


def hide(string: str, after: int = 2) -> str:
    if string is not None and len(string) > after:
        return string[:after] + '*' * (len(string) - after)
    return string


def hide_url(url: str) -> str:
    if url is None:
        return ''
    # Simple regex to hide credentials in URL
    return re.sub(r'//(.*?):*(.*?)@', lambda m: '//***@', url)


def parse():
    parser = argparse.ArgumentParser(
        description='Git Platforms Synchronization')
    parser.add_argument('--from-url', required=True,
                        help='Git "from" platform API URL (Required)')
    parser.add_argument('--from-login',
                        help='Git "from" login or token.')
    parser.add_argument('--from-password',
                        help='Git "from" password.')
    parser.add_argument('--from-org',
                        help='Git "from" organization (or project).', required=True)
    parser.add_argument('--from-type',
                        help='Git "from" type (Bitbucket, Gitea, GitHub, ... ; To use when cannot be detected from URL).', default='')
    parser.add_argument('--from-proxy',
                        help='Git "from" proxy (with credentials if needed).')
    parser.add_argument('--from-disable-ssl-verify',
                        help='Git "from" disable SSL verification.', action='store_true')
    parser.add_argument('--to-url', required=True,
                        help='Git "to" platform API URL (Required)')
    parser.add_argument('--to-login',
                        help='Git "to" login or token (Required).', required=True)
    parser.add_argument('--to-password',
                        help='Git "to" password.')
    parser.add_argument('--to-org',
                        help='Git "to" organization (or project).', required=True)
    parser.add_argument(
        '--to-type', help='Git "to" type (Bitbucket, Gitea, GitHub, ... ; To use when cannot be detected from URL).', default='')
    parser.add_argument('--to-proxy',
                        help='Git "to" proxy (with credentials if needed).')
    parser.add_argument('--to-disable-ssl-verify',
                        help='Git "to" disable SSL verification.', action='store_true')
    parser.add_argument('--to-description-prefix',
                        help='Description prefix for Git "to" repositories creation.', default='')
    parser.add_argument('--repos-include',
                        help='Repositories names patterns to include (comma separated).', default='')
    parser.add_argument('--repos-exclude',
                        help='Repositories names patterns to exclude (comma separated).', default='\\.')
    parser.add_argument('--branches-include',
                        help='Branches names patterns to include (comma separated).', default='')
    parser.add_argument('--branches-exclude',
                        help='Branches names patterns to exclude (comma separated).', default='\\.')
    parser.add_argument('-d', '--dry-run',
                        help='Dry-run : Just analyse which branches should be synchronized, without doning it really.',  action='store_true')
    parser.add_argument(
        '-l', '--log-level', help='Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)', default='INFO')
    args = parser.parse_args()
    return args


def print_args(args: argparse.Namespace):
    logger.info('\n------ Input arguments ------')
    logger.info('Git "from" platform URL     : %s', args.from_url)
    logger.info('Git "from" login or token   : %s', hide(args.from_login))
    logger.info('Git "from" org/project      : %s', args.from_org)
    logger.info('Git "from" type             : %s', args.from_type)
    logger.info('Git "from" proxy            : %s', hide_url(args.from_proxy))
    logger.info('Git "from" disable SSL      : %s',
                args.from_disable_ssl_verify)
    logger.info('Git "to" platform URL       : %s', args.to_url)
    logger.info('Git "to" login or token     : %s', hide(args.to_login))
    logger.info('Git "to" org/project        : %s', args.to_org)
    logger.info('Git "to" type               : %s', args.to_type)
    logger.info('Git "to" proxy              : %s', hide_url(args.to_proxy))
    logger.info('Git "to" disable SSL        : %s', args.to_disable_ssl_verify)
    logger.info('Git "to" description prefix : %s', args.to_description_prefix)
    logger.info('Repositories include        : %s', args.repos_include)
    logger.info('Repositories exclude        : %s', args.repos_exclude)
    logger.info('Branches include            : %s', args.branches_include)
    logger.info('Branches exclude            : %s', args.branches_exclude)
    logger.info('Dry-run                     : %s', args.dry_run)
    logger.info('Log Level                   : %s', args.log_level)


def reduce(items: list, includes: str, excludes: str):
    includes_combined = "(" + ")|(".join(includes.split(',')) + ")"
    excludes_combined = "(" + ")|(".join(excludes.split(',')) + ")"
    new_items = []
    for item in items:
        if re.match(excludes_combined, item) or not re.match(includes_combined, item):
            continue
        new_items.append(item)
    return new_items
