import re
from pytest_httpserver import HTTPServer
from pytest import LogCaptureFixture, raises
from modules.git_clients import GitClientFactory, GitClient, check_input, check_input_empty
from tests.test_utils import get_url_root, expect_request
from requests import exceptions
from github import GithubException
from gitlab import GitlabError


def test_interface():
    client = GitClient()
    client.get_login_or_token()
    client.get_password()
    client.get_url()
    client.get_repos('org')
    client.has_repo('org', 'repo')
    client.get_branches('org', 'repo')
    client.get_tags('org', 'repo')
    client.get_repo_description('org', 'repo')
    client.get_repo_clone_url('org', 'repo')
    client.create_repo('org', 'repo')
    client.create_repo('org', 'repo', 'description')


def test_check_inputs():
    with raises(ValueError, match='not empty'):
        check_input_empty('value', 'not empty')
    with raises(ValueError, match='empty'):
        check_input('', 'empty')
    with raises(ValueError, match='empty'):
        check_input(None, 'empty')  # NOSONAR : Test wanted


def test_type_undefined(caplog: LogCaptureFixture):
    with raises(ValueError, match=re.escape('Type "None" not supported or not detected from URL "https://fake.url.dev". Or python client dependency not installed - Bitbucket (atlassian-python-api): True, Gerrit (python-gerrit-api): True, Gitea (py-gitea): True, GitLab (python-gitlab): True, GitHub (PyGithub): True.')):
        GitClientFactory.create_client('https://fake.url.dev')
    with raises(ValueError, match=re.escape('Type "" not supported or not detected from URL "https://fake.url.dev". Or python client dependency not installed - Bitbucket (atlassian-python-api): True, Gerrit (python-gerrit-api): True, Gitea (py-gitea): True, GitLab (python-gitlab): True, GitHub (PyGithub): True.')):
        GitClientFactory.create_client('https://fake.url.dev', '')


def test_github_proxy(httpserver: HTTPServer, caplog: LogCaptureFixture):
    proxy = get_url_root(httpserver)
    with raises(NotImplementedError, match=re.escape('Proxy not implemented yet for GitHubClient (PyGithub#2426). Please use HTTP_PROXY/HTTPS_PROXY/NO_PROXY environment variables.')):
        GitClientFactory.create_client('https://fake.url.dev', 'github', 'ghu_xxxx', proxy=proxy)


def test_github_connection_params():
    github = GitClientFactory.create_client('https://fake.url.dev', 'github', 'ghu_xxxx')
    assert github.get_login_or_token() == 'ghu_xxxx'
    assert github.get_url() == 'https://fake.url.dev'
    assert github.get_password() is None
    github = GitClientFactory.create_client('https://fake.url.dev', 'github', 'login', 'password')
    assert github.get_login_or_token() == 'login'
    assert github.get_password() == 'password'


def test_github_gets(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'github', '/users/spring-projects')
    expect_request(httpserver, 'github', '/users/spring-projects/repos')
    expect_request(httpserver, 'github', '/repos/spring-projects/spring-petclinic')
    expect_request(httpserver, 'github', '/repos/spring-projects/spring-petclinic/branches')
    expect_request(httpserver, 'github', '/repos/spring-projects/spring-petclinic/tags')
    httpserver.expect_request('/repos/spring-projects/non-existing-repo').respond_with_data(status=404)

    github = GitClientFactory.create_client(get_url_root(httpserver), 'github', 'ghu_xxxx')

    assert len(github.get_repos('spring-projects')) == 30
    assert github.has_repo('spring-projects', 'spring-petclinic')
    assert not github.has_repo('spring-projects', 'non-existing-repo')
    assert get_url_root(httpserver) + '/spring-projects/spring-petclinic.git' == github.get_repo_clone_url('spring-projects', 'spring-petclinic')
    assert github.get_repo_description('spring-projects', 'spring-petclinic') == 'A sample Spring-based application'
    assert len(github.get_branches('spring-projects', 'spring-petclinic')) == 8
    assert len(github.get_tags('spring-projects', 'spring-petclinic')) == 1
    assert github.get_tags('spring-projects', 'spring-petclinic')['1.5.x'] == 'c36452a2c34443ae26b4ecbba4f149906af14717'


