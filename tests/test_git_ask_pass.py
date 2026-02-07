import os
from modules.git_askpass import read_input_from_sys_env
from pytest import LogCaptureFixture


def test_bad_input():
    assert 1 == read_input_from_sys_env('')
    assert 1 == read_input_from_sys_env('Bad')


def test_no_sys_env(capsys):
    assert 0 == read_input_from_sys_env('Username')
    assert 0 == read_input_from_sys_env('Password')
    assert '\n\n' == capsys.readouterr().out


def test_username(capsys):
    os.environ['GIT_USERNAME'] = 'foo'
    assert 0 == read_input_from_sys_env('Username')
    assert 'foo\n' == capsys.readouterr().out


def test_password(capsys):
    os.environ['GIT_PASSWORD'] = 'bar'  # noqa
    assert 0 == read_input_from_sys_env('Password')
    assert 'bar\n' == capsys.readouterr().out


def test_username_and_password(capsys):
    os.environ['GIT_USERNAME'] = 'foo'
    os.environ['GIT_PASSWORD'] = 'bar'  # noqa
    assert 0 == read_input_from_sys_env('username')
    assert 0 == read_input_from_sys_env('password')
    assert 'foo\nbar\n' == capsys.readouterr().out
