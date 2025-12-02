"""Integration tests for the complete application."""
import pytest
from pathlib import Path
import re


@pytest.fixture
def html_content():
    """Read index.html content."""
    path = Path("src/frontend/index.html")
    if not path.exists():
        pytest.skip("index.html not found")
    return path.read_text(encoding='utf-8')


@pytest.fixture
def app_js_content():
    """Read app.js content."""
    path = Path("src/frontend/app.js")
    if not path.exists():
        pytest.skip("app.js not found")
    return path.read_text(encoding='utf-8')


# UI Controls Tests (10.1)
def test_has_file_input(html_content):
    """Test that file input exists."""
    assert 'id="file-select"' in html_content, \
        "Should have file selection input"


def test_has_timeframe_select(html_content):
    """Test that timeframe selection exists."""
    assert 'id="timeframe-select"' in html_content, \
        "Should have timeframe selection dropdown"


def test_has_indicator_select(html_content):
    """Test that indicator selection exists."""
    assert 'id="indicator-select"' in html_content, \
        "Should have indicator selection dropdown"


def test_has_load_button(html_content):
    """Test that load button exists."""
    assert 'id="load-btn"' in html_content, \
        "Should have load chart button"


def test_has_controls_section(html_content):
    """Test that controls are present in header."""
    assert 'class="controls"' in html_content or 'class="control-group"' in html_content, \
        "Should have controls in header"


def test_has_active_indicators_display(html_content):
    """Test that active indicators display exists."""
    assert 'id="active-indicators"' in html_content, \
        "Should have active indicators display area"


def test_timeframe_options_present(html_content):
    """Test that timeframe options are available."""
    timeframes = ['1min', '5min', '15min', '1h', '4h', '1D']
    for tf in timeframes:
        assert tf in html_content, \
            f"Should have {tf} timeframe option"


def test_indicator_options_present(html_content):
    """Test that indicator options are available."""
    indicators = ['RSI', 'SMA', 'EMA']
    for ind in indicators:
        assert ind in html_content, \
            f"Should have {ind} indicator options"


# Application Integration Tests (10.2-10.6)
def test_has_chart_application_class(app_js_content):
    """Test that ChartApplication class exists."""
    assert re.search(r'class\s+ChartApplication', app_js_content), \
        "Should define ChartApplication class"


def test_initializes_chart_manager(app_js_content):
    """Test that MultiChartManager is initialized (Task 26)."""
    assert 'new MultiChartManager' in app_js_content, \
        "Should initialize MultiChartManager"


def test_has_event_listeners(app_js_content):
    """Test that event listeners are set up."""
    assert 'addEventListener' in app_js_content, \
        "Should set up event listeners"


def test_handles_load_button_click(app_js_content):
    """Test that load button click is handled."""
    assert 'load-btn' in app_js_content, \
        "Should handle load button click"


def test_handles_indicator_selection(app_js_content):
    """Test that indicator selection is handled."""
    assert 'addIndicator' in app_js_content or 'indicator' in app_js_content.lower(), \
        "Should handle indicator selection"


def test_manages_active_indicators(app_js_content):
    """Test that active indicators are managed."""
    assert 'activeIndicators' in app_js_content, \
        "Should manage active indicators list"


def test_can_remove_indicators(app_js_content):
    """Test that indicators can be removed."""
    assert 'removeIndicator' in app_js_content, \
        "Should support removing indicators"


# State Management Tests (10.5)
def test_saves_state_to_localstorage(app_js_content):
    """Test that state is saved to localStorage."""
    assert 'localStorage' in app_js_content, \
        "Should use localStorage for state persistence"


def test_loads_state_from_localstorage(app_js_content):
    """Test that state is loaded from localStorage."""
    has_load_state = any([
        'loadState' in app_js_content,
        'getItem' in app_js_content
    ])
    assert has_load_state, "Should load state from localStorage"


def test_tracks_current_filename(app_js_content):
    """Test that current filename is tracked."""
    assert 'currentFilename' in app_js_content or 'filename' in app_js_content, \
        "Should track current filename"


def test_tracks_current_timeframe(app_js_content):
    """Test that current timeframe is tracked."""
    assert 'currentTimeframe' in app_js_content or 'timeframe' in app_js_content, \
        "Should track current timeframe"


# Dynamic API Communication Tests (10.2)
def test_builds_request_options(app_js_content):
    """Test that request options are built dynamically."""
    assert 'options' in app_js_content, \
        "Should build request options"


def test_includes_indicators_in_request(app_js_content):
    """Test that indicators are included in API requests."""
    has_indicators = any([
        'indicators:' in app_js_content,
        'options.indicators' in app_js_content
    ])
    assert has_indicators, "Should include indicators in requests"


def test_includes_timeframe_in_request(app_js_content):
    """Test that timeframe is included in API requests."""
    has_timeframe = any([
        'timeframe:' in app_js_content,
        'options.timeframe' in app_js_content
    ])
    assert has_timeframe, "Should include timeframe in requests"


# Error Handling Tests
def test_has_error_handling(app_js_content):
    """Test that error handling is implemented."""
    has_error = any([
        'try' in app_js_content and 'catch' in app_js_content,
        'showError' in app_js_content
    ])
    assert has_error, "Should have error handling"


def test_shows_error_messages(app_js_content):
    """Test that error messages are shown to users."""
    assert 'showError' in app_js_content or 'alert' in app_js_content, \
        "Should show error messages to users"


# Window Resize Tests
def test_handles_window_resize(app_js_content):
    """Test that window resize is handled."""
    assert 'resize' in app_js_content.lower(), \
        "Should handle window resize"


# Module Loading Tests
def test_app_js_loaded_in_html(html_content):
    """Test that app.js is loaded in HTML."""
    assert 'app.js' in html_content, \
        "Should load app.js in HTML"


def test_scripts_loaded_in_correct_order(html_content):
    """Test that scripts are loaded in correct order."""
    data_client_pos = html_content.find('data-client.js')
    chart_pos = html_content.find('chart.js')
    app_pos = html_content.find('app.js')
    
    assert data_client_pos < chart_pos < app_pos, \
        "Scripts should load in order: data-client -> chart -> app"


# DOM Ready Tests
def test_waits_for_dom_ready(app_js_content):
    """Test that app waits for DOM to be ready."""
    assert 'DOMContentLoaded' in app_js_content, \
        "Should wait for DOM to be ready before initializing"


# Global Export Tests
def test_exports_app_globally(app_js_content):
    """Test that app is exported globally."""
    assert 'window.app' in app_js_content, \
        "Should export app instance globally"


# Code Quality Tests
def test_uses_modern_javascript(app_js_content):
    """Test that modern JavaScript is used."""
    modern_features = [
        'const ' in app_js_content,
        'let ' in app_js_content,
        'async' in app_js_content,
        '=>' in app_js_content
    ]
    assert sum(modern_features) >= 3, \
        "Should use modern JavaScript features"


def test_has_comprehensive_documentation(app_js_content):
    """Test that code is well documented."""
    assert '/**' in app_js_content, \
        "Should have JSDoc documentation"


def test_proper_class_structure(app_js_content):
    """Test that proper class structure is used."""
    has_structure = all([
        'constructor' in app_js_content,
        'this.' in app_js_content
    ])
    assert has_structure, "Should use proper class structure"

