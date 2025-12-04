"""Basic import tests for PyCharting package."""

import pytest


def test_package_import():
    """Test that the main package can be imported."""
    import src
    assert src.__version__ == "0.1.0"


def test_core_import():
    """Test that core module can be imported."""
    from src.pycharting import core
    assert core is not None


def test_data_import():
    """Test that data module can be imported."""
    from src.pycharting import data
    assert data is not None


def test_api_import():
    """Test that api module can be imported."""
    from src.pycharting import api
    assert api is not None


def test_web_import():
    """Test that web module can be imported."""
    from src.pycharting import web
    assert web is not None


def test_dependencies_available():
    """Test that core dependencies are available."""
    import pandas
    import numpy
    import fastapi
    import uvicorn
    
    assert pandas is not None
    assert numpy is not None
    assert fastapi is not None
    assert uvicorn is not None
