#!/usr/bin/python

import sys
from sys import argv
from os import environ


def read_input_from_sys_env(param: str) -> int:
    if 'username' in param.lower():
        print(environ.get('GIT_USERNAME', ''))
        return 0

    if 'password' in param.lower():
        print(environ.get('GIT_PASSWORD', ''))
        return 0

    return 1


if __name__ == '__main__':
    sys.exit(read_input_from_sys_env(argv[1]))
