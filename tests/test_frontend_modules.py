"""Tests for JavaScript module loading configuration."""
import pytest
from pathlib import Path
from html.parser import HTMLParser
import re


class ScriptParser(HTMLParser):
    """Parser to extract script tags and their order."""
    
    def __init__(self):
        super().__init__()
        self.scripts = []
        
    def handle_starttag(self, tag, attrs):
        """Track script tags with their position."""
        if tag == 'script':
            attrs_dict = dict(attrs)
            self.scripts.append(attrs_dict)


@pytest.fixture
def html_content():
    """Read HTML content."""
    html_path = Path("src/frontend/index.html")
    if not html_path.exists():
        pytest.skip("HTML file not found")
    return html_path.read_text(encoding='utf-8')


def test_has_data_client_js(html_content):
    """Test that data-client.js is referenced."""
    assert 'data-client.js' in html_content, "HTML should reference data-client.js"


def test_has_chart_js(html_content):
    """Test that chart.js is referenced."""
    assert 'chart.js' in html_content, "HTML should reference chart.js"


def test_data_client_loaded_before_chart(html_content):
    """Test that data-client.js is loaded before chart.js."""
    data_client_pos = html_content.find('data-client.js')
    chart_pos = html_content.find('chart.js')
    
    assert data_client_pos > 0, "data-client.js should be in HTML"
    assert chart_pos > 0, "chart.js should be in HTML"
    assert data_client_pos < chart_pos, "data-client.js should be loaded before chart.js"


def test_modules_loaded_after_uplot(html_content):
    """Test that custom modules are loaded after uPlot."""
    uplot_pos = html_content.rfind('uPlot')
    data_client_pos = html_content.find('data-client.js')
    
    assert uplot_pos > 0, "uPlot should be in HTML"
    assert data_client_pos > uplot_pos, "Custom modules should be loaded after uPlot"


def test_script_tags_have_defer_or_position(html_content):
    """Test that scripts use defer or are positioned correctly (end of body)."""
    # Scripts should either have defer attribute or be at end of body
    body_end = html_content.lower().rfind('</body>')
    data_client_pos = html_content.find('data-client.js')
    
    # Should be within 500 characters of body end
    distance = body_end - data_client_pos
    assert distance < 500, "Scripts should be near end of body or use defer"


def test_js_files_exist():
    """Test that JavaScript module files exist."""
    data_client_path = Path("src/frontend/data-client.js")
    chart_path = Path("src/frontend/chart.js")
    
    assert data_client_path.exists(), "data-client.js should exist"
    assert chart_path.exists(), "chart.js should exist"


def test_js_files_not_empty():
    """Test that JavaScript files are not empty."""
    data_client_path = Path("src/frontend/data-client.js")
    chart_path = Path("src/frontend/chart.js")
    
    if not (data_client_path.exists() and chart_path.exists()):
        pytest.skip("JS files not yet created")
    
    data_client_content = data_client_path.read_text(encoding='utf-8')
    chart_content = chart_path.read_text(encoding='utf-8')
    
    assert len(data_client_content.strip()) > 0, "data-client.js should not be empty"
    assert len(chart_content.strip()) > 0, "chart.js should not be empty"


def test_modules_use_relative_paths(html_content):
    """Test that module paths are relative (not absolute)."""
    # Should use relative paths like ./data-client.js or data-client.js
    assert not re.search(r'https?://.*data-client\.js', html_content), \
        "data-client.js should use relative path, not CDN"
    assert not re.search(r'https?://.*chart\.js', html_content), \
        "chart.js should use relative path, not CDN (avoid confusion with Chart.js library)"


def test_script_loading_order_complete(html_content):
    """Test complete script loading order: uPlot, data-client, chart."""
    # Find positions
    uplot_pos = html_content.find('uPlot.iife.min.js')
    data_client_pos = html_content.find('data-client.js')
    chart_pos = html_content.find('chart.js')
    
    assert uplot_pos < data_client_pos < chart_pos, \
        "Loading order should be: uPlot -> data-client -> chart"


def test_script_tags_syntax_valid(html_content):
    """Test that script tags have valid syntax."""
    # Should have opening and closing script tags for each module
    assert '<script' in html_content.lower()
    assert '</script>' in html_content.lower()
    
    # Count script tags (should have at least 3: uPlot, data-client, chart)
    script_count = html_content.lower().count('<script')
    assert script_count >= 3, f"Should have at least 3 script tags, found {script_count}"

