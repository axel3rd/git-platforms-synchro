import json
import shutil
import tarfile

from git import Repo
from git_platforms_synchro import TMP_REPO_GIT_DIRECTORY
from pytest_httpserver import HTTPServer


def get_url_root(httpserver: HTTPServer) -> str:
    return httpserver.url_for('/').rstrip('/')


def load_json(file: str, url_to_mock: str, url_replacement: str):
    with open(file) as f:
        return json.loads(f.read().replace(url_to_mock, url_replacement))


def mock_cloned_repo(httpserver: HTTPServer, bare: bool = False):
    shutil.rmtree(TMP_REPO_GIT_DIRECTORY, ignore_errors=True)
    suffix = ''
    if bare:
        suffix = '.bare'
    with tarfile.open('tests/resources/spring-petclinic.git' + suffix + '.tgz', 'r:gz') as tar:
        tar.extractall(path=TMP_REPO_GIT_DIRECTORY)

    # Replace remote origin URL to point to httpserver
    repo = Repo(TMP_REPO_GIT_DIRECTORY)
    repo.remote('origin').set_url(
        get_url_root(httpserver) + '/spring-projects/spring-petclinic.git')


def expect_request(httpserver: HTTPServer, type: str, uri: str, str_to_replace: str = None, str_replacement: str = None):
    with open('tests/http_mocks/' + type + uri + '.json') as f:
        content = f.read()
    if type == 'github':
        content = content.replace(
            'https://api.github.com', get_url_root(httpserver)).replace(
            'https://github.com', get_url_root(httpserver))
    if type == 'gitea':
        content = content.replace(
            'http://localhost:3000', get_url_root(httpserver))
    if str_to_replace and str_replacement:
        content = content.replace(str_to_replace, str_replacement)
    httpserver.expect_request(uri).respond_with_json(json.loads(content))
