import sys
import shutil
import json
import unittest
import tarfile
import git_platforms_synchro
from pytest_httpserver import HTTPServer
from pytest import LogCaptureFixture


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


def test_same_from_to_github(httpserver: HTTPServer, caplog: LogCaptureFixture):
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

    assert 'Already synchronized, nothing to do.' in caplog.text


def test_same_from_to_gitea(httpserver: HTTPServer, caplog: LogCaptureFixture):
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

    assert 'Already synchronized, nothing to do.' in caplog.text


def test_from_github_to_gitea_create(httpserver: HTTPServer, caplog: LogCaptureFixture):
    # GitHub with spring-projects
    expect_request(httpserver, 'github', '/orgs/spring-projects')
    expect_request(httpserver, 'github', '/orgs/spring-projects/repos')
    expect_request(httpserver, 'github',
                   '/repos/spring-projects/spring-petclinic')
    expect_request(httpserver, 'github',
                   '/repos/spring-projects/spring-petclinic/branches')
    # Gitea with "Empty" org
    expect_request(httpserver, 'gitea', '/api/v1/orgs/MyOrg')
    httpserver.expect_request(
        '/api/v1/orgs/MyOrg/repos', query_string='page=1').respond_with_json([])
    httpserver.expect_request(
        '/api/v1/repos/MyOrg/spring-petclinic').respond_with_data(status=404)
    httpserver.expect_request(
        '/api/v1/orgs/MyOrg/repos', method='POST').respond_with_json(status=201, response_json={'id': 42, 'name': 'spring-petclinic'})

    # httpserver doesn't support KeepAlive, so we need to mock the git clone as already existing directory
    shutil.rmtree(git_platforms_synchro.TMP_REPO_GIT_DIRECTORY,
                  ignore_errors=True, onerror=None)
    # TODO Create a fake git repo bare with one commit

    testargs = ['prog', '--from-url', httpserver.url_for('/'), '--from-type', 'GitHub',
                '--to-url', httpserver.url_for('/'), '--to-type', 'Gitea', '--to-user', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'MyOrg', '--repos-include', 'spring-petclinic', '--branches-include', 'main,springboot3']
    with unittest.mock.patch.object(sys, 'argv', testargs):
        git_platforms_synchro.main()

    assert 'Repository do not exist on "to" plaform, will be created as mirror.' in caplog.text

    # TODO verify repo pushed to Gitea correctly
    assert False
