import os
import json
import tarfile
import tempfile
import pytest
from unittest.mock import patch
from git import Repo
from modules.utils import ENV_TEST_MODE, TMP_REPO_GIT_DIRECTORY, delete_temporary_repo_git_directory, set_file_execution_permission, test_git_ask_pass
from pytest_httpserver import HTTPServer


def get_url_root(httpserver: HTTPServer) -> str:
    return httpserver.url_for('/').rstrip('/')


def load_json(file: str, url_to_mock: str = None, url_replacement: str = None):
    with open(file) as f:
        content = f.read()
        if url_to_mock and url_replacement:
            content = content.replace(url_to_mock, url_replacement)
        return json.loads(content)


def mock_cloned_repo(httpserver: HTTPServer, bare: bool = False):
    delete_temporary_repo_git_directory(force_if_test_mode=True)
    os.environ[ENV_TEST_MODE] = 'true'
    suffix = ''
    if bare:
        suffix = '.bare'
    with tarfile.open('tests/resources/spring-petclinic.git' + suffix + '.tgz', 'r:gz') as tar:
        tar.extractall(path=TMP_REPO_GIT_DIRECTORY, filter='fully_trusted')

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


@pytest.mark.skipif(os.name == 'nt', reason='Specific Linux test')
def test_delete_temporary_repo_git_directory_permission_denied_linux():
    if not os.path.exists(TMP_REPO_GIT_DIRECTORY):
        os.mkdir(TMP_REPO_GIT_DIRECTORY)
    with patch('shutil.rmtree', side_effect=PermissionError("Permission denied")):
        with pytest.raises(PermissionError) as excinfo:
            delete_temporary_repo_git_directory(True)
        assert 'Permission denied' in str(excinfo.value)


@pytest.mark.skipif(os.name == 'nt', reason='Specific Linux test')
def test_delete_temporary_repo_git_directory_permission_denied_windows(capsys):
    if not os.path.exists(TMP_REPO_GIT_DIRECTORY):
        os.mkdir(TMP_REPO_GIT_DIRECTORY)

    mock_result = type('MockResult', (), {
        'stdout': '',
        'stderr': '',
        'returncode': 0
    })()

    with patch('shutil.rmtree', side_effect=PermissionError("Permission denied")):
        with patch('os.name', 'nt'):
            with patch('subprocess.run', return_value=mock_result) as mock_run:
                delete_temporary_repo_git_directory(True)
                mock_run.assert_called_once_with(['cmd', '/c', 'rmdir', '/s', '/q', 'tmp-git-repo'], shell=True)


@pytest.mark.skipif(os.name == 'nt', reason='Specific Linux test')
def test_set_file_execution_permission():
    with tempfile.NamedTemporaryFile(mode='w', delete=True) as temp_file:
        assert not os.access(temp_file.name, os.X_OK)
        set_file_execution_permission(temp_file.name)
        assert os.access(temp_file.name, os.X_OK)


def test_test_git_ask_pass():
    test_git_ask_pass()
