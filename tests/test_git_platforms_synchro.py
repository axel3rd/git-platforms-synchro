import re
import sys
import git_platforms_synchro
from git import GitCommandError
from unittest.mock import patch
from pytest_httpserver import HTTPServer
from pytest import LogCaptureFixture, raises
from tests.test_utils import get_url_root, expect_request, mock_cloned_repo


def get_test_args_github_to_gitea(httpserver: HTTPServer):
    testargs = ['prog', '--from-url', get_url_root(httpserver), '--from-type', 'GitHub', '--from-login', 'foo', '--from-password', 'bar',
                '--to-url', get_url_root(httpserver), '--to-type', 'Gitea', '--to-login', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'MyOrg', '--repos-include', 'spring-petclinic', '--branches-include', 'main,springboot3']
    return testargs


def prepare_github_with_spring_projects(httpserver: HTTPServer, prepare_branches: bool = True, prepare_tags: bool = True):
    # GitHub with spring-projects
    expect_request(httpserver, 'github', '/users/spring-projects')
    expect_request(httpserver, 'github', '/users/spring-projects/repos')
    expect_request(httpserver, 'github',
                   '/repos/spring-projects/spring-petclinic')
    if prepare_branches:
        expect_request(httpserver, 'github',
                       '/repos/spring-projects/spring-petclinic/branches')
    if prepare_tags:
        expect_request(httpserver, 'github',
                       '/repos/spring-projects/spring-petclinic/tags')


def prepare_gitea_with_spring_projects(httpserver: HTTPServer, prepare_branches: bool = True, prepare_tags: bool = True, update_commit: bool = False):
    expect_request(httpserver, 'gitea', '/api/v1/users/MyOrg')
    expect_request(httpserver, 'gitea',
                   '/api/v1/users/MyOrg/repos', query_string='page=1')
    httpserver.expect_request(
        '/api/v1/users/MyOrg/repos',  query_string='page=2').respond_with_json([])
    expect_request(httpserver, 'gitea', '/api/v1/repos/MyOrg/spring-petclinic')
    if prepare_branches:
        if update_commit:
            expect_request(httpserver, 'gitea',
                           '/api/v1/repos/MyOrg/spring-petclinic/branches', query_string='page=1', str_to_replace='6148ddd9671ccab86a3f0ae2dfa77d833b713ee8', str_replacement='bbbbddd9671ccab86a3f0ae2dfa77d833b713ee8')
        else:
            expect_request(httpserver, 'gitea',
                           '/api/v1/repos/MyOrg/spring-petclinic/branches', query_string='page=1')
        httpserver.expect_request(
            '/api/v1/repos/MyOrg/spring-petclinic/branches',  query_string='page=2').respond_with_json([])
    if prepare_tags:
        expect_request(httpserver, 'gitea',
                       '/api/v1/repos/MyOrg/spring-petclinic/tags', query_string='page=1')
        httpserver.expect_request(
            '/api/v1/repos/MyOrg/spring-petclinic/tags',  query_string='page=2').respond_with_json([])


def test_git_type_undefined(httpserver: HTTPServer):
    testargs = ['prog', '--from-url', get_url_root(httpserver), '--to-url', httpserver.url_for(
        '/'), '--to-login', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'new-org']

    with raises(ValueError, match='Type "" not supported or not detected from URL "' +
                get_url_root(httpserver) + '".'):
        with patch.object(sys, 'argv', testargs):
            git_platforms_synchro.main()
            # Should have raised an error
            assert False


def test_from_github_proxy_not_implemented(httpserver: HTTPServer, caplog: LogCaptureFixture):
    testargs = ['prog', '--dry-run', '--from-url', get_url_root(httpserver), '--from-type', 'GitHub', '--from-proxy', 'http://my-proxy:8080', '--from-login', 'ghu_foo1234567890abcdef',
                '--to-url', get_url_root(httpserver), '--to-type', 'GitHub', '--to-login', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'spring-projects', '--repos-include', 'spring-petclinic', '--branches-include', 'main,springboot3']

    with raises(NotImplementedError, match=re.escape('Proxy not implemented yet for GitHubClient (PyGithub#2426). Please use HTTP_PROXY/HTTPS_PROXY/NO_PROXY environment variables.')):
        with patch.object(sys, 'argv', testargs):
            git_platforms_synchro.main()


