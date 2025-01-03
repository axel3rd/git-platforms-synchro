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


def test_same_from_to_github(httpserver: HTTPServer):
    expect_request(httpserver, 'github', '/orgs/spring-projects')
    expect_request(httpserver, 'github', '/orgs/spring-projects/repos')
    expect_request(httpserver, 'github',
                   '/repos/spring-projects/spring-petclinic')
    expect_request(httpserver, 'github',
                   '/repos/spring-projects/spring-petclinic/branches')

    testargs = ['prog', '--from-url', httpserver.url_for('/'), '--from-type', 'GitHub',
                '--to-url', httpserver.url_for('/'), '--to-type', 'GitHub', '--to-user', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'spring-projects', '--repos-include', 'spring-petclinic', '--branches-include', 'main,springboot3']
    with unittest.mock.patch.object(sys, 'argv', testargs):
        git_platforms_synchro.main()


def test_same_from_to_gitea(httpserver: HTTPServer):
    expect_request(httpserver, 'gitea', '/api/v1/orgs/MyOrg')
    # Declare empty page two before next first page result, infinite loop otherwise
    httpserver.expect_request(
        '/api/v1/orgs/MyOrg/repos',  query_string='page=2').respond_with_json([])
    expect_request(httpserver, 'gitea', '/api/v1/orgs/MyOrg/repos')
    expect_request(httpserver, 'gitea', '/api/v1/repos/MyOrg/spring-petclinic')
    expect_request(httpserver, 'gitea',
                   '/api/v1/repos/MyOrg/spring-petclinic/branches')

    testargs = ['prog', '--from-url', httpserver.url_for('/'), '--from-type', 'Gitea', '--from-user', 'foo', '--from-password', 'bar',
                '--to-url', httpserver.url_for('/'), '--to-type', 'Gitea', '--to-user', 'foo', '--to-password', 'bar', '--from-org', 'MyOrg', '--to-org', 'MyOrg', '--repos-include', 'spring-petclinic', '--branches-include', 'main,springboot3']
    with unittest.mock.patch.object(sys, 'argv', testargs):
        git_platforms_synchro.main()
