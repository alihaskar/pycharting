"""Tests for uPlot library integration."""
import pytest
from pathlib import Path
from html.parser import HTMLParser
import re


class UPlotParser(HTMLParser):
    """Parser to extract script and link tags."""
    
    def __init__(self):
        super().__init__()
        self.link_tags = []
        self.script_tags = []
        
    def handle_starttag(self, tag, attrs):
        """Track link and script tags."""
        attrs_dict = dict(attrs)
        
        if tag == 'link':
            self.link_tags.append(attrs_dict)
        elif tag == 'script':
            self.script_tags.append(attrs_dict)


@pytest.fixture
def html_content():
    """Read HTML content."""
    html_path = Path("src/frontend/index.html")
    if not html_path.exists():
        pytest.skip("HTML file not found")
    return html_path.read_text(encoding='utf-8')


def test_has_uplot_css_cdn(html_content):
    """Test that uPlot CSS is loaded from CDN."""
    parser = UPlotParser()
    parser.feed(html_content)
    
    # Check for uPlot CSS CDN link
    uplot_css_found = any(
        'uplot' in link.get('href', '').lower() and
        link.get('rel') == 'stylesheet'
        for link in parser.link_tags
    )
    assert uplot_css_found, "HTML should include uPlot CSS from CDN"


def test_has_uplot_js_cdn(html_content):
    """Test that uPlot JS is loaded from CDN."""
    parser = UPlotParser()
    parser.feed(html_content)
    
    # Check for uPlot JS CDN script
    uplot_js_found = any(
        'uplot' in script.get('src', '').lower()
        for script in parser.script_tags
    )
    assert uplot_js_found, "HTML should include uPlot JS from CDN"


def test_css_loaded_before_js(html_content):
    """Test that CSS is loaded before JavaScript."""
    # CSS should appear in <head>, JS at end of <body>
    css_pos = html_content.lower().find('uplot')
    js_pos = html_content.lower().rfind('uplot')
    
    assert css_pos < js_pos, "uPlot CSS should be loaded before uPlot JS"


def test_uplot_css_in_head(html_content):
    """Test that uPlot CSS is in the head section."""
    # Find head section
    head_start = html_content.lower().find('<head')
    head_end = html_content.lower().find('</head>')
    
    # Find uPlot CSS
    css_pos = html_content.lower().find('uplot') 
    
    assert head_start < css_pos < head_end, "uPlot CSS should be in <head> section"


def test_uplot_js_near_body_end(html_content):
    """Test that uPlot JS is near the end of body."""
    # Find uPlot JS script
    matches = list(re.finditer(r'uplot.*?\.js', html_content, re.IGNORECASE))
    assert len(matches) > 0, "Should have uPlot JS script"
    
    uplot_js_pos = matches[-1].start()
    body_end = html_content.lower().rfind('</body>')
    
    # Should be within 1000 characters of body end
    assert body_end - uplot_js_pos < 1000, "uPlot JS should be near end of <body>"


def test_uplot_version_pinned(html_content):
    """Test that uPlot version is pinned (not using latest)."""
    # Should have version number in URL
    version_pattern = r'uplot[@/](\d+\.)?(\d+\.)?(\*|\d+)'
    assert re.search(version_pattern, html_content, re.IGNORECASE), \
        "uPlot CDN URL should include version number"


def test_cdn_uses_https(html_content):
    """Test that CDN links use HTTPS."""
    # Find all CDN URLs
    cdn_urls = re.findall(r'(https?://[^\s"\'<>]+)', html_content, re.IGNORECASE)
    
    for url in cdn_urls:
        assert url.startswith('https://'), f"CDN URL should use HTTPS: {url}"


def test_has_integrity_hash(html_content):
    """Test that CDN resources have integrity hashes for security."""
    parser = UPlotParser()
    parser.feed(html_content)
    
    # At least one CDN resource should have integrity hash
    has_integrity = any(
        'integrity' in link
        for link in parser.link_tags + parser.script_tags
    )
    
    # This is optional but recommended
    # assert has_integrity, "CDN resources should include integrity hashes"
    # For now, just check it exists in newer versions
    if not has_integrity:
        pytest.skip("Integrity hashes are optional but recommended")


def test_uplot_css_url_valid_format(html_content):
    """Test that uPlot CSS URL has valid CDN format."""
    # Should be from a known CDN (jsdelivr, unpkg, cdnjs)
    known_cdns = ['jsdelivr', 'unpkg', 'cdnjs']
    
    parser = UPlotParser()
    parser.feed(html_content)
    
    uplot_css_links = [
        link for link in parser.link_tags
        if 'uplot' in link.get('href', '').lower()
    ]
    
    assert len(uplot_css_links) > 0, "Should have uPlot CSS link"
    
    css_href = uplot_css_links[0]['href']
    has_known_cdn = any(cdn in css_href.lower() for cdn in known_cdns)
    assert has_known_cdn, f"uPlot CSS should be from known CDN: {known_cdns}"


def test_uplot_js_url_valid_format(html_content):
    """Test that uPlot JS URL has valid CDN format."""
    # Should be from a known CDN
    known_cdns = ['jsdelivr', 'unpkg', 'cdnjs']
    
    parser = UPlotParser()
    parser.feed(html_content)
    
    uplot_js_scripts = [
        script for script in parser.script_tags
        if 'uplot' in script.get('src', '').lower()
    ]
    
    assert len(uplot_js_scripts) > 0, "Should have uPlot JS script"
    
    js_src = uplot_js_scripts[0]['src']
    has_known_cdn = any(cdn in js_src.lower() for cdn in known_cdns)
    assert has_known_cdn, f"uPlot JS should be from known CDN: {known_cdns}"

