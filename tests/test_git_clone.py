import sys
import shutil
from unittest.mock import patch
import tarfile
import git_platforms_synchro
from pytest import LogCaptureFixture


def test_cloned_reuse(caplog: LogCaptureFixture):
    shutil.rmtree(git_platforms_synchro.TMP_REPO_GIT_DIRECTORY,
                  ignore_errors=True)
    with tarfile.open('tests/resources/spring-petclinic.git.tgz', 'r:gz') as tar:
        tar.extractall(
            path=git_platforms_synchro.TMP_REPO_GIT_DIRECTORY, filter='tar')
    git_platforms_synchro.git_clone(
        'https://github.com', 'spring-projects', 'spring-petclinic')

    assert 'Reusing existing cloned repo https://github.com/spring-projects/spring-petclinic.git' in caplog.text


def test_cloned_new(caplog: LogCaptureFixture):
    shutil.rmtree(git_platforms_synchro.TMP_REPO_GIT_DIRECTORY,
                  ignore_errors=True)

    # TODO : Mock with a fake git server instead of really cloning and check error

    git_platforms_synchro.git_clone(
        'https://github.com', 'spring-projects', 'spring-petclinic')

    assert 'Cloning repo https://github.com/spring-projects/spring-petclinic.git' in caplog.text


def test_cloned_bad_from(caplog: LogCaptureFixture):
    shutil.rmtree(git_platforms_synchro.TMP_REPO_GIT_DIRECTORY,
                  ignore_errors=True)
    with tarfile.open('tests/resources/spring-petclinic.git.tgz', 'r:gz') as tar:
        tar.extractall(
            path=git_platforms_synchro.TMP_REPO_GIT_DIRECTORY, filter='tar')
    # TODO : Cloned repo will not be the current one


def test_mirror_reuse(caplog: LogCaptureFixture):
    shutil.rmtree(git_platforms_synchro.TMP_REPO_GIT_DIRECTORY,
                  ignore_errors=True)
    with tarfile.open('tests/resources/spring-petclinic.git.bare.tgz', 'r:gz') as tar:
        tar.extractall(
            path=git_platforms_synchro.TMP_REPO_GIT_DIRECTORY, filter='tar')
    git_platforms_synchro.git_clone(
        'https://github.com', 'spring-projects', 'spring-petclinic', mirror=True)

    assert 'Reusing existing cloned repo https://github.com/spring-projects/spring-petclinic.git' in caplog.text


def test_mirror_new(caplog: LogCaptureFixture):
    shutil.rmtree(git_platforms_synchro.TMP_REPO_GIT_DIRECTORY,
                  ignore_errors=True)

    # TODO : Mock with a fake git server instead of really cloning and check error

    git_platforms_synchro.git_clone(
        'https://github.com', 'spring-projects', 'spring-petclinic', mirror=True)

    assert 'Cloning repo https://github.com/spring-projects/spring-petclinic.git' in caplog.text


def test_mirror_bad_from(caplog: LogCaptureFixture):
    shutil.rmtree(git_platforms_synchro.TMP_REPO_GIT_DIRECTORY,
                  ignore_errors=True)
    with tarfile.open('tests/resources/spring-petclinic.git.bare.tgz', 'r:gz') as tar:
        tar.extractall(
            path=git_platforms_synchro.TMP_REPO_GIT_DIRECTORY, filter='tar')
    # TODO : Cloned repo will not be the current one
