import sys
import subprocess


# File should be completly isolated, so dedicated process (works only from Python 3.11 & Pytest)
# GLobal code coverage should be executed with same options: --concurrency=thread --parallel-mode

def exec_test_method(test_file: str, test_method: str):
    subprocess.run([sys.executable, '-m', 'coverage', 'run', '--concurrency=thread', '--parallel-mode', '-m',
                   'pytest', test_file.replace('tests/', 'tests/sub') + '::' + test_method], check=True)


def test_no_bitbucket(request):
    exec_test_method(request.module.__file__, request.node.name)


def test_no_gitlab(request):
    exec_test_method(request.module.__file__, request.node.name)


def test_no_gitea(request):
    exec_test_method(request.module.__file__, request.node.name)


def test_no_github(request):
    exec_test_method(request.module.__file__, request.node.name)
