import os
from modules.git_askpass import read_input_from_sys_env
from pytest import LogCaptureFixture


def test_bad_input():
    assert read_input_from_sys_env('') == 1
    assert read_input_from_sys_env('Bad') == 1


def test_no_sys_env(capsys):
    assert read_input_from_sys_env('Username') == 0
    assert read_input_from_sys_env('Password') == 0
    assert capsys.readouterr().out == '\n\n'


def test_username(capsys):
    os.environ['GIT_USERNAME'] = 'foo'
    assert read_input_from_sys_env('Username') == 0
    assert capsys.readouterr().out == 'foo\n'


def test_password(capsys):
    os.environ['GIT_PASSWORD'] = 'bar'  # noqa
    assert read_input_from_sys_env('Password') == 0
    assert capsys.readouterr().out == 'bar\n'


def test_username_and_password(capsys):
    os.environ['GIT_USERNAME'] = 'foo'
    os.environ['GIT_PASSWORD'] = 'bar'  # noqa
    assert read_input_from_sys_env('username') == 0
    assert read_input_from_sys_env('password') == 0
    assert capsys.readouterr().out == 'foo\nbar\n'
