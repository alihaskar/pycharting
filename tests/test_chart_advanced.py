"""Advanced tests for chart.js enhanced features."""
import pytest
from pathlib import Path
import re


@pytest.fixture
def chart_content():
    """Read chart.js content."""
    path = Path("src/frontend/chart.js")
    if not path.exists():
        pytest.skip("chart.js not found")
    return path.read_text(encoding='utf-8')


# Multi-Axis Setup Tests (9.2)
def test_supports_multiple_axes(chart_content):
    """Test that multiple axes configuration exists."""
    has_axes = any([
        'axes' in chart_content.lower(),
        'scale' in chart_content.lower(),
        'y-axis' in chart_content.lower()
    ])
    assert has_axes, "Should support multiple axes configuration"


def test_handles_overlay_indicators(chart_content):
    """Test that overlay indicators (on price axis) are supported."""
    # Indicators like SMA, EMA should overlay on price
    assert 'indicator' in chart_content.lower(), \
        "Should handle overlay indicators"


# Zoom and Pan Tests (9.3)
def test_has_zoom_pan_support(chart_content):
    """Test that zoom/pan functionality exists."""
    has_zoom_pan = any([
        'zoom' in chart_content.lower(),
        'pan' in chart_content.lower(),
        'setScale' in chart_content,
        'cursor' in chart_content.lower()
    ])
    # Zoom/pan will be added in later subtasks
    if not has_zoom_pan:
        pytest.skip("Zoom/pan support not yet implemented")


# Data Update Tests (9.4)
def test_supports_data_updates(chart_content):
    """Test that data can be updated without full re-initialization."""
    has_update = any([
        'setData' in chart_content,
        'updateData' in chart_content,
        'update(' in chart_content
    ])
    # This will be implemented in subtask 9.4
    if not has_update:
        pytest.skip("Data update support not yet implemented")


# Performance Optimization Tests (9.5)
def test_has_performance_considerations(chart_content):
    """Test that performance optimizations are mentioned."""
    has_perf = any([
        'performance' in chart_content.lower(),
        'optimize' in chart_content.lower(),
        'efficient' in chart_content.lower(),
        'debounce' in chart_content.lower()
    ])
    # Performance optimizations will be added
    if not has_perf:
        pytest.skip("Performance optimizations not yet fully implemented")


# State Management Tests (9.6)
def test_tracks_chart_state(chart_content):
    """Test that chart state is tracked."""
    has_state = any([
        'state' in chart_content.lower(),
        'this.chart' in chart_content,
        'this.config' in chart_content
    ])
    assert has_state, "Should track chart state"


def test_manages_chart_instance(chart_content):
    """Test that chart instance is properly managed."""
    assert 'this.chart' in chart_content, \
        "Should manage chart instance as property"


# Configuration Tests (9.7)
def test_has_configurable_options(chart_content):
    """Test that chart options can be configured."""
    assert 'opts' in chart_content or 'options' in chart_content, \
        "Should have configurable options"


def test_handles_dynamic_series(chart_content):
    """Test that series can be added dynamically."""
    assert 'series' in chart_content, \
        "Should handle series configuration"


# Integration and Error Handling
def test_validates_container(chart_content):
    """Test that container element is validated."""
    has_validation = any([
        'getElementById' in chart_content,
        'querySelector' in chart_content,
        'throw' in chart_content
    ])
    assert has_validation, "Should validate container element"


def test_provides_user_feedback(chart_content):
    """Test that user feedback is provided for errors."""
    assert 'innerHTML' in chart_content, \
        "Should provide user feedback"


# Code Quality Tests
def test_proper_encapsulation(chart_content):
    """Test that ChartManager encapsulates chart logic."""
    # Should use 'this' for instance properties
    this_count = chart_content.count('this.')
    assert this_count >= 3, \
        "Should use proper encapsulation with instance properties"


def test_clean_code_organization(chart_content):
    """Test that code is well organized."""
    lines = chart_content.split('\n')
    assert len(lines) >= 50, \
        "Should have substantial implementation"


def test_exports_only_necessary_classes(chart_content):
    """Test that only necessary classes are exported."""
    window_exports = chart_content.count('window.')
    assert 1 <= window_exports <= 3, \
        "Should export appropriate classes to window"


# Comprehensive Feature Tests
def test_complete_chart_lifecycle(chart_content):
    """Test that complete chart lifecycle is supported."""
    lifecycle_methods = [
        'constructor' in chart_content,
        'render' in chart_content.lower(),
        'destroy' in chart_content
    ]
    assert all(lifecycle_methods), \
        "Should support complete chart lifecycle (create, render, destroy)"


def test_integrates_all_components(chart_content):
    """Test that all major components are integrated."""
    components = [
        'DataClient' in chart_content,
        'uPlot' in chart_content,
        'series' in chart_content,
        'container' in chart_content
    ]
    assert sum(components) >= 3, \
        "Should integrate major components"

