"""Tests for project directory structure."""
import os
from pathlib import Path


def test_root_directories_exist():
    """Test that all required root-level directories exist."""
    project_root = Path(__file__).parent.parent
    
    required_dirs = [
        "src",
        "data",
        "tests",
    ]
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_name} does not exist"
        assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"


def test_src_subdirectories_exist():
    """Test that all required src subdirectories exist."""
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    
    required_subdirs = [
        "ingestion",
        "processing",
        "api",
        "frontend",
    ]
    
    for subdir_name in required_subdirs:
        subdir_path = src_dir / subdir_name
        assert subdir_path.exists(), f"Subdirectory src/{subdir_name} does not exist"
        assert subdir_path.is_dir(), f"src/{subdir_name} exists but is not a directory"


def test_module_init_files_exist():
    """Test that __init__.py files exist in Python modules."""
    project_root = Path(__file__).parent.parent
    
    required_init_files = [
        "src/__init__.py",
        "src/ingestion/__init__.py",
        "src/processing/__init__.py",
        "src/api/__init__.py",
    ]
    
    for init_file in required_init_files:
        init_path = project_root / init_file
        assert init_path.exists(), f"Init file {init_file} does not exist"
        assert init_path.is_file(), f"{init_file} exists but is not a file"

