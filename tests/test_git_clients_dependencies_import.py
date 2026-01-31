import re
from pytest import raises

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