"""
Level 01 Environment & Configuration Verification Test
"""
import os
import sys


def test_python_version():
    """Verify Python runtime version is 3.10+"""
    assert sys.version_info >= (3, 10), f"Python version {sys.version} is below 3.10"


def test_project_structure():
    """Verify core project root directories exist"""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    required_dirs = ["backend", "ai", "docs", "tests"]
    for dir_name in required_dirs:
        dir_path = os.path.join(base_dir, dir_name)
        assert os.path.isdir(dir_path), f"Required directory {dir_name} is missing"


def test_env_example_exists():
    """Verify .env.example exists and contains critical keys"""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env_example_path = os.path.join(base_dir, ".env.example")
    assert os.path.isfile(env_example_path), ".env.example is missing"

    with open(env_example_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "PROJECT_NAME" in content
    assert "DATABASE_URL" in content
    assert "REDIS_URL" in content
    assert "SECRET_KEY" in content
