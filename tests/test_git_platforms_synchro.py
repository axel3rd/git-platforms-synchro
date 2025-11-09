import sys
import shutil
import json
import tarfile
import pytest_httpserver
import git_platforms_synchro
from git import GitCommandError
from unittest.mock import patch
from pytest_httpserver import HTTPServer
from pytest import LogCaptureFixture, fail


def get_url_root(httpserver: HTTPServer) -> str:
    return httpserver.url_for('/').rstrip('/')


def load_json(file: str, url_to_mock: str, url_replacement: str):
    with open(file) as f:
        return json.loads(f.read().replace(url_to_mock, url_replacement))


def expect_request(httpserver: HTTPServer, type: str, uri: str, str_to_replace: str = None, str_replacement: str = None):
    with open('tests/http_mocks/' + type + uri + '.json') as f:
        content = f.read()
    if type == 'github':
        content = content.replace(
            'https://api.github.com/', httpserver.url_for('/'))
    if str_to_replace and str_replacement:
        content = content.replace(str_to_replace, str_replacement)
    httpserver.expect_request(uri).respond_with_json(json.loads(content))


def test_git_type_undefined(httpserver: HTTPServer):
    testargs = ['prog', '--from-url', httpserver.url_for('/'), '--to-url', httpserver.url_for(
        '/'), '--to-user', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'new-org']
    try:
        with patch.object(sys, 'argv', testargs):
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

    testargs = ['prog', '--dry-run', '--from-url', httpserver.url_for('/'), '--from-type', 'GitHub',
                '--to-url', httpserver.url_for('/'), '--to-type', 'GitHub', '--to-user', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'spring-projects', '--repos-include', 'spring-petclinic', '--branches-include', 'main,springboot3']
    with patch.object(sys, 'argv', testargs):
        git_platforms_synchro.main()

    assert 'Already synchronized.' in caplog.text
    assert 'All branches already synchronized, do tags only...' in caplog.text


def test_same_from_to_gitea(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'gitea', '/api/v1/orgs/MyOrg')
    # Declare empty page two before next first page result, infinite loop otherwise
    httpserver.expect_request(
        '/api/v1/orgs/MyOrg/repos',  query_string='page=2').respond_with_json([])
    expect_request(httpserver, 'gitea', '/api/v1/orgs/MyOrg/repos')
    expect_request(httpserver, 'gitea', '/api/v1/repos/MyOrg/spring-petclinic')
    expect_request(httpserver, 'gitea',
                   '/api/v1/repos/MyOrg/spring-petclinic/branches')

    testargs = ['prog', '--dry-run', '--from-url', httpserver.url_for('/'), '--from-type', 'Gitea', '--from-user', 'foo', '--from-password', 'bar',
                '--to-url', httpserver.url_for('/'), '--to-type', 'Gitea', '--to-user', 'foo', '--to-password', 'bar', '--from-org', 'MyOrg', '--to-org', 'MyOrg', '--repos-include', 'spring-petclinic', '--branches-include', 'main,springboot3']
    with patch.object(sys, 'argv', testargs):
        git_platforms_synchro.main()

    assert 'Already synchronized.' in caplog.text
    assert 'All branches already synchronized, do tags only...' in caplog.text


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
    httpserver.expect_oneshot_request(
        '/api/v1/repos/MyOrg/spring-petclinic').respond_with_data(status=404)
    httpserver.expect_request(
        '/api/v1/orgs/MyOrg/repos', method='POST').respond_with_json(status=201, response_json={'id': 42, 'name': 'spring-petclinic'})
    # Newly created repo at second call
    expect_request(httpserver, 'gitea', '/api/v1/repos/MyOrg/spring-petclinic',
                   'http://localhost:3000', get_url_root(httpserver))

    # httpserver doesn't support KeepAlive, so we need to mock the git clone as already existing bare directory (reuse mechanism) and mock the git push failure
    shutil.rmtree(git_platforms_synchro.TMP_REPO_GIT_DIRECTORY,
                  ignore_errors=True)
    with tarfile.open('tests/resources/spring-petclinic.git.bare.tgz', 'r:gz') as tar:
        tar.extractall(path=git_platforms_synchro.TMP_REPO_GIT_DIRECTORY)
    httpserver.expect_request(
        '/MyOrg/spring-petclinic.git/info/refs', query_string='service=git-receive-pack', method='GET').respond_with_data(status=542)

    testargs = ['prog', '--from-url', get_url_root(httpserver), '--from-type', 'GitHub',
                '--to-url', get_url_root(httpserver), '--to-type', 'Gitea', '--to-user', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'MyOrg', '--repos-include', 'spring-petclinic', '--branches-include', 'main,springboot3']
    with patch.object(sys, 'argv', testargs):
        try:
            git_platforms_synchro.main()
            fail('Expected GitCommandError')
        except GitCommandError:
            assert 'Repository does not exist on "to" plaform, will be created as mirror.' in caplog.text
            assert 'Reusing existing cloned repo https://github.com/spring-projects/spring-petclinic.git' in caplog.text
            assert 'The requested URL returned error: 542' in caplog.text


