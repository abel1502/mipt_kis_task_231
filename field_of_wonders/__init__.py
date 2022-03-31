"""
The module housing the implementation of the Field of Wonders game
"""

from .server import run_server
from .client import run_client


__all__ = ("run_client", "run_server")
