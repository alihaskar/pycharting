"""
Browser launch utility for opening chart URLs.

Provides cross-platform browser launching with URL validation
and error handling.
"""

import webbrowser
import logging
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)


def validate_url(url: str) -> str:
    """
    Validate that URL is properly formatted and uses HTTP/HTTPS scheme.
    
    Args:
        url: URL string to validate
        
    Returns:
        Validated URL string
        
    Raises:
        ValueError: If URL is invalid or uses unsupported scheme
        
    Examples:
        >>> validate_url("http://localhost:3000")
        'http://localhost:3000'
        >>> validate_url("https://example.com")
        'https://example.com'
    """
    # Strip whitespace
    url = url.strip()
    
    # Check for empty URL
    if not url:
        raise ValueError("URL cannot be empty")
    
    # Check for valid scheme (http or https)
    if not (url.startswith('http://') or url.startswith('https://')):
        raise ValueError("URL must start with http:// or https://")
    
    return url


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid without raising exception.
    
    Args:
        url: URL string to check
        
    Returns:
        True if URL is valid, False otherwise
        
    Examples:
        >>> is_valid_url("http://localhost:3000")
        True
        >>> is_valid_url("ftp://example.com")
        False
    """
    try:
        validate_url(url)
        return True
    except ValueError:
        return False


def launch_browser(url: str, new_window: int = 2) -> bool:
    """
    Launch default browser to the specified URL.
    
    Opens the default web browser to the given URL with proper
    error handling and logging. Works across Windows, macOS, and Linux.
    
    Args:
        url: URL to open in browser
        new_window: Browser window behavior:
            0 = same window/tab
            1 = new window
            2 = new tab (default)
        
    Returns:
        True if browser launched successfully, False otherwise
        
    Raises:
        ValueError: If URL is invalid
        
    Examples:
        >>> launch_browser("http://localhost:3000")
        True
        >>> launch_browser("https://example.com:8080")
        True
    """
    # Validate URL first
    url = validate_url(url)
    
    # Attempt to open browser
    try:
        webbrowser.open(url, new=new_window)
        logger.info(f"Successfully opened browser to {url}")
        return True
    except Exception as e:
        logger.warning(f"Failed to open browser: {e}")
        # Fallback is handled by caller
        return False

