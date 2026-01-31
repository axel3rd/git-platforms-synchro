import subprocess
import sys

# File should be completly isolated, so dedicated process (works only from Python 3.11 & Pytest)
def test_sub():
    test_file = "tests/subtest_git_clients_dependencies_import.py"
    subprocess.run([sys.executable, "-m", "pytest", test_file], check=True)