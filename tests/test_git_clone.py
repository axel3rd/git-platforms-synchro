import shutil
import tarfile
import git_platforms_synchro
from pytest import LogCaptureFixture, fail
from pytest_httpserver import HTTPServer
from git import GitCommandError
from tests.test_utils import get_url_root


def test_cloned_reuse(caplog: LogCaptureFixture):
    shutil.rmtree(git_platforms_synchro.TMP_REPO_GIT_DIRECTORY,
                  ignore_errors=True)
    with tarfile.open('tests/resources/spring-petclinic.git.tgz', 'r:gz') as tar:
        tar.extractall(
            path=git_platforms_synchro.TMP_REPO_GIT_DIRECTORY, filter='tar')
    git_platforms_synchro.git_clone(
        'https://github.com/spring-projects/spring-petclinic.git')

    assert 'Reusing existing cloned repo https://github.com/spring-projects/spring-petclinic.git' in caplog.text


def test_cloned_new(httpserver: HTTPServer, caplog: LogCaptureFixture):
    shutil.rmtree(git_platforms_synchro.TMP_REPO_GIT_DIRECTORY,
                  ignore_errors=True)

    httpserver.expect_request(
        '/spring-projects/spring-petclinic.git/info/refs', query_string='service=git-upload-pack', method='GET').respond_with_data(status=542)

    clone_url = get_url_root(httpserver) + \
        '/spring-projects/spring-petclinic.git'
    try:
        git_platforms_synchro.git_clone(clone_url)
        fail('Expected GitCommandError')
    except GitCommandError:
        assert 'Cloning repo ' + clone_url in caplog.text
        assert '"GET /spring-projects/spring-petclinic.git/info/refs?service=git-upload-pack HTTP/1.1" 542 -' in caplog.text
        assert 'The requested URL returned error: 542' in caplog.text


def test_cloned_bad_from_org(httpserver: HTTPServer, caplog: LogCaptureFixture):
    shutil.rmtree(git_platforms_synchro.TMP_REPO_GIT_DIRECTORY,
                  ignore_errors=True)
    with tarfile.open('tests/resources/spring-petclinic.git.tgz', 'r:gz') as tar:
        tar.extractall(
            path=git_platforms_synchro.TMP_REPO_GIT_DIRECTORY, filter='tar')
    httpserver.expect_request(
        '/spring-projects-other/spring-petclinic.git/info/refs', query_string='service=git-upload-pack', method='GET').respond_with_data(status=542)

    clone_url = get_url_root(httpserver) + \
        '/spring-projects-other/spring-petclinic.git'
    try:
        git_platforms_synchro.git_clone(clone_url)
    except GitCommandError:
        assert 'Cloning repo ' + clone_url in caplog.text
        assert '"GET /spring-projects-other/spring-petclinic.git/info/refs?service=git-upload-pack HTTP/1.1" 542 -' in caplog.text
        assert 'The requested URL returned error: 542' in caplog.text


def test_cloned_bad_from_repo(httpserver: HTTPServer, caplog: LogCaptureFixture):
    shutil.rmtree(git_platforms_synchro.TMP_REPO_GIT_DIRECTORY,
                  ignore_errors=True)
    with tarfile.open('tests/resources/spring-petclinic.git.tgz', 'r:gz') as tar:
        tar.extractall(
            path=git_platforms_synchro.TMP_REPO_GIT_DIRECTORY, filter='tar')

    httpserver.expect_request(
        '/spring-projects/spring-petclinic-other.git/info/refs', query_string='service=git-upload-pack', method='GET').respond_with_data(status=542)

    clone_url = get_url_root(httpserver) + \
        '/spring-projects/spring-petclinic-other.git'
    try:
        git_platforms_synchro.git_clone(clone_url)
    except GitCommandError:
        assert 'Cloning repo ' + clone_url in caplog.text
        assert '"GET /spring-projects/spring-petclinic-other.git/info/refs?service=git-upload-pack HTTP/1.1" 542 -' in caplog.text
        assert 'The requested URL returned error: 542' in caplog.text


