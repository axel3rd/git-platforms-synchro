from pytest_httpserver import HTTPServer
from pytest import LogCaptureFixture
from git_clients import GitClientFactory
from tests.test_utils import get_url_root, expect_request


def test_github_gets(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'github', '/users/spring-projects')
    expect_request(httpserver, 'github', '/users/spring-projects/repos')
    expect_request(httpserver, 'github',
                   '/repos/spring-projects/spring-petclinic')
    expect_request(httpserver, 'github',
                   '/repos/spring-projects/spring-petclinic/branches')
    expect_request(httpserver, 'github',
                   '/repos/spring-projects/spring-petclinic/tags')
    httpserver.expect_request(
        '/repos/spring-projects/non-existing-repo').respond_with_data(status=404)

    github = GitClientFactory.create_client(
        get_url_root(httpserver), 'github', 'ghu_xxxx')

    assert 30 == len(github.get_repos('spring-projects'))
    assert github.has_repo('spring-projects', 'spring-petclinic')
    assert not github.has_repo('spring-projects', 'non-existing-repo')
    assert get_url_root(httpserver) + '/spring-projects/spring-petclinic.git' == github.get_repo_clone_url(
        'spring-projects', 'spring-petclinic')
    assert 'A sample Spring-based application' == github.get_repo_description(
        'spring-projects', 'spring-petclinic')
    assert 8 == len(github.get_branches('spring-projects',
                                        'spring-petclinic'))
    assert 1 == len(github.get_tags('spring-projects',
                                    'spring-petclinic'))
    assert 'c36452a2c34443ae26b4ecbba4f149906af14717' == github.get_tags('spring-projects',
                                                                         'spring-petclinic')['1.5.x']


def test_github_org_create_repo(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'github', '/orgs/spring-projects')
    httpserver.expect_oneshot_request(
        '/orgs/spring-projects/repos', method='POST').respond_with_data(status=201)

    github = GitClientFactory.create_client(
        get_url_root(httpserver), 'github', 'ghu_xxxx')

    github.create_repo('spring-projects', 'new-repo')


def test_github_user_create_repo(httpserver: HTTPServer, caplog: LogCaptureFixture):
    httpserver.expect_request(
        '/orgs/spring-projects').respond_with_data(status=404)
    httpserver.expect_oneshot_request(
        '/user/repos', method='POST').respond_with_data(status=201)

    github = GitClientFactory.create_client(
        get_url_root(httpserver), 'github', 'ghu_xxxx')

    github.create_repo('spring-projects', 'new-repo')


def test_github_empty_branches_tags(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'github', '/users/spring-projects')
    expect_request(httpserver, 'github',
                   '/repos/spring-projects/spring-petclinic')
    httpserver.expect_request(
        '/repos/spring-projects/spring-petclinic/branches').respond_with_data('[]')
    httpserver.expect_request(
        '/repos/spring-projects/spring-petclinic/tags').respond_with_data('[]')

    github = GitClientFactory.create_client(
        get_url_root(httpserver), 'github', 'ghu_xxxx')

    assert 0 == len(github.get_branches('spring-projects',
                                        'spring-petclinic'))
    assert 0 == len(github.get_tags('spring-projects',
                                    'spring-petclinic'))


def test_gitea_gets(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'gitea', '/api/v1/users/MyOrg')
    # Declare empty page two before next first page result, infinite loop otherwise
    httpserver.expect_request(
        '/api/v1/users/MyOrg/repos',  query_string='page=2').respond_with_json([])
    expect_request(httpserver, 'gitea', '/api/v1/users/MyOrg/repos')
    expect_request(httpserver, 'gitea', '/api/v1/repos/MyOrg/spring-petclinic')
    expect_request(httpserver, 'gitea',
                   '/api/v1/repos/MyOrg/spring-petclinic/branches')
    expect_request(httpserver, 'gitea',
                   '/api/v1/repos/MyOrg/spring-petclinic/tags')
    httpserver.expect_request(
        '/api/v1/repos/MyOrg/non-existing-repo').respond_with_data(status=404)

    gitea = GitClientFactory.create_client(
        get_url_root(httpserver), 'gitea', 'foo', 'bar')

    assert 2 == len(gitea.get_repos('MyOrg'))
    assert gitea.has_repo('MyOrg', 'spring-petclinic')
    assert not gitea.has_repo('MyOrg', 'non-existing-repo')
    assert get_url_root(httpserver) + '/MyOrg/spring-petclinic.git' == gitea.get_repo_clone_url(
        'MyOrg', 'spring-petclinic')
    assert 'A (copied) sample Spring-based application' == gitea.get_repo_description(
        'MyOrg', 'spring-petclinic')
    assert 8 == len(gitea.get_branches('MyOrg',
                                       'spring-petclinic'))
    assert 1 == len(gitea.get_tags('MyOrg',
                                   'spring-petclinic'))
    assert 'c36452a2c34443ae26b4ecbba4f149906af14717' == gitea.get_tags('MyOrg',
                                                                        'spring-petclinic')['1.5.x']


def test_gitea_org_create_repo(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'gitea', '/api/v1/orgs/MyOrg')
    httpserver.expect_request(
        '/api/v1/orgs/MyOrg/repos', method='POST').respond_with_json(status=201, response_json={'id': 42, 'name': 'spring-petclinic'})

    gitea = GitClientFactory.create_client(
        get_url_root(httpserver), 'gitea', 'foo', 'bar')

    gitea.create_repo('MyOrg', 'new-repo', 'A new repo')


def test_gitea_user_create_repo(httpserver: HTTPServer, caplog: LogCaptureFixture):
    httpserver.expect_request(
        '/api/v1/orgs/MyOrg').respond_with_data(status=404)
    expect_request(httpserver, 'gitea', '/api/v1/users/MyOrg')
    httpserver.expect_request(
        '/api/v1/user/repos', method='POST').respond_with_json(status=201, response_json={'id': 42, 'name': 'spring-petclinic'})

    gitea = GitClientFactory.create_client(
        get_url_root(httpserver), 'gitea', 'foo', 'bar')

    gitea.create_repo('MyOrg', 'new-repo', 'A new repo')


def test_gitea_empty_branches_tags(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'gitea', '/api/v1/orgs/MyOrg')
    expect_request(httpserver, 'gitea',
                   '/api/v1/repos/MyOrg/spring-ai-examples-empty')
    httpserver.expect_request(
        '/api/v1/repos/MyOrg/spring-ai-examples-empty/tags').respond_with_data('[]')

    gitea = GitClientFactory.create_client(
        get_url_root(httpserver), 'gitea', 'foo', 'bar')

    assert 0 == len(gitea.get_branches('MyOrg',
                                       'spring-ai-examples-empty'))
    assert 0 == len(gitea.get_tags('MyOrg',
                                   'spring-ai-examples-empty'))
