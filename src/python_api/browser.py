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


def launch_browser_with_fallback(url: str, new_window: int = 2) -> bool:
    """
    Launch browser with automatic fallback to printing URL.
    
    Attempts to open the browser automatically, and if that fails,
    prints the URL to the console for manual opening.
    
    Args:
        url: URL to open in browser
        new_window: Browser window behavior (0=same, 1=new window, 2=new tab)
        
    Returns:
        True if browser launched successfully, False if fallback was used
        
    Raises:
        ValueError: If URL is invalid
        
    Examples:
        >>> launch_browser_with_fallback("http://localhost:3000")
        True
        >>> # If browser fails, prints: "Please open your browser to: http://localhost:3000"
    """
    # Validate URL first (raises ValueError if invalid)
    url = validate_url(url)
    
    # Try to launch browser
    success = launch_browser(url, new_window)
    
    # If launch failed, print URL as fallback
    if not success:
        print(f"\n📊 Please open your browser to: {url}\n")
    
    return success

