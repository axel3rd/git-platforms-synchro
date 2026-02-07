#!/usr/bin/python

from sys import argv
from os import environ

if 'username' in argv[1].lower():
    print(environ.get('GIT_USERNAME', ''))
    exit()

if 'password' in argv[1].lower():
    print(environ.get('GIT_PASSWORD', ''))
    exit()

exit(1)