def test_github_org_create_repo(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'github', '/orgs/spring-projects')
    httpserver.expect_oneshot_request('/orgs/spring-projects/repos', method='POST').respond_with_data(status=201)

    github = GitClientFactory.create_client(get_url_root(httpserver), 'github', 'ghu_xxxx')

    github.create_repo('spring-projects', 'new-repo')


def test_github_user_create_repo(httpserver: HTTPServer, caplog: LogCaptureFixture):
    httpserver.expect_request('/orgs/spring-projects').respond_with_data(status=404)
    httpserver.expect_oneshot_request('/user/repos', method='POST').respond_with_data(status=201)

    github = GitClientFactory.create_client(get_url_root(httpserver), 'github', 'ghu_xxxx')

    github.create_repo('spring-projects', 'new-repo')


def test_github_empty_branches_tags(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'github', '/users/spring-projects')
    expect_request(httpserver, 'github', '/repos/spring-projects/spring-petclinic')
    httpserver.expect_request('/repos/spring-projects/spring-petclinic/branches').respond_with_data('[]')
    httpserver.expect_request('/repos/spring-projects/spring-petclinic/tags').respond_with_data('[]')
    github = GitClientFactory.create_client(get_url_root(httpserver), 'github', 'ghu_xxxx')

    assert len(github.get_branches('spring-projects', 'spring-petclinic')) == 0
    assert len(github.get_tags('spring-projects', 'spring-petclinic')) == 0


def test_github_errors_has_repo(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'github', '/users/spring-projects')
    httpserver.expect_request('/repos/spring-projects/spring-petclinic').respond_with_data(status=442)
    github = GitClientFactory.create_client(get_url_root(httpserver), 'github', 'ghu_xxxx')
    with raises(GithubException, match='442'):
        github.has_repo('spring-projects', 'spring-petclinic')


def test_github_errors_create_repo(httpserver: HTTPServer, caplog: LogCaptureFixture):
    httpserver.expect_request('/orgs/spring-projects').respond_with_data(status=442)
    github = GitClientFactory.create_client(get_url_root(httpserver), 'github', 'ghu_xxxx')
    with raises(GithubException, match='442'):
        github.create_repo('spring-projects', 'spring-petclinic', 'fake')


def test_gitea_proxy(httpserver: HTTPServer, caplog: LogCaptureFixture):
    gitea = GitClientFactory.create_client('https://fake.url.dev', 'gitea', 'foo', 'bar', proxy=get_url_root(httpserver))

    with raises(exceptions.ProxyError):
        gitea.get_repos('Fake')

    assert 'CONNECT fake.url.dev:443 HTTP/1' in caplog.text


def test_gitea_connection_params():
    gitea = GitClientFactory.create_client('https://fake.url.dev', 'gitea', 'login', 'password')
    assert gitea.get_login_or_token() == 'login'
    assert gitea.get_password() == 'password'
    assert gitea.get_url() == 'https://fake.url.dev'


def test_gitea_gets(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'gitea', '/api/v1/users/MyOrg')
    expect_request(httpserver, 'gitea', '/api/v1/users/MyOrg/repos', query_string='page=1')
    httpserver.expect_request('/api/v1/users/MyOrg/repos', query_string='page=2').respond_with_json([])
    expect_request(httpserver, 'gitea', '/api/v1/repos/MyOrg/spring-petclinic')
    expect_request(httpserver, 'gitea', '/api/v1/repos/MyOrg/spring-petclinic/branches', query_string='page=1')
    httpserver.expect_request('/api/v1/repos/MyOrg/spring-petclinic/branches', query_string='page=2').respond_with_json([])
    expect_request(httpserver, 'gitea', '/api/v1/repos/MyOrg/spring-petclinic/tags', query_string='page=1')
    httpserver.expect_request('/api/v1/repos/MyOrg/spring-petclinic/tags', query_string='page=2').respond_with_json([])
    httpserver.expect_request('/api/v1/repos/MyOrg/non-existing-repo').respond_with_data(status=404)

    gitea = GitClientFactory.create_client(get_url_root(httpserver), 'gitea', 'foo', 'bar')

    assert len(gitea.get_repos('MyOrg')) == 2
    assert gitea.has_repo('MyOrg', 'spring-petclinic')
    assert not gitea.has_repo('MyOrg', 'non-existing-repo')
    assert get_url_root(httpserver) + '/MyOrg/spring-petclinic.git' == gitea.get_repo_clone_url('MyOrg', 'spring-petclinic')
    assert gitea.get_repo_description('MyOrg', 'spring-petclinic') == 'A (copied) sample Spring-based application'
    assert len(gitea.get_branches('MyOrg', 'spring-petclinic')) == 8
    assert len(gitea.get_tags('MyOrg', 'spring-petclinic')) == 1
    assert gitea.get_tags('MyOrg', 'spring-petclinic')['1.5.x'] == 'c36452a2c34443ae26b4ecbba4f149906af14717'


