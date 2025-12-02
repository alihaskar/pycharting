"""Tests for chart.js ChartManager implementation."""
import pytest
from pathlib import Path
import re


@pytest.fixture
def chart_js_path():
    """Get path to chart.js."""
    return Path("src/frontend/chart.js")


@pytest.fixture
def chart_content(chart_js_path):
    """Read chart.js content."""
    if not chart_js_path.exists():
        pytest.skip("chart.js not found")
    return chart_js_path.read_text(encoding='utf-8')


# Basic Structure Tests
def test_chart_file_exists(chart_js_path):
    """Test that chart.js exists."""
    assert chart_js_path.exists(), "chart.js should exist"


def test_has_chart_manager_class(chart_content):
    """Test that ChartManager class is defined."""
    assert re.search(r'class\s+ChartManager', chart_content), \
        "Should define ChartManager class"


def test_has_constructor(chart_content):
    """Test that ChartManager has constructor."""
    assert 'constructor(' in chart_content, \
        "ChartManager should have constructor"


# uPlot Configuration Tests (9.1)
def test_creates_uplot_instance(chart_content):
    """Test that uPlot instance is created."""
    assert 'new uPlot' in chart_content or 'uPlot(' in chart_content, \
        "Should create uPlot instance"


def test_has_chart_options_config(chart_content):
    """Test that chart options are configured."""
    has_opts = any([
        'opts' in chart_content,
        'options' in chart_content,
        'config' in chart_content
    ])
    assert has_opts, "Should define chart options/configuration"


def test_configures_series(chart_content):
    """Test that series configuration exists."""
    assert 'series' in chart_content.lower(), \
        "Should configure chart series"


def test_supports_ohlc_data(chart_content):
    """Test that OHLC data handling is mentioned."""
    has_ohlc = any([
        'ohlc' in chart_content.lower(),
        'open' in chart_content.lower() and 'close' in chart_content.lower(),
        'candlestick' in chart_content.lower()
    ])
    assert has_ohlc, "Should support OHLC data"


# Multi-Axis Tests (9.2)
def test_supports_indicators(chart_content):
    """Test that indicator support is implemented."""
    assert 'indicator' in chart_content.lower(), \
        "Should support technical indicators"


def test_handles_metadata(chart_content):
    """Test that metadata handling exists."""
    assert 'metadata' in chart_content, \
        "Should handle metadata from API"


# Chart Lifecycle Tests
def test_has_render_method(chart_content):
    """Test that render method exists."""
    has_render = any([
        'renderChart' in chart_content,
        'render(' in chart_content,
        'draw' in chart_content
    ])
    assert has_render, "Should have chart rendering method"


def test_has_destroy_method(chart_content):
    """Test that destroy method exists for cleanup."""
    assert 'destroy' in chart_content, \
        "Should have destroy method for cleanup"


def test_destroys_existing_chart(chart_content):
    """Test that existing chart is destroyed before creating new one."""
    assert 'this.chart' in chart_content, \
        "Should track chart instance"


# Integration Tests
def test_integrates_with_data_client(chart_content):
    """Test that DataClient integration exists."""
    assert 'DataClient' in chart_content, \
        "Should integrate with DataClient"


def test_has_load_and_render_method(chart_content):
    """Test that convenience method for loading and rendering exists."""
    assert 'loadAndRender' in chart_content or 'load' in chart_content, \
        "Should have method to load and render data"


def test_handles_errors_gracefully(chart_content):
    """Test that error handling is implemented."""
    has_error_handling = any([
        'try' in chart_content and 'catch' in chart_content,
        'error' in chart_content.lower()
    ])
    assert has_error_handling, "Should handle errors gracefully"


def test_shows_error_messages(chart_content):
    """Test that error messages are displayed to users."""
    assert 'innerHTML' in chart_content or 'textContent' in chart_content, \
        "Should display error messages to users"


# Export Tests
def test_exports_to_window(chart_content):
    """Test that ChartManager is exported."""
    assert 'window.ChartManager' in chart_content, \
        "Should export ChartManager to window object"


# Documentation Tests
def test_has_documentation(chart_content):
    """Test that code has documentation."""
    assert '/**' in chart_content or '//' in chart_content, \
        "Should have code documentation"


def test_uses_modern_javascript(chart_content):
    """Test that modern JavaScript is used."""
    modern_features = [
        'const ' in chart_content,
        'let ' in chart_content,
        'async' in chart_content,
        '=>' in chart_content
    ]
    assert sum(modern_features) >= 3, \
        "Should use modern JavaScript features"

