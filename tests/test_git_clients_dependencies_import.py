import re
from pytest import raises, mark

# This test mock 'sys.modules' which is shared between all tests
# So if executed alone, it work, but not in all tests suite
# A solution should be found to isolate it :-(

@mark.skip(reason='Should be isolated')
def test_no_github(mocker):
    mocker.patch.dict('sys.modules', {'github': None})
    with raises(ValueError, match=re.escape('Type "github" not supported or not detected from URL "http://localhost". Or python client dependency not installed - GitHub (PyGithub): False, Gitea (py-gitea): True, Bitbucket (atlassian-python-api): True')):
        from modules.git_clients import GitClientFactory
        GitClientFactory.create_client('http://localhost', 'github')

@mark.skip(reason='Should be isolated')
def test_no_gitea(mocker):
    mocker.patch.dict('sys.modules', {'gitea': None})
    with raises(ValueError, match=re.escape('Type "gitea" not supported or not detected from URL "http://localhost". Or python client dependency not installed - GitHub (PyGithub): True, Gitea (py-gitea): False, Bitbucket (atlassian-python-api): True')):
        from modules.git_clients import GitClientFactory
        GitClientFactory.create_client('http://localhost', 'gitea')

@mark.skip(reason='Should be isolated')
def test_no_bitbucket(mocker):
    mocker.patch.dict('sys.modules', {'atlassian': None})
    with raises(ValueError, match=re.escape('Type "bitbucket" not supported or not detected from URL "http://localhost". Or python client dependency not installed - GitHub (PyGithub): True, Gitea (py-gitea): True, Bitbucket (atlassian-python-api): False')):
        from modules.git_clients import GitClientFactory
        GitClientFactory.create_client('http://localhost', 'bitbucket')     