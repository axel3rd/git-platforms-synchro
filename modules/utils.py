import os
import stat
import shutil
import subprocess


TMP_REPO_GIT_DIRECTORY = 'tmp-git-repo/'
ENV_TEST_MODE = 'TEST_MODE'


def delete_temporary_repo_git_directory(force_if_test_mode: bool = False):
    if os.environ.get(ENV_TEST_MODE) != 'true' or force_if_test_mode:
        if os.path.exists(TMP_REPO_GIT_DIRECTORY) and os.path.isdir(TMP_REPO_GIT_DIRECTORY):
            try:
                shutil.rmtree(TMP_REPO_GIT_DIRECTORY)
            except PermissionError as e:
                # Windows case
                if 'nt' in os.name:
                    subprocess.run(['cmd', '/c', 'rmdir', '/s', '/q', TMP_REPO_GIT_DIRECTORY.rstrip('/')], shell=True)
                else:
                    raise e


def set_file_execution_permission(file: str):
    if not os.access(file, os.X_OK):
        permissions = os.stat(file).st_mode
        os.chmod(file, permissions | stat.S_IXUSR | stat.S_IXGRP)


def get_git_ask_pass() -> str:
    os_windows = os.name == 'nt'
    working_dir = os.path.dirname(os.path.realpath(__file__))
    git_askpass = os.path.join(working_dir, 'git_askpass.' + ('bat' if os_windows else 'py'))
    if not os_windows:
        set_file_execution_permission(git_askpass)
    return git_askpass


def test_git_ask_pass() -> None:
    git_askpass = get_git_ask_pass()
    custom_env = os.environ.copy()
    custom_env['GIT_USERNAME'] = 'test42'
    custom_env['GIT_PASSWORD'] = '42test'  # noqa: S2068
    result_user = subprocess.run([git_askpass, 'Username'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=custom_env)
    result_pwd = subprocess.run([git_askpass, 'Password'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=custom_env)
    os.environ.pop('GIT_USERNAME', None)
    os.environ.pop('GIT_PASSWORD', None)
    if result_user.returncode != 0 or result_user.stdout != 'test42\n' or result_pwd.returncode != 0 or result_pwd.stdout != '42test\n':
        raise ValueError(
            'PROBLEM: The ' +
            git_askpass +
            ' used for Git authentications without credentials storage cannot be executed, please verify file Dos/Unix encoding and/or permissions.')
