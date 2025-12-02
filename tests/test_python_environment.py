"""Tests for Python virtual environment setup."""
import sys
import subprocess
from pathlib import Path


def test_python_version_is_3_11_or_higher():
    """Test that Python version is 3.11 or higher."""
    version_info = sys.version_info
    assert version_info.major == 3, f"Python major version is {version_info.major}, expected 3"
    assert version_info.minor >= 11, (
        f"Python minor version is {version_info.minor}, expected 11 or higher. "
        f"Current version: {version_info.major}.{version_info.minor}.{version_info.micro}"
    )


def test_environment_isolation():
    """Test that we're running in a virtual environment."""
    # Check if we're in a virtual environment by looking for VIRTUAL_ENV or poetry venv markers
    in_virtualenv = (
        hasattr(sys, 'real_prefix') or  # Old virtualenv
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or  # venv
        'VIRTUAL_ENV' in sys.prefix  # Any virtualenv marker
    )
    
    assert in_virtualenv, (
        "Not running in a virtual environment. "
        "Activate the environment with 'poetry shell' or 'poetry run'"
    )


def test_poetry_environment_exists():
    """Test that Poetry environment is configured."""
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"
    
    assert pyproject_path.exists(), "pyproject.toml not found"
    
    # Check if Poetry can detect the environment
    result = subprocess.run(
        ["poetry", "env", "info", "--path"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, "Poetry environment not found"
    assert result.stdout.strip(), "Poetry environment path is empty"

