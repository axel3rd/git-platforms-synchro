[![Build Status](https://github.com/axel3rd/git-platforms-synchro/workflows/Build/badge.svg)](https://github.com/axel3rd/git-platforms-synchro/actions/workflows/build-dev.yml) [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=axel3rd%3Agit-platforms-synchro&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=axel3rd%3Agit-platforms-synchro)

# Git Platforms Synchronization

Synchronize branches of repositories from a Git paltform to another (with rebase, merge unsupported).

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
    --from-url https://api.github.com --from-org spring-projects \
    --to-url http://localhost:3000 --to-type gitea --to-user foo --to-password bar --to-org MyOrg \
    --repos-include spring-petclinic,spring-ai-examples \
    --branches-include "main,spring-ai*"
```

## Options

```
usage: git_platforms_synchro.py [-h] --from-url FROM_URL [--from-user FROM_USER] [--from-password FROM_PASSWORD] --from-org FROM_ORG [--from-type FROM_TYPE] [--from-proxy FROM_PROXY] --to-url TO_URL --to-user TO_USER
                                --to-password TO_PASSWORD --to-org TO_ORG [--to-type TO_TYPE] [--to-proxy TO_PROXY] [--repos-include REPOS_INCLUDE] [--repos-exclude REPOS_EXCLUDE] [--branches-include BRANCHES_INCLUDE]
                                [--branches-exclude BRANCHES_EXCLUDE] [-d] [-l LOG_LEVEL]

Git Platforms Synchronization

options:
  -h, --help            show this help message and exit
  --from-url FROM_URL   Git "from" platform API URL (Required)
  --from-user FROM_USER
                        Git "from" user.
  --from-password FROM_PASSWORD
                        Git "from" password or token.
  --from-org FROM_ORG   Git "from" organization (or project).
  --from-type FROM_TYPE
                        Git "from" type (Bitbucket, Gitea, GitHub, ... ; To use when cannot be detected from URL).
  --from-proxy FROM_PROXY
                        Git "from" proxy (with credentials if needed).
  --to-url TO_URL       Git "to" platform API URL (Required)
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

## Development utilities

To instantiate a Gitea accessible via proxy (login/password= `evil/live`), runnable via `docker compose up`:

```
services:
  # Gitea platform
  my.gitea.local:
    image: docker.io/gitea/gitea:latest-rootless
    restart: always
    volumes:
      - ./data:/var/lib/gitea
      - ./config:/etc/gitea
      - /etc/timezone:/etc/timezone:ro
      - /etc/localtime:/etc/localtime:ro
    ports:
      - "3000:3000"
      - "2222:2222"

  # Proxy server
  proxy:
    image: monokal/tinyproxy
    environment:
      BASIC_AUTH_USER: evil
      BASIC_AUTH_PASSWORD: live
    ports:
      - '8000:8888/tcp'
    command: ANY
```