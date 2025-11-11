import sys
import git_platforms_synchro
from git import GitCommandError
from unittest.mock import patch
from pytest_httpserver import HTTPServer
from pytest import LogCaptureFixture, fail
from tests.test_utils import get_url_root, expect_request, mock_cloned_repo


def prepare_github_with_spring_projects(httpserver: HTTPServer, prepare_branches: bool = True):
    # GitHub with spring-projects
    expect_request(httpserver, 'github', '/users/spring-projects')
    expect_request(httpserver, 'github', '/users/spring-projects/repos')
    expect_request(httpserver, 'github',
                   '/repos/spring-projects/spring-petclinic')
    if prepare_branches:
        expect_request(httpserver, 'github',
                       '/repos/spring-projects/spring-petclinic/branches')


def prepare_gitea_with_spring_projects(httpserver: HTTPServer, update_commit: bool = False):
    expect_request(httpserver, 'gitea', '/api/v1/users/MyOrg')
    # Declare empty page two before next first page result, infinite loop otherwise
    httpserver.expect_request(
        '/api/v1/users/MyOrg/repos',  query_string='page=2').respond_with_json([])
    expect_request(httpserver, 'gitea', '/api/v1/users/MyOrg/repos')
    expect_request(httpserver, 'gitea', '/api/v1/repos/MyOrg/spring-petclinic')
    if update_commit:
        expect_request(httpserver, 'gitea',
                       '/api/v1/repos/MyOrg/spring-petclinic/branches', '6148ddd9671ccab86a3f0ae2dfa77d833b713ee8', 'bbbbddd9671ccab86a3f0ae2dfa77d833b713ee8')
    else:
        expect_request(httpserver, 'gitea',
                       '/api/v1/repos/MyOrg/spring-petclinic/branches')


def test_git_type_undefined(httpserver: HTTPServer):
    testargs = ['prog', '--from-url', httpserver.url_for('/'), '--to-url', httpserver.url_for(
        '/'), '--to-login', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'new-org']
    try:
        with patch.object(sys, 'argv', testargs):
            git_platforms_synchro.main()
            # Should have raised an error
            assert False
    except ValueError as e:
        assert str(e) == 'Type "" not supported or not detected from URL "' + \
            httpserver.url_for('/') + '".'


def test_same_from_to_github_no_auth(httpserver: HTTPServer, caplog: LogCaptureFixture):
    prepare_github_with_spring_projects(httpserver)

    testargs = ['prog', '--dry-run', '--from-url', httpserver.url_for('/'), '--from-type', 'GitHub',
                '--to-url', httpserver.url_for('/'), '--to-type', 'GitHub', '--to-login', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'spring-projects', '--repos-include', 'spring-petclinic', '--branches-include', 'main,springboot3']
    with patch.object(sys, 'argv', testargs):
        git_platforms_synchro.main()

    assert 'Already synchronized.' in caplog.text
    assert 'All branches already synchronized, do tags only...' in caplog.text


def test_same_from_to_github_token(httpserver: HTTPServer, caplog: LogCaptureFixture):
    prepare_github_with_spring_projects(httpserver)

    testargs = ['prog', '--dry-run', '--from-url', httpserver.url_for('/'), '--from-type', 'GitHub', '--from-login', 'ghu_foo1234567890abcdef',
                '--to-url', httpserver.url_for('/'), '--to-type', 'GitHub', '--to-login', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'spring-projects', '--repos-include', 'spring-petclinic', '--branches-include', 'main,springboot3']
    with patch.object(sys, 'argv', testargs):
        git_platforms_synchro.main()

    assert 'Already synchronized.' in caplog.text
    assert 'All branches already synchronized, do tags only...' in caplog.text