def test_gitea_org_create_repo(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'gitea', '/api/v1/orgs/MyOrg')
    httpserver.expect_request('/api/v1/orgs/MyOrg/repos', method='POST').respond_with_json(status=201, response_json={
        'id': 42,
        'name': 'spring-petclinic'})

    gitea = GitClientFactory.create_client(get_url_root(httpserver), 'gitea', 'foo', 'bar')

    gitea.create_repo('MyOrg', 'new-repo', 'A new repo')


def test_gitea_user_create_repo(httpserver: HTTPServer, caplog: LogCaptureFixture):
    httpserver.expect_request('/api/v1/orgs/MyOrg').respond_with_data(status=404)
    expect_request(httpserver, 'gitea', '/api/v1/users/MyOrg')
    httpserver.expect_request('/api/v1/user/repos', method='POST').respond_with_json(status=201, response_json={'id': 42, 'name': 'spring-petclinic'})

    gitea = GitClientFactory.create_client(get_url_root(httpserver), 'gitea', 'foo', 'bar')

    gitea.create_repo('MyOrg', 'new-repo', 'A new repo')


def test_gitea_empty_branches_tags(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'gitea', '/api/v1/orgs/MyOrg')
    expect_request(httpserver, 'gitea', '/api/v1/repos/MyOrg/spring-ai-examples-empty')
    httpserver.expect_request('/api/v1/repos/MyOrg/spring-ai-examples-empty/branches').respond_with_data('[]')
    httpserver.expect_request('/api/v1/repos/MyOrg/spring-ai-examples-empty/tags').respond_with_data('[]')

    gitea = GitClientFactory.create_client(get_url_root(httpserver), 'gitea', 'foo', 'bar')

    assert len(gitea.get_branches('MyOrg', 'spring-ai-examples-empty')) == 0
    assert len(gitea.get_tags('MyOrg', 'spring-ai-examples-empty')) == 0


def test_gitea_pagination_repos(httpserver: HTTPServer):
    expect_request(httpserver, 'gitea', '/api/v1/users/MyOrgMany')
    for i in range(1, 4):
        expect_request(httpserver, 'gitea', '/api/v1/users/MyOrgMany/repos', query_string=f'page={i}', file_suffix=f'.{i}')
    httpserver.expect_request('/api/v1/users/MyOrgMany/repos', query_string='page=4').respond_with_json([])

    gitea = GitClientFactory.create_client(get_url_root(httpserver), 'gitea', 'foo', 'bar')

    repos = gitea.get_repos('MyOrgMany')
    assert len(repos) == 62
    assert 'repo-0' in repos
    assert 'repo-1' in repos
    assert 'repo-42' in repos
    assert 'repo-60' in repos
    assert 'repo-61' in repos


def test_gitea_pagination_branches_and_tags(httpserver: HTTPServer):
    expect_request(httpserver, 'gitea', '/api/v1/users/MyOrg')
    expect_request(httpserver, 'gitea', '/api/v1/repos/MyOrg/many')

    for i in range(1, 4):
        expect_request(httpserver, 'gitea', '/api/v1/repos/MyOrg/many/branches', query_string=f'page={i}', file_suffix=f'.{i}')
        expect_request(httpserver, 'gitea', '/api/v1/repos/MyOrg/many/tags', query_string=f'page={i}', file_suffix=f'.{i}')
    httpserver.expect_request('/api/v1/repos/MyOrg/many/branches', query_string='page=4').respond_with_json([])
    httpserver.expect_request('/api/v1/repos/MyOrg/many/tags', query_string='page=4').respond_with_json([])

    gitea = GitClientFactory.create_client(get_url_root(httpserver), 'gitea', 'foo', 'bar')

    branches = gitea.get_branches('MyOrg', 'many')
    assert len(branches) == 65
    assert 'branch-1766187828' in branches
    assert 'branch-1766187943' in branches
    assert 'branch-1766188006' in branches
    assert 'branch-1766188063' in branches

    tags = gitea.get_tags('MyOrg', 'many')
    assert len(tags) == 64
    assert 'v1.1766187743' in tags
    assert 'v1.1766187923' in tags
    assert 'v1.1766187939' in tags
    assert 'v1.1766187950' in tags
    assert 'v1.1766188010' in tags
    assert 'v1.1766188040' in tags
    assert 'v1.1766188055' in tags
    assert 'v1.1766188064' in tags


