import os
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
