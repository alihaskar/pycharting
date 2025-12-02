"""
Server utilities for local HTTP server management.

Provides port management and server lifecycle utilities for the
Python API's local server functionality.
"""

import socket
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def find_available_port(preferred_port: int = 8000, max_attempts: int = 10) -> int:
    """
    Find an available port for the local server.
    
    Tries to bind to the preferred port first. If occupied, tries
    sequential ports until an available one is found.
    
    Args:
        preferred_port: First port to try (default: 8000)
        max_attempts: Maximum number of ports to try (default: 10)
        
    Returns:
        Available port number
        
    Raises:
        RuntimeError: If no available ports found in the range
        
    Examples:
        >>> port = find_available_port()
        >>> port >= 8000
        True
        >>> port = find_available_port(preferred_port=9000, max_attempts=5)
        >>> port >= 9000
        True
    """
    for port in range(preferred_port, preferred_port + max_attempts):
        try:
            # Try to bind to the port
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                # If binding succeeds, port is available
                logger.info(f"Found available port: {port}")
                return port
        except OSError as e:
            # Port is occupied or binding failed
            logger.debug(f"Port {port} unavailable: {e}")
            continue
    
    # No available ports found in range
    end_port = preferred_port + max_attempts - 1
    raise RuntimeError(
        f"No available ports found in range {preferred_port}-{end_port}. "
        f"All {max_attempts} ports are occupied."
    )

