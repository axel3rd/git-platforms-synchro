import subprocess
import sys

def test_sub():
    test_file = "tests/subtest_git_clients_dependencies_import.py"
    subprocess.run([sys.executable, "-m", "pytest", test_file], check=True)