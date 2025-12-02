"""Tests for frontend HTML structure."""
import pytest
from pathlib import Path
from html.parser import HTMLParser


class HTMLValidator(HTMLParser):
    """Parser to validate HTML structure."""
    
    def __init__(self):
        super().__init__()
        self.tags = []
        self.meta_tags = []
        self.ids = []
        self.has_doctype = False
        
    def handle_starttag(self, tag, attrs):
        """Track opening tags."""
        self.tags.append(tag)
        attrs_dict = dict(attrs)
        
        if tag == 'meta':
            self.meta_tags.append(attrs_dict)
        
        if 'id' in attrs_dict:
            self.ids.append(attrs_dict['id'])
    
    def handle_decl(self, decl):
        """Track doctype declaration."""
        if 'DOCTYPE' in decl.upper():
            self.has_doctype = True


@pytest.fixture
def html_path():
    """Get path to index.html."""
    return Path("src/frontend/index.html")


@pytest.fixture
def html_content(html_path):
    """Read HTML content."""
    if not html_path.exists():
        pytest.skip(f"HTML file not found: {html_path}")
    return html_path.read_text(encoding='utf-8')


def test_html_file_exists():
    """Test that index.html exists."""
    html_path = Path("src/frontend/index.html")
    assert html_path.exists(), "index.html should exist in src/frontend/"


def test_html_has_doctype(html_content):
    """Test that HTML has DOCTYPE declaration."""
    parser = HTMLValidator()
    parser.feed(html_content)
    assert parser.has_doctype, "HTML should have DOCTYPE declaration"


def test_html_basic_structure(html_content):
    """Test that HTML has basic html, head, body structure."""
    parser = HTMLValidator()
    parser.feed(html_content)
    
    assert 'html' in parser.tags, "HTML should have <html> tag"
    assert 'head' in parser.tags, "HTML should have <head> tag"
    assert 'body' in parser.tags, "HTML should have <body> tag"


def test_html_has_meta_charset(html_content):
    """Test that HTML has charset meta tag."""
    parser = HTMLValidator()
    parser.feed(html_content)
    
    charset_found = any(
        meta.get('charset') == 'UTF-8' or 
        meta.get('charset') == 'utf-8'
        for meta in parser.meta_tags
    )
    assert charset_found, "HTML should have UTF-8 charset meta tag"


def test_html_has_viewport_meta(html_content):
    """Test that HTML has viewport meta tag for responsive design."""
    parser = HTMLValidator()
    parser.feed(html_content)
    
    viewport_found = any(
        meta.get('name') == 'viewport'
        for meta in parser.meta_tags
    )
    assert viewport_found, "HTML should have viewport meta tag"


def test_html_has_title(html_content):
    """Test that HTML has title tag."""
    parser = HTMLValidator()
    parser.feed(html_content)
    
    assert 'title' in parser.tags, "HTML should have <title> tag"


def test_html_has_chart_container(html_content):
    """Test that HTML has chart container div."""
    parser = HTMLValidator()
    parser.feed(html_content)
    
    # Should have a chart container with specific ID
    chart_ids = ['chart', 'chart-container', 'uplot-chart']
    has_chart_container = any(id in parser.ids for id in chart_ids)
    assert has_chart_container, f"HTML should have chart container with one of these IDs: {chart_ids}"


def test_html_semantic_structure(html_content):
    """Test that HTML uses semantic HTML5 tags."""
    parser = HTMLValidator()
    parser.feed(html_content)
    
    # Should have at least one semantic tag
    semantic_tags = ['header', 'main', 'section', 'article', 'footer', 'nav']
    has_semantic = any(tag in parser.tags for tag in semantic_tags)
    assert has_semantic, f"HTML should use semantic HTML5 tags like {semantic_tags}"


def test_html_valid_utf8(html_path):
    """Test that HTML is valid UTF-8."""
    try:
        html_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        pytest.fail("HTML file should be valid UTF-8 encoded")


def test_html_not_empty(html_content):
    """Test that HTML file is not empty."""
    assert len(html_content.strip()) > 0, "HTML file should not be empty"


def test_html_has_lang_attribute(html_content):
    """Test that html tag has lang attribute."""
    # Look for lang attribute in html tag
    assert 'lang=' in html_content.lower(), "HTML tag should have lang attribute"