def test_mirror_reuse(caplog: LogCaptureFixture):
    shutil.rmtree(git_platforms_synchro.TMP_REPO_GIT_DIRECTORY,
                  ignore_errors=True)
    with tarfile.open('tests/resources/spring-petclinic.git.bare.tgz', 'r:gz') as tar:
        tar.extractall(
            path=git_platforms_synchro.TMP_REPO_GIT_DIRECTORY, filter='tar')

    git_platforms_synchro.git_clone(
        'https://github.com/spring-projects/spring-petclinic.git', mirror=True)

    assert 'Reusing existing cloned repo https://github.com/spring-projects/spring-petclinic.git' in caplog.text


def test_mirror_new(httpserver: HTTPServer, caplog: LogCaptureFixture):
    shutil.rmtree(git_platforms_synchro.TMP_REPO_GIT_DIRECTORY,
                  ignore_errors=True)

    httpserver.expect_request(
        '/spring-projects/spring-petclinic.git/info/refs', query_string='service=git-upload-pack', method='GET').respond_with_data(status=542)

    try:
        git_platforms_synchro.git_clone(get_url_root(
            httpserver) + '/spring-projects/spring-petclinic.git', mirror=True)
        fail('Expected GitCommandError')
    except GitCommandError:
        assert '"GET /spring-projects/spring-petclinic.git/info/refs?service=git-upload-pack HTTP/1.1" 542 -' in caplog.text
        assert 'The requested URL returned error: 542' in caplog.text


def test_mirror_bad_from_org(httpserver: HTTPServer, caplog: LogCaptureFixture):
    shutil.rmtree(git_platforms_synchro.TMP_REPO_GIT_DIRECTORY,
                  ignore_errors=True)
    with tarfile.open('tests/resources/spring-petclinic.git.bare.tgz', 'r:gz') as tar:
        tar.extractall(
            path=git_platforms_synchro.TMP_REPO_GIT_DIRECTORY, filter='tar')

    httpserver.expect_request(
        '/spring-projects-other/spring-petclinic.git/info/refs', query_string='service=git-upload-pack', method='GET').respond_with_data(status=542)

    clone_url = get_url_root(httpserver) + \
        '/spring-projects-other/spring-petclinic.git'
    try:
        git_platforms_synchro.git_clone(clone_url, mirror=True)
    except GitCommandError:
        assert 'Cloning repo ' + clone_url in caplog.text
        assert '"GET /spring-projects-other/spring-petclinic.git/info/refs?service=git-upload-pack HTTP/1.1" 542 -' in caplog.text
        assert 'The requested URL returned error: 542' in caplog.text


def test_mirror_bad_from_repo(httpserver: HTTPServer, caplog: LogCaptureFixture):
    shutil.rmtree(git_platforms_synchro.TMP_REPO_GIT_DIRECTORY,
                  ignore_errors=True)
    with tarfile.open('tests/resources/spring-petclinic.git.bare.tgz', 'r:gz') as tar:
        tar.extractall(
            path=git_platforms_synchro.TMP_REPO_GIT_DIRECTORY, filter='tar')

    httpserver.expect_request(
        '/spring-projects/spring-petclinic-other.git/info/refs', query_string='service=git-upload-pack', method='GET').respond_with_data(status=542)

    clone_url = get_url_root(httpserver) + \
        '/spring-projects/spring-petclinic-other.git'
    try:
        git_platforms_synchro.git_clone(clone_url, mirror=True)
    except GitCommandError:
        assert 'Cloning repo ' + clone_url in caplog.text
        assert '"GET /spring-projects/spring-petclinic-other.git/info/refs?service=git-upload-pack HTTP/1.1" 542 -' in caplog.text
        assert 'The requested URL returned error: 542' in caplog.text
