"""PyCharting - A Python library for interactive charting and data visualization."""

__version__ = "0.1.0"

# Import main API functions
from src.api.interface import plot, stop_server, get_server_status

# Export public API
__all__ = ['plot', 'stop_server', 'get_server_status', '__version__']
