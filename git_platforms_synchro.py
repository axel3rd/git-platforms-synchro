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

    git_from = GitClientFactory.create_client(args.from_url, args.from_type)
    git_to = GitClientFactory.create_client(args.to_url, args.to_type)

    logger.debug(git_from.get_repos(args.from_org))

    return 0


if __name__ == '__main__':
    sys.exit(main())