def test_bitbucket_proxy(httpserver: HTTPServer, caplog: LogCaptureFixture):
    bitbucket = GitClientFactory.create_client('https://fake.url.dev', 'bitbucket', 'fake_token', proxy=get_url_root(httpserver))

    with raises(exceptions.ProxyError):
        bitbucket.get_repos('Fake')

    assert 'CONNECT fake.url.dev:443 HTTP/1' in caplog.text


def test_bitbucket_connection_params():
    bitbucket = GitClientFactory.create_client('https://fake.url.dev', 'bitbucket', 'login', 'password')
    assert bitbucket.get_login_or_token() == 'login'
    assert bitbucket.get_password() == 'password'
    assert bitbucket.get_url() == 'https://fake.url.dev'


def test_bitbucket_gets(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'bitbucket', '/rest/api/1.0/projects/MyOrg/repos')
    expect_request(httpserver, 'bitbucket', '/rest/api/1.0/projects/MyOrg/repos/spring-petclinic')
    expect_request(httpserver, 'bitbucket', '/rest/api/1.0/projects/MyOrg/repos/spring-petclinic/branches')
    expect_request(httpserver, 'bitbucket', '/rest/api/1.0/projects/MyOrg/repos/spring-petclinic/tags')
    httpserver.expect_request('/rest/api/1.0/projects/MyOrg/repos/non-existing-repo').respond_with_data(status=404)

    bitbucket = GitClientFactory.create_client(get_url_root(httpserver), 'bitbucket', 'fake_token')

    assert len(bitbucket.get_repos('MyOrg')) == 2
    assert bitbucket.has_repo('MyOrg', 'spring-petclinic')
    assert not bitbucket.has_repo('MyOrg', 'non-existing-repo')
    assert get_url_root(httpserver) + '/scm/myorg/spring-petclinic.git' == bitbucket.get_repo_clone_url('MyOrg', 'spring-petclinic')
    assert bitbucket.get_repo_description('MyOrg', 'spring-petclinic') == 'A sample Spring-based application'
    assert len(bitbucket.get_branches('MyOrg', 'spring-petclinic')) == 8
    assert len(bitbucket.get_tags('MyOrg', 'spring-petclinic')) == 1
    assert bitbucket.get_tags('MyOrg', 'spring-petclinic')['1.5.x'] == 'c36452a2c34443ae26b4ecbba4f149906af14717'


def test_bitbucket_create_repo(httpserver: HTTPServer, caplog: LogCaptureFixture):
    httpserver.expect_oneshot_request('/rest/api/1.0/projects/MyOrg/repos', method='POST').respond_with_json(status=201, response_json={
        'id': 42,
        'slug': 'new-repo',
        'name': 'new-repo'})
    httpserver.expect_oneshot_request('/rest/api/1.0/projects/MyOrg/repos/new-repo', method='PUT').respond_with_json(status=200, response_json={
        'id': 42,
        'slug': 'new-repo',
        'name': 'new-repo'})

    bitbucket = GitClientFactory.create_client(get_url_root(httpserver), 'bitbucket', 'ghu_xxxx')

    bitbucket.create_repo('MyOrg', 'new-repo')


def test_bitbucket_empty_branches_tags(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'bitbucket', '/rest/api/1.0/projects/MyOrg/repos')
    expect_request(httpserver, 'bitbucket', '/rest/api/1.0/projects/MyOrg/repos/spring-ai-examples')
    expect_request(httpserver, 'bitbucket', '/rest/api/1.0/projects/MyOrg/repos/spring-ai-examples/branches')
    expect_request(httpserver, 'bitbucket', '/rest/api/1.0/projects/MyOrg/repos/spring-ai-examples/tags')

    bitbucket = GitClientFactory.create_client(get_url_root(httpserver), 'bitbucket', 'fake_token')

    assert len(bitbucket.get_branches('MyOrg', 'spring-ai-examples')) == 0
    assert len(bitbucket.get_tags('MyOrg', 'spring-ai-examples')) == 0


