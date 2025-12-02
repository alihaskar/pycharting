"""Tests for project configuration files."""
from pathlib import Path
import re


def test_gitignore_exists():
    """Test that .gitignore file exists."""
    project_root = Path(__file__).parent.parent
    gitignore = project_root / ".gitignore"
    
    assert gitignore.exists(), ".gitignore file not found"
    assert gitignore.is_file(), ".gitignore is not a file"


def test_gitignore_excludes_python_artifacts():
    """Test that .gitignore excludes Python-specific artifacts."""
    project_root = Path(__file__).parent.parent
    gitignore = project_root / ".gitignore"
    content = gitignore.read_text()
    
    required_patterns = [
        "__pycache__",
        "*.py[cod]",
        "*.so",
        ".Python",
        "*.egg-info",
        "dist",
        "build",
    ]
    
    for pattern in required_patterns:
        assert pattern in content, f"Pattern '{pattern}' not found in .gitignore"


def test_gitignore_excludes_venv():
    """Test that .gitignore excludes virtual environment directories."""
    project_root = Path(__file__).parent.parent
    gitignore = project_root / ".gitignore"
    content = gitignore.read_text()
    
    # Should have at least one venv pattern
    venv_patterns = ["venv/", ".venv/", "env/", ".env/"]
    has_venv_pattern = any(pattern in content for pattern in venv_patterns)
    
    assert has_venv_pattern, "No virtual environment patterns found in .gitignore"


def test_gitignore_excludes_data_files():
    """Test that .gitignore excludes data directory."""
    project_root = Path(__file__).parent.parent
    gitignore = project_root / ".gitignore"
    content = gitignore.read_text()
    
    assert "data/" in content, "data/ directory not excluded in .gitignore"


def test_gitignore_excludes_ide_files():
    """Test that .gitignore excludes common IDE files."""
    project_root = Path(__file__).parent.parent
    gitignore = project_root / ".gitignore"
    content = gitignore.read_text()
    
    ide_patterns = [".vscode", ".idea"]
    
    for pattern in ide_patterns:
        assert pattern in content, f"IDE pattern '{pattern}' not found in .gitignore"


def test_gitignore_excludes_env_files():
    """Test that .gitignore excludes environment variable files."""
    project_root = Path(__file__).parent.parent
    gitignore = project_root / ".gitignore"
    content = gitignore.read_text()
    
    assert ".env" in content, ".env file not excluded in .gitignore"


def test_readme_exists_and_not_empty():
    """Test that README.md exists and contains content."""
    project_root = Path(__file__).parent.parent
    readme = project_root / "README.md"
    
    assert readme.exists(), "README.md file not found"
    assert readme.is_file(), "README.md is not a file"
    
    content = readme.read_text()
    assert len(content) > 100, "README.md appears to be empty or too short"
    assert "# " in content, "README.md should contain at least one header"


def test_readme_contains_setup_instructions():
    """Test that README.md contains setup instructions."""
    project_root = Path(__file__).parent.parent
    readme = project_root / "README.md"
    content = readme.read_text().lower()
    
    required_sections = ["setup", "install", "poetry"]
    
    for section in required_sections:
        assert section in content, f"README.md should mention '{section}'"


def test_pyproject_toml_properly_configured():
    """Test that pyproject.toml is properly configured."""
    project_root = Path(__file__).parent.parent
    pyproject = project_root / "pyproject.toml"
    
    assert pyproject.exists(), "pyproject.toml not found"
    
    content = pyproject.read_text()
    
    # Check for essential sections
    assert "[tool.poetry]" in content, "Missing [tool.poetry] section"
    assert "[tool.poetry.dependencies]" in content, "Missing dependencies section"
    assert 'name = "charting"' in content, "Project name not set correctly"


def test_pytest_configuration():
    """Test that pytest is configured in pyproject.toml."""
    project_root = Path(__file__).parent.parent
    pyproject = project_root / "pyproject.toml"
    content = pyproject.read_text()
    
    # Check if pytest is in dev dependencies or regular dependencies
    has_pytest = "pytest" in content
    
    assert has_pytest, "pytest not found in dependencies"

