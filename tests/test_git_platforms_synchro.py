import sys
import json
import unittest
import git_platforms_synchro
from pytest_httpserver import HTTPServer

from github import Github


def load_json(file, url_to_mock, url_replacement):
    with open(file) as f:
        return json.loads(f.read().replace(url_to_mock, url_replacement))


def expect_request(httpserver, type, uri):
    with open('tests/http_mocks/' + type + uri + '.json') as f:
        content = f.read()
    if type == 'github':
        content = content.replace(
            'https://api.github.com/', httpserver.url_for('/'))
    httpserver.expect_request(uri).respond_with_json(json.loads(content))


def test_git_type_undefined(httpserver: HTTPServer):
    testargs = ['prog', '--from-url', httpserver.url_for('/'), '--to-url', httpserver.url_for(
        '/'), '--to-user', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'new-org']
    try:
        with unittest.mock.patch.object(sys, 'argv', testargs):
            git_platforms_synchro.main()
            # Should have raised an error
            assert False
    except ValueError as e:
        assert str(e) == 'Type "" not supported or not detected from URL "' + \
            httpserver.url_for('/') + '".'


def test_minimal(httpserver: HTTPServer):
    expect_request(httpserver, 'github', '/orgs/spring-projects')
    expect_request(httpserver, 'github', '/orgs/spring-projects/repos')

    testargs = ['prog', '--from-url', httpserver.url_for('/'), '--from-type', 'GitHub',
                '--to-url', httpserver.url_for('/'), '--to-type', 'Gitea', '--to-user', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'new-org']
    with unittest.mock.patch.object(sys, 'argv', testargs):
        git_platforms_synchro.main()