def test_from_github_to_gitea_sync(httpserver: HTTPServer, caplog: LogCaptureFixture):
    # httpserver doesn't support KeepAlive, so we need to mock the git clone as already existing bare directory (reuse mechanism) and mock the git push failure
    shutil.rmtree(git_platforms_synchro.TMP_REPO_GIT_DIRECTORY,
                  ignore_errors=True)
    with tarfile.open('tests/resources/spring-petclinic.git.tgz', 'r:gz') as tar:
        tar.extractall(
            path=git_platforms_synchro.TMP_REPO_GIT_DIRECTORY, filter='tar')
    httpserver.expect_request(
        '/MyOrg/spring-petclinic.git/info/refs', query_string='service=git-receive-pack', method='GET').respond_with_data(status=542)

    # GitHub with spring-projects
    expect_request(httpserver, 'github', '/orgs/spring-projects')
    expect_request(httpserver, 'github', '/orgs/spring-projects/repos')
    expect_request(httpserver, 'github',
                   '/repos/spring-projects/spring-petclinic')
    expect_request(httpserver, 'github',
                   '/repos/spring-projects/spring-petclinic/branches')

    # Gitea with same repo
    expect_request(httpserver, 'gitea', '/api/v1/orgs/MyOrg')
    # Declare empty page two before next first page result, infinite loop otherwise
    httpserver.expect_request(
        '/api/v1/orgs/MyOrg/repos',  query_string='page=2').respond_with_json([])
    expect_request(httpserver, 'gitea', '/api/v1/orgs/MyOrg/repos')
    expect_request(httpserver, 'gitea', '/api/v1/repos/MyOrg/spring-petclinic',
                   'http://localhost:3000', get_url_root(httpserver))
    expect_request(httpserver, 'gitea',
                   '/api/v1/repos/MyOrg/spring-petclinic/branches', '6148ddd9671ccab86a3f0ae2dfa77d833b713ee8', 'bbbbddd9671ccab86a3f0ae2dfa77d833b713ee8')

    testargs = ['prog', '--from-url', get_url_root(httpserver), '--from-type', 'GitHub', '--from-user', 'foo', '--from-password', 'bar',
                '--to-url', get_url_root(httpserver), '--to-type', 'Gitea', '--to-user', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'MyOrg', '--repos-include', 'spring-petclinic', '--branches-include', 'main']

    with patch.object(sys, 'argv', testargs):
        try:
            git_platforms_synchro.main()
            fail('Expected GitCommandError')
        except GitCommandError:
            assert 'Reusing existing cloned repo https://github.com/spring-projects/spring-petclinic.git' in caplog.text
            assert 'Synchronize branch...' in caplog.text
            assert 'The requested URL returned error: 542' in caplog.text


def test_from_github_to_gitea_tags_only(httpserver: HTTPServer, caplog: LogCaptureFixture):
    # httpserver doesn't support KeepAlive, so we need to mock the git clone as already existing bare directory (reuse mechanism) and mock the git push failure
    shutil.rmtree(git_platforms_synchro.TMP_REPO_GIT_DIRECTORY,
                  ignore_errors=True)
    with tarfile.open('tests/resources/spring-petclinic.git.tgz', 'r:gz') as tar:
        tar.extractall(
            path=git_platforms_synchro.TMP_REPO_GIT_DIRECTORY, filter='tar')
    httpserver.expect_request(
        '/MyOrg/spring-petclinic.git/info/refs', query_string='service=git-receive-pack', method='GET').respond_with_data(status=542)

    # GitHub with spring-projects
    expect_request(httpserver, 'github', '/orgs/spring-projects')
    expect_request(httpserver, 'github', '/orgs/spring-projects/repos')
    expect_request(httpserver, 'github',
                   '/repos/spring-projects/spring-petclinic')
    expect_request(httpserver, 'github',
                   '/repos/spring-projects/spring-petclinic/branches')

    # Gitea with same repo
    expect_request(httpserver, 'gitea', '/api/v1/orgs/MyOrg')
    # Declare empty page two before next first page result, infinite loop otherwise
    httpserver.expect_request(
        '/api/v1/orgs/MyOrg/repos',  query_string='page=2').respond_with_json([])
    expect_request(httpserver, 'gitea', '/api/v1/orgs/MyOrg/repos')
    expect_request(httpserver, 'gitea', '/api/v1/repos/MyOrg/spring-petclinic',
                   'http://localhost:3000', get_url_root(httpserver))
    expect_request(httpserver, 'gitea',
                   '/api/v1/repos/MyOrg/spring-petclinic/branches')

    testargs = ['prog', '--from-url', get_url_root(httpserver), '--from-type', 'GitHub', '--from-user', 'foo', '--from-password', 'bar',
                '--to-url', get_url_root(httpserver), '--to-type', 'Gitea', '--to-user', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'MyOrg', '--repos-include', 'spring-petclinic', '--branches-include', 'main']

    with patch.object(sys, 'argv', testargs):
        try:
            git_platforms_synchro.main()
            fail('Expected GitCommandError')
        except GitCommandError:
            assert 'Reusing existing cloned repo https://github.com/spring-projects/spring-petclinic.git' in caplog.text
            assert 'All branches already synchronized, do tags only...' in caplog.text
            assert 'The requested URL returned error: 542' in caplog.text
