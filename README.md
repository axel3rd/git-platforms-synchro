# Git Platforms Synchronization

Synchronize (with rebase) branches of repositories from a Git paltform to another.

## Preamble

**Experimental** status.

Currently not implemented:
- Bitbucket
- Proxy support

## Usage

Dependencies installation (once): 

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Execution program:

```
python3 git_platforms_synchro.py \ 
    --from-url https://from.git.com --from-org my-org
    --to-url https://to.git.com --to-user foo --to-password bar --to-org my-org
```

## Options

```
usage: git_platforms_synchro.py [-h] --from-url FROM_URL [--from-user FROM_USER] [--from-password FROM_PASSWORD] --from-org FROM_ORG [--from-type FROM_TYPE] [--from-proxy FROM_PROXY] --to-url TO_URL --to-user TO_USER
                                --to-password TO_PASSWORD --to-org TO_ORG [--to-type TO_TYPE] [--to-proxy TO_PROXY] [--repos-include REPOS_INCLUDE] [--repos-exclude REPOS_EXCLUDE] [--branches-include BRANCHES_INCLUDE]
                                [--branches-exclude BRANCHES_EXCLUDE] [-d] [-l LOG_LEVEL]

Git Platforms Synchronization

options:
  -h, --help            show this help message and exit
  --from-url FROM_URL   Git "from" platform URL (Required)
  --from-user FROM_USER
                        Git "from" user.
  --from-password FROM_PASSWORD
                        Git "from" password or token.
  --from-org FROM_ORG   Git "from" organization (or project).
  --from-type FROM_TYPE
                        Git "from" type (Bitbucket, Gitea, GitHub, ... ; To use when cannot be detected from URL).
  --from-proxy FROM_PROXY
                        Git "from" proxy (with credentials if needed).
  --to-url TO_URL       Git "to" platform URL (Required)
  --to-user TO_USER     Git "to" user (Required).
  --to-password TO_PASSWORD
                        Git "to" password or token (Required).
  --to-org TO_ORG       Git "to" organization (or project).
  --to-type TO_TYPE     Git "to" type (Bitbucket, Gitea, GitHub, ... ; To use when cannot be detected from URL).
  --to-proxy TO_PROXY   Git "to" proxy (with credentials if needed).
  --repos-include REPOS_INCLUDE
                        Repositories names patterns to include (comma separated).
  --repos-exclude REPOS_EXCLUDE
                        Repositories names patterns to exclude (comma separated).
  --branches-include BRANCHES_INCLUDE
                        Branches names patterns to include (comma separated).
  --branches-exclude BRANCHES_EXCLUDE
                        Branches names patterns to exclude (comma separated).
  -d, --dry-run         Dry-run : Just analyse which branches should be synchronized, without doning it really.
  -l LOG_LEVEL, --log-level LOG_LEVEL
                        Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
```                        