import os
from modules.git_askpass import read_input_from_sys_env


def test_bad_input():
    assert read_input_from_sys_env('') == 1
    assert read_input_from_sys_env('Bad') == 1


def test_no_sys_env(capsys):
    assert read_input_from_sys_env('Username') == 0
    assert read_input_from_sys_env('Password') == 0
    assert capsys.readouterr().out == '\n\n'


def test_username(capsys, monkeypatch):
    monkeypatch.setenv('GIT_USERNAME', 'foo')
    assert read_input_from_sys_env('Username') == 0
    assert capsys.readouterr().out == 'foo\n'


def test_password(capsys, monkeypatch):
    monkeypatch.setenv('GIT_PASSWORD', 'bar')  # noqa
    assert read_input_from_sys_env('Password') == 0
    assert capsys.readouterr().out == 'bar\n'


def test_username_and_password(capsys, monkeypatch):
    monkeypatch.setenv('GIT_USERNAME', 'foo')
    monkeypatch.setenv('GIT_PASSWORD', 'bar')  # noqa
    assert read_input_from_sys_env('username') == 0
    assert read_input_from_sys_env('password') == 0
    assert capsys.readouterr().out == 'foo\nbar\n'