def test_same_from_to_github_no_auth(httpserver: HTTPServer, caplog: LogCaptureFixture):
    prepare_github_with_spring_projects(httpserver)

    testargs = ['prog', '--dry-run', '--from-url', get_url_root(httpserver), '--from-type', 'GitHub',
                '--to-url', get_url_root(httpserver), '--to-type', 'GitHub', '--to-login', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'spring-projects', '--repos-include', 'spring-petclinic', '--branches-include', 'main,springboot3']
    with patch.object(sys, 'argv', testargs):
        git_platforms_synchro.main()

    assert 'Already synchronized.' in caplog.text
    assert 'All branches already synchronized, do tags only...' not in caplog.text


def test_same_from_to_github_token(httpserver: HTTPServer, caplog: LogCaptureFixture):
    prepare_github_with_spring_projects(httpserver)

    testargs = ['prog', '--dry-run', '--from-url', get_url_root(httpserver), '--from-type', 'GitHub', '--from-login', 'ghu_foo1234567890abcdef',
                '--to-url', get_url_root(httpserver), '--to-type', 'GitHub', '--to-login', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'spring-projects', '--repos-include', 'spring-petclinic', '--branches-include', 'main,springboot3']
    with patch.object(sys, 'argv', testargs):
        git_platforms_synchro.main()

    assert 'Already synchronized.' in caplog.text
    assert 'All branches already synchronized, do tags only...' not in caplog.text


def test_same_from_to_gitea(httpserver: HTTPServer, caplog: LogCaptureFixture):
    prepare_gitea_with_spring_projects(httpserver)

    testargs = ['prog', '--dry-run', '--from-url', get_url_root(httpserver), '--from-type', 'Gitea', '--from-login', 'foo', '--from-password', 'bar',
                '--to-url', get_url_root(httpserver), '--to-type', 'Gitea', '--to-login', 'foo', '--to-password', 'bar', '--from-org', 'MyOrg', '--to-org', 'MyOrg', '--repos-include', 'spring-petclinic', '--branches-include', 'main,springboot3']
    with patch.object(sys, 'argv', testargs):
        git_platforms_synchro.main()

    assert 'Already synchronized.' in caplog.text
    assert 'All branches already synchronized, do tags only...' not in caplog.text


def test_from_github_empty_repo(httpserver: HTTPServer, caplog: LogCaptureFixture):
    prepare_github_with_spring_projects(httpserver, prepare_branches=False)
    httpserver.expect_request(
        '/repos/spring-projects/spring-petclinic/branches').respond_with_data('[]')
    prepare_gitea_with_spring_projects(httpserver)

    with patch.object(sys, 'argv', get_test_args_github_to_gitea(httpserver)):
        git_platforms_synchro.main()

    assert 'Repository has no branches on "from" platform, skipping.' in caplog.text


def test_from_github_to_gitea_mirror_create(httpserver: HTTPServer, caplog: LogCaptureFixture):
    prepare_github_with_spring_projects(httpserver)

    # Gitea with "Empty" org
    expect_request(httpserver, 'gitea', '/api/v1/orgs/MyOrg')
    httpserver.expect_request(
        '/api/v1/users/MyOrg/repos', query_string='page=1').respond_with_json([])
    httpserver.expect_oneshot_request(
        '/api/v1/repos/MyOrg/spring-petclinic').respond_with_data(status=404)
    httpserver.expect_request(
        '/api/v1/orgs/MyOrg/repos', method='POST').respond_with_json(status=201, response_json={'id': 42, 'name': 'spring-petclinic'})
    # Newly created repo at second call
    expect_request(httpserver, 'gitea', '/api/v1/repos/MyOrg/spring-petclinic')

    # httpserver doesn't support KeepAlive, so we need to mock the git clone as already existing bare directory (reuse mechanism) and mock the git push failure
    mock_cloned_repo(httpserver, bare=True)
    httpserver.expect_request(
        '/MyOrg/spring-petclinic.git/info/refs', query_string='service=git-receive-pack', method='GET').respond_with_data(status=542)

    with raises(GitCommandError):
        with patch.object(sys, 'argv', get_test_args_github_to_gitea(httpserver)):
            git_platforms_synchro.main()

    assert 'Repository does not exist on "to" plaform, create as mirror...' in caplog.text
    assert 'Reusing existing cloned repo ' + \
        get_url_root(httpserver) + \
        '/spring-projects/spring-petclinic.git' in caplog.text
    assert 'The requested URL returned error: 542' in caplog.text