def test_bitbucket_bad_clone_url_http(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'bitbucket', '/rest/api/1.0/projects/MyOrg/repos/spring-ai-examples-no-clone-url-http')
    bitbucket = GitClientFactory.create_client(get_url_root(httpserver), 'bitbucket', 'fake_token')
    with raises(ValueError, match='Cannot not found http clone link'):
        bitbucket.get_repo_clone_url('MyOrg', 'spring-ai-examples-no-clone-url-http')


def test_gitlab_proxy(httpserver: HTTPServer, caplog: LogCaptureFixture):
    gitlab = GitClientFactory.create_client('https://fake.url.dev', 'gitlab', 'fake_token', proxy=get_url_root(httpserver))

    with raises(exceptions.ProxyError):
        gitlab.get_repos('Fake')

    assert 'CONNECT fake.url.dev:443 HTTP/1' in caplog.text


def test_gitlab_connection_params():
    gitlab = GitClientFactory.create_client('https://fake.url.dev', 'gitlab', 'login', 'password')
    assert gitlab.get_login_or_token() == 'login'
    assert gitlab.get_password() == 'password'
    assert gitlab.get_url() == 'https://fake.url.dev'

    gitlab = GitClientFactory.create_client('https://fake.url.dev', 'gitlab', 'glpat-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
    assert gitlab.get_login_or_token() == 'glpat-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    assert gitlab.get_password() is None

    # ~Recall for 'private_token' deteaction from password in initialization
    gitlab = GitClientFactory.create_client('https://fake.url.dev', 'gitlab', 'foo', 'glpat-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
    assert gitlab.get_login_or_token() == 'foo'
    assert gitlab.get_password() == 'glpat-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'


def test_gitlab_gets(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'gitlab', '/api/v4/users', 'username=axel3rd')
    expect_request(httpserver, 'gitlab', '/api/v4/users/42/projects', 'include_subgroups=True')
    expect_request(httpserver, 'gitlab', '/api/v4/projects/axel3rd/spring-petclinic')
    expect_request(httpserver, 'gitlab', '/api/v4/projects/78242723/repository/branches')
    expect_request(httpserver, 'gitlab', '/api/v4/projects/78242723/repository/tags')
    httpserver.expect_request('/api/v4/projects/axel3rd/non-existing-repo').respond_with_data(status=404)

    gitlab = GitClientFactory.create_client(get_url_root(httpserver), 'gitlab', 'glpat-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')

    assert len(gitlab.get_repos('axel3rd')) == 2
    assert gitlab.has_repo('axel3rd', 'spring-petclinic')
    assert not gitlab.has_repo('axel3rd', 'non-existing-repo')
    assert get_url_root(httpserver) + '/axel3rd/spring-petclinic.git' == gitlab.get_repo_clone_url('axel3rd', 'spring-petclinic')
    assert gitlab.get_repo_description('axel3rd', 'spring-petclinic') == 'A sample Spring-based application'
    assert len(gitlab.get_branches('axel3rd', 'spring-petclinic')) == 8
    assert len(gitlab.get_tags('axel3rd', 'spring-petclinic')) == 1
    assert gitlab.get_tags('axel3rd', 'spring-petclinic')['1.5.x'] == 'c36452a2c34443ae26b4ecbba4f149906af14717'


def test_gitlab_create_repo(httpserver: HTTPServer, caplog: LogCaptureFixture):
    httpserver.expect_request('/api/v4/projects', method='POST').respond_with_json(status=201, response_json={
        'id': 42,
        'name': 'new-repo'})

    gitlab = GitClientFactory.create_client(get_url_root(httpserver), 'gitlab', 'glpat-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')

    gitlab.create_repo('axel3rd', 'new-repo')


def test_gitlab_empty_branches_tags(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'gitlab', '/api/v4/users', 'username=axel3rd')
    expect_request(httpserver, 'gitlab', '/api/v4/users/42/projects', 'include_subgroups=True')
    expect_request(httpserver, 'gitlab', '/api/v4/projects/axel3rd/spring-petclinic')
    httpserver.expect_request('/api/v4/projects/78242723/repository/branches').respond_with_data('[]')
    httpserver.expect_request('/api/v4/projects/78242723/repository/tags').respond_with_data('[]')

    gitlab = GitClientFactory.create_client(get_url_root(httpserver), 'gitlab', 'glpat-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')

    assert len(gitlab.get_branches('axel3rd', 'spring-petclinic')) == 0
    assert len(gitlab.get_tags('axel3rd', 'spring-petclinic')) == 0


def test_gitlab_errors_has_repo(httpserver: HTTPServer, caplog: LogCaptureFixture):
    httpserver.expect_request('/api/v4/projects/axel3rd/spring-petclinic').respond_with_data(status=442)
    gitlab = GitClientFactory.create_client(get_url_root(httpserver), 'gitlab', 'glpat-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
    with raises(GitlabError, match='442'):
        gitlab.has_repo('axel3rd', 'spring-petclinic')


def test_gerrit_proxy(httpserver: HTTPServer, caplog: LogCaptureFixture):
    gerrit = GitClientFactory.create_client('https://fake.url.dev', 'gerrit', 'foo', 'bar', proxy=get_url_root(httpserver))

    with raises(exceptions.ProxyError):
        gerrit.get_repos('')

    assert 'CONNECT fake.url.dev:443 HTTP/1' in caplog.text


def test_gerrit_connection_params():
    gerrit = GitClientFactory.create_client('https://fake.url.dev', 'gerrit', 'login', 'password')
    assert gerrit.get_login_or_token() == 'login'
    assert gerrit.get_password() == 'password'
    assert gerrit.get_url() == 'https://fake.url.dev'


def test_gerrit_gets(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'gerrit', '/a/projects/', 'all=1&d=0')
    expect_request(httpserver, 'gerrit', '/a/projects/test-repo')
    expect_request(httpserver, 'gerrit', '/a/projects/test-repo/description')
    expect_request(httpserver, 'gerrit', '/a/projects/test-repo/branches/', 'n=0&s=0')
    expect_request(httpserver, 'gerrit', '/a/projects/test-repo/tags/', 'n=0&s=0')
    httpserver.expect_request('/a/projects/non-existing-repo').respond_with_data(status=404)

    gerrit = GitClientFactory.create_client(get_url_root(httpserver), 'gerrit', 'foo', 'bar')

    assert len(gerrit.get_repos('')) == 104
    assert gerrit.has_repo('', 'test-repo')
    assert not gerrit.has_repo('', 'non-existing-repo')
    assert get_url_root(httpserver) + '/test-repo.git' == gerrit.get_repo_clone_url('', 'test-repo')
    assert gerrit.get_repo_description('', 'test-repo') == 'Testing repo'
    assert len(gerrit.get_branches('', 'test-repo')) == 100
    assert len(gerrit.get_tags('', 'test-repo')) == 99
    assert gerrit.get_tags('', 'test-repo')['tag-1'] == '1fdc5f22d58eeb8ea2395f81d84854439141a848'


def test_gerrit_create_repo(httpserver: HTTPServer, caplog: LogCaptureFixture):
    httpserver.expect_oneshot_request('/a/projects/test-repo', method='GET').respond_with_data(status=404)
    httpserver.expect_oneshot_request('/a/projects/test-repo', method='PUT').respond_with_data(status=201)
    # On creation, Gerrit get project twice
    httpserver.expect_oneshot_request('/a/projects/test-repo', method='GET').respond_with_json({'id': 'test-repo'})
    httpserver.expect_oneshot_request('/a/projects/test-repo', method='GET').respond_with_json({'id': 'test-repo'})

    gerrit = GitClientFactory.create_client(get_url_root(httpserver), 'gerrit', 'foo', 'bar')

    gerrit.create_repo('', 'test-repo')


def test_gerrit_empty_branches_tags(httpserver: HTTPServer, caplog: LogCaptureFixture):
    expect_request(httpserver, 'gerrit', '/a/projects/test-repo-1')
    expect_request(httpserver, 'gerrit', '/a/projects/test-repo-1/branches/', 'n=0&s=0')
    httpserver.expect_request('/a/projects/test-repo-1/tags/', query_string='n=0&s=0').respond_with_data('[]')

    gerrit = GitClientFactory.create_client(get_url_root(httpserver), 'gerrit', 'foo', 'bar')

    assert len(gerrit.get_branches('', 'test-repo-1')) == 0
    assert len(gerrit.get_tags('', 'test-repo-1')) == 0
