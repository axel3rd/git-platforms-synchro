import re
import sys
from pytest import raises, fixture
from contextlib import contextmanager

# This test mock 'sys.modules' which is shared between all tests
# So if executed alone, it work, but not in all tests suite
# So complete isolation for each test with a process via tests/test_git_clients_dependencies_import.py execution

STR_SYS_MODULES = 'sys.modules'
STR_LOCALHOST = 'http://localhost'


def test_no_bitbucket(mocker):
    mocker.patch.dict(STR_SYS_MODULES, {'atlassian': None})
    with raises(ValueError, match=re.escape('Type "bitbucket" not supported or not detected from URL "http://localhost". Or python client dependency not installed - Bitbucket (atlassian-python-api): False, Gerrit (python-gerrit-api): True, Gitea (py-gitea): True, GitLab (python-gitlab): True, GitHub (PyGithub): True.')):
        from modules.git_clients import GitClientFactory
        GitClientFactory.create_client(STR_LOCALHOST, 'bitbucket')


def test_no_gerrit(mocker):
    mocker.patch.dict(STR_SYS_MODULES, {'gerrit': None})
    with raises(ValueError, match=re.escape('Type "gerrit" not supported or not detected from URL "http://localhost". Or python client dependency not installed - Bitbucket (atlassian-python-api): True, Gerrit (python-gerrit-api): False, Gitea (py-gitea): True, GitLab (python-gitlab): True, GitHub (PyGithub): True.')):
        from modules.git_clients import GitClientFactory
        GitClientFactory.create_client(STR_LOCALHOST, 'gerrit')


def test_no_gitea(mocker):
    mocker.patch.dict(STR_SYS_MODULES, {'gitea': None})
    with raises(ValueError, match=re.escape('Type "gitea" not supported or not detected from URL "http://localhost". Or python client dependency not installed - Bitbucket (atlassian-python-api): True, Gerrit (python-gerrit-api): True, Gitea (py-gitea): False, GitLab (python-gitlab): True, GitHub (PyGithub): True.')):
        from modules.git_clients import GitClientFactory
        GitClientFactory.create_client(STR_LOCALHOST, 'gitea')


def test_no_gitlab(mocker):
    mocker.patch.dict(STR_SYS_MODULES, {'gitlab': None})
    with raises(ValueError, match=re.escape('Type "gitlab" not supported or not detected from URL "http://localhost". Or python client dependency not installed - Bitbucket (atlassian-python-api): True, Gerrit (python-gerrit-api): True, Gitea (py-gitea): True, GitLab (python-gitlab): False, GitHub (PyGithub): True.')):
        from modules.git_clients import GitClientFactory
        GitClientFactory.create_client(STR_LOCALHOST, 'gitlab')


def test_no_github(mocker):
    mocker.patch.dict(STR_SYS_MODULES, {'github': None})
    with raises(ValueError, match=re.escape('Type "github" not supported or not detected from URL "http://localhost". Or python client dependency not installed - Bitbucket (atlassian-python-api): True, Gerrit (python-gerrit-api): True, Gitea (py-gitea): True, GitLab (python-gitlab): True, GitHub (PyGithub): False.')):
        from modules.git_clients import GitClientFactory
        GitClientFactory.create_client(STR_LOCALHOST, 'github')
