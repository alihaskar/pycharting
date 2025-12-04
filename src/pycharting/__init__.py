"""Public package for the PyCharting library.

This module re-exports the main Python API surface so that users can do:

    from pycharting import plot, stop_server, get_server_status
"""

from typing import Any, Dict  # re-exported types are only for type checkers

from api.interface import plot, stop_server, get_server_status  # type: ignore F401

__all__ = ["plot", "stop_server", "get_server_status", "__version__"]

# Keep this in sync with pyproject.toml
__version__ = "0.2.3"


