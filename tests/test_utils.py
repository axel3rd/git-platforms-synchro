import os
import json
import tarfile
from git import Repo
from git_platforms_synchro import TMP_REPO_GIT_DIRECTORY, delete_temporary_repo_git_directory
from modules.utils import ENV_TEST_MODE
from pytest_httpserver import HTTPServer


def get_url_root(httpserver: HTTPServer) -> str:
    return httpserver.url_for('/').rstrip('/')


def load_json(file: str, url_to_mock: str, url_replacement: str):
    with open(file) as f:
        return json.loads(f.read().replace(url_to_mock, url_replacement))


def mock_cloned_repo(httpserver: HTTPServer, bare: bool = False):
    delete_temporary_repo_git_directory(force_if_test_mode=True)
    os.environ[ENV_TEST_MODE] = 'true'
    suffix = ''
    if bare:
        suffix = '.bare'
    with tarfile.open('tests/resources/spring-petclinic.git' + suffix + '.tgz', 'r:gz') as tar:
        tar.extractall(path=TMP_REPO_GIT_DIRECTORY)

    # Replace remote origin URL to point to httpserver
    repo = Repo(TMP_REPO_GIT_DIRECTORY)
    repo.remote('origin').set_url(get_url_root(httpserver) + '/spring-projects/spring-petclinic.git')


def expect_request(httpserver: HTTPServer, type: str, uri: str, query_string: str = None,
                   str_to_replace: str = None, str_replacement: str = None, file_suffix: str = ''):
    with open('tests/http_mocks/' + type + uri + file_suffix + '.json') as f:
        content = f.read()
    if type == 'github':
        content = content.replace('https://api.github.com', get_url_root(httpserver)).replace('https://github.com', get_url_root(httpserver))
    if type == 'gitea':
        content = content.replace('http://localhost:3000', get_url_root(httpserver))
    if type == 'bitbucket':
        content = content.replace('http://localhost:7990', get_url_root(httpserver))
    if type == 'gitlab':
        content = content.replace('https://gitlab.com', get_url_root(httpserver))
    if str_to_replace and str_replacement:
        content = content.replace(str_to_replace, str_replacement)
    httpserver.expect_request(uri, query_string=query_string).respond_with_json(json.loads(content))