def test_from_github_to_gitea_mirror_exist(httpserver: HTTPServer, caplog: LogCaptureFixture):
    prepare_github_with_spring_projects(httpserver)

    # Gitea with "Empty" org
    expect_request(httpserver, 'gitea', '/api/v1/orgs/MyOrg')
    httpserver.expect_request(
        '/api/v1/users/MyOrg/repos', query_string='page=1').respond_with_json([])

    # Empty repo on first call and newly created repo at second call ('empty' value not important in this case)
    expect_request(httpserver, 'gitea', '/api/v1/repos/MyOrg/spring-petclinic',
                   str_to_replace='"empty": false,', str_replacement='"empty": true,')
    httpserver.expect_request(
        '/api/v1/repos/MyOrg/spring-petclinic/branches',  query_string='page=1').respond_with_json([])

    # httpserver doesn't support KeepAlive, so we need to mock the git clone as already existing bare directory (reuse mechanism) and mock the git push failure
    mock_cloned_repo(httpserver, bare=True)
    httpserver.expect_request(
        '/MyOrg/spring-petclinic.git/info/refs', query_string='service=git-receive-pack', method='GET').respond_with_data(status=542)

    with raises(GitCommandError):
        with patch.object(sys, 'argv', get_test_args_github_to_gitea(httpserver)):
            git_platforms_synchro.main()
    assert 'Repository has no branches on "to" platform, synchronize as mirror...' in caplog.text
    assert 'Reusing existing cloned repo ' + \
        get_url_root(httpserver) + \
        '/spring-projects/spring-petclinic.git' in caplog.text
    assert 'The requested URL returned error: 542' in caplog.text


def test_from_github_to_gitea_sync(httpserver: HTTPServer, caplog: LogCaptureFixture):
    # httpserver doesn't support KeepAlive, so we need to mock the git clone as already existing bare directory (reuse mechanism) and mock the git push failure
    mock_cloned_repo(httpserver, bare=False)
    httpserver.expect_request(
        '/MyOrg/spring-petclinic.git/info/refs', query_string='service=git-receive-pack', method='GET').respond_with_data(status=542)

    # GitHub with spring-projects
    prepare_github_with_spring_projects(httpserver)

    # Gitea with same repo
    prepare_gitea_with_spring_projects(httpserver, update_commit=True)

    with raises(GitCommandError):
        with patch.object(sys, 'argv', get_test_args_github_to_gitea(httpserver)):
            git_platforms_synchro.main()

    assert 'Reusing existing cloned repo ' + \
        get_url_root(httpserver) + \
        '/spring-projects/spring-petclinic.git' in caplog.text
    assert 'Synchronize branch...' in caplog.text
    assert 'The requested URL returned error: 542' in caplog.text


def test_from_github_to_gitea_tags_only(httpserver: HTTPServer, caplog: LogCaptureFixture):
    # httpserver doesn't support KeepAlive, so we need to mock the git clone as already existing bare directory (reuse mechanism) and mock the git push failure
    mock_cloned_repo(httpserver, bare=False)
    httpserver.expect_request(
        '/MyOrg/spring-petclinic.git/info/refs', query_string='service=git-receive-pack', method='GET').respond_with_data(status=542)

    # GitHub with spring-projects
    prepare_github_with_spring_projects(httpserver)

    # Gitea with same repo
    prepare_gitea_with_spring_projects(httpserver, prepare_tags=False)
    httpserver.expect_request(
        '/api/v1/repos/MyOrg/spring-petclinic/tags').respond_with_data('[]')

    with raises(GitCommandError):
        with patch.object(sys, 'argv', get_test_args_github_to_gitea(httpserver)):
            git_platforms_synchro.main()

    assert 'Reusing existing cloned repo ' + \
        get_url_root(httpserver) + \
        '/spring-projects/spring-petclinic.git' in caplog.text
    assert 'All branches already synchronized, do tags only...' in caplog.text
    assert 'The requested URL returned error: 542' in caplog.text


def test_from_github_to_gitea_all_already_sync(httpserver: HTTPServer, caplog: LogCaptureFixture):
    # GitHub with spring-projects
    prepare_github_with_spring_projects(httpserver)

    # Gitea with same repo
    prepare_gitea_with_spring_projects(httpserver)

    with patch.object(sys, 'argv', get_test_args_github_to_gitea(httpserver)):
        git_platforms_synchro.main()

    assert 'Already synchronized.' in caplog.text
    assert 'Synchronize branch...' not in caplog.text
    assert 'All branches already synchronized, do tags only...' not in caplog.text
    assert 'Git Platforms Synchronization finished sucessfully. Repos updated: 0/1. Branches updated: 0/2' in caplog.text
