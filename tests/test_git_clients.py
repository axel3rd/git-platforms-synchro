from pytest_httpserver import HTTPServer
from pytest import LogCaptureFixture
from git_clients import GitClientFactory
from tests.test_utils import get_url_root, expect_request


def test_github_org(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'github', '/orgs/spring-projects')
    expect_request(httpserver, 'github', '/orgs/spring-projects/repos')
    expect_request(httpserver, 'github',
                   '/repos/spring-projects/spring-petclinic')
    expect_request(httpserver, 'github',
                   '/repos/spring-projects/spring-petclinic/branches')
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


def test_github_user(httpserver: HTTPServer, caplog: LogCaptureFixture):
    # TODO Not yet implemented
    assert False, "Not yet implemented"


def test_gitea_org(httpserver: HTTPServer, caplog: LogCaptureFixture):
    # TODO Not yet implemented
    assert False, "Not yet implemented"


def test_gitea_user(httpserver: HTTPServer, caplog: LogCaptureFixture):
    # TODO Not yet implemented
    assert False, "Not yet implemented"
