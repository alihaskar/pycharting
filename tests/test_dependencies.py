"""Tests for project dependencies."""
import importlib
import subprocess
from pathlib import Path


def test_core_dependencies_importable():
    """Test that all core dependencies can be imported."""
    core_packages = [
        "fastapi",
        "pandas",
        "numpy",
        "pydantic",
        "uvicorn",
    ]
    
    for package in core_packages:
        try:
            importlib.import_module(package)
        except ImportError as e:
            assert False, f"Failed to import {package}: {e}"


def test_dev_dependencies_importable():
    """Test that all development dependencies can be imported."""
    dev_packages = [
        "pytest",
    ]
    
    for package in dev_packages:
        try:
            importlib.import_module(package)
        except ImportError as e:
            assert False, f"Failed to import dev dependency {package}: {e}"


def test_poetry_lock_exists():
    """Test that poetry.lock file exists for reproducible installs."""
    project_root = Path(__file__).parent.parent
    lock_file = project_root / "poetry.lock"
    
    assert lock_file.exists(), "poetry.lock file not found. Run 'poetry install'"


def test_dependencies_installed():
    """Test that Poetry reports all dependencies as installed."""
    result = subprocess.run(
        ["poetry", "check"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Poetry check failed: {result.stdout}\n{result.stderr}"


def test_specific_package_versions():
    """Test that specific core packages are available with version info."""
    packages_to_check = {
        "fastapi": "fastapi",
        "pandas": "pandas",
        "numpy": "numpy",
    }
    
    for module_name, package_name in packages_to_check.items():
        module = importlib.import_module(module_name)
        assert hasattr(module, "__version__"), f"{package_name} does not expose __version__"
        assert module.__version__, f"{package_name} version is empty"

