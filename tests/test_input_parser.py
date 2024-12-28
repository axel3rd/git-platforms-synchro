import sys
import unittest
import input_parser


def test_parsing_required():
    testargs = ['prog', '--from-url', 'https://from.git.com',
                '--to-url', 'https://to.git.com', '--to-user', 'foo', '--to-password', 'bar', '--from-org', 'my-org', '--to-org', 'my-org']
    with unittest.mock.patch.object(sys, 'argv', testargs):
        input_parser.parse()
