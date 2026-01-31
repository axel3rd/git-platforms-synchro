import re, sys
from pytest import raises, fixture
from contextlib import contextmanager

# This test mock 'sys.modules' which is shared between all tests
# So if executed alone, it work, but not in all tests suite
# So complete isolation for each test with a new context

def test_no_github(mocker):
    mocker.patch.dict('sys.modules', {'github': None})
    with raises(ValueError, match=re.escape('Type "github" not supported or not detected from URL "http://localhost". Or python client dependency not installed - GitHub (PyGithub): False, Gitea (py-gitea): True, Bitbucket (atlassian-python-api): True')):
        from modules.git_clients import GitClientFactory
        GitClientFactory.create_client('http://localhost', 'github')

def test_no_gitea(mocker):
    mocker.patch.dict('sys.modules', {'gitea': None})
    with raises(ValueError, match=re.escape('Type "gitea" not supported or not detected from URL "http://localhost". Or python client dependency not installed - GitHub (PyGithub): True, Gitea (py-gitea): False, Bitbucket (atlassian-python-api): True')):
        from modules.git_clients import GitClientFactory
        GitClientFactory.create_client('http://localhost', 'gitea')

def test_no_bitbucket(mocker):
    mocker.patch.dict('sys.modules', {'atlassian': None})
    with raises(ValueError, match=re.escape('Type "bitbucket" not supported or not detected from URL "http://localhost". Or python client dependency not installed - GitHub (PyGithub): True, Gitea (py-gitea): True, Bitbucket (atlassian-python-api): False')):
        from modules.git_clients import GitClientFactory
        GitClientFactory.create_client('http://localhost', 'bitbucket')     