def test_same_from_to_gitea(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'gitea', '/api/v1/users/MyOrg')
    # Declare empty page two before next first page result, infinite loop otherwise
    httpserver.expect_request(
        '/api/v1/users/MyOrg/repos',  query_string='page=2').respond_with_json([])
    expect_request(httpserver, 'gitea', '/api/v1/users/MyOrg/repos')
    expect_request(httpserver, 'gitea', '/api/v1/repos/MyOrg/spring-petclinic')
    expect_request(httpserver, 'gitea',
                   '/api/v1/repos/MyOrg/spring-petclinic/branches')

    testargs = ['prog', '--dry-run', '--from-url', httpserver.url_for('/'), '--from-type', 'Gitea', '--from-login', 'foo', '--from-password', 'bar',
                '--to-url', httpserver.url_for('/'), '--to-type', 'Gitea', '--to-login', 'foo', '--to-password', 'bar', '--from-org', 'MyOrg', '--to-org', 'MyOrg', '--repos-include', 'spring-petclinic', '--branches-include', 'main,springboot3']
    with patch.object(sys, 'argv', testargs):
        git_platforms_synchro.main()

    assert 'Already synchronized.' in caplog.text
    assert 'All branches already synchronized, do tags only...' in caplog.text


def test_from_github_empty_repo(httpserver: HTTPServer, caplog: LogCaptureFixture):
    prepare_github_with_spring_projects(httpserver, prepare_branches=False)
    httpserver.expect_request(
        '/repos/spring-projects/spring-petclinic/branches').respond_with_data('[]')
    prepare_gitea_with_spring_projects(httpserver)

    testargs = ['prog', '--from-url', get_url_root(httpserver), '--from-type', 'GitHub',
                '--to-url', get_url_root(httpserver), '--to-type', 'Gitea', '--to-login', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'MyOrg', '--repos-include', 'spring-petclinic', '--branches-include', 'main,springboot3']
    with patch.object(sys, 'argv', testargs):
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

    testargs = ['prog', '--from-url', get_url_root(httpserver), '--from-type', 'GitHub',
                '--to-url', get_url_root(httpserver), '--to-type', 'Gitea', '--to-login', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'MyOrg', '--repos-include', 'spring-petclinic', '--branches-include', 'main,springboot3']
    with patch.object(sys, 'argv', testargs):
        try:
            git_platforms_synchro.main()
            fail('Expected GitCommandError')
        except GitCommandError:
            assert 'Repository does not exist on "to" plaform, will be created as mirror.' in caplog.text
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
                   '"empty": false,', '"empty": true,')

    # httpserver doesn't support KeepAlive, so we need to mock the git clone as already existing bare directory (reuse mechanism) and mock the git push failure
    mock_cloned_repo(httpserver, bare=True)
    httpserver.expect_request(
        '/MyOrg/spring-petclinic.git/info/refs', query_string='service=git-receive-pack', method='GET').respond_with_data(status=542)

    testargs = ['prog', '--from-url', get_url_root(httpserver), '--from-type', 'GitHub',
                '--to-url', get_url_root(httpserver), '--to-type', 'Gitea', '--to-login', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'MyOrg', '--repos-include', 'spring-petclinic', '--branches-include', 'main,springboot3']
    with patch.object(sys, 'argv', testargs):
        try:
            git_platforms_synchro.main()
            fail('Expected GitCommandError')
        except GitCommandError:
            assert 'Repository has no branches on "to" platform, will be mirrored.' in caplog.text
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

    testargs = ['prog', '--from-url', get_url_root(httpserver), '--from-type', 'GitHub', '--from-login', 'foo', '--from-password', 'bar',
                '--to-url', get_url_root(httpserver), '--to-type', 'Gitea', '--to-login', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'MyOrg', '--repos-include', 'spring-petclinic', '--branches-include', 'main']

    with patch.object(sys, 'argv', testargs):
        try:
            git_platforms_synchro.main()
            fail('Expected GitCommandError')
        except GitCommandError:
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
    prepare_gitea_with_spring_projects(httpserver)

    testargs = ['prog', '--from-url', get_url_root(httpserver), '--from-type', 'GitHub', '--from-login', 'foo', '--from-password', 'bar',
                '--to-url', get_url_root(httpserver), '--to-type', 'Gitea', '--to-login', 'foo', '--to-password', 'bar', '--from-org', 'spring-projects', '--to-org', 'MyOrg', '--repos-include', 'spring-petclinic', '--branches-include', 'main']

    with patch.object(sys, 'argv', testargs):
        try:
            git_platforms_synchro.main()
            fail('Expected GitCommandError')
        except GitCommandError:
            assert 'Reusing existing cloned repo ' + \
                get_url_root(httpserver) + \
                '/spring-projects/spring-petclinic.git' in caplog.text
            assert 'All branches already synchronized, do tags only...' in caplog.text
            assert 'The requested URL returned error: 542' in caplog.text
