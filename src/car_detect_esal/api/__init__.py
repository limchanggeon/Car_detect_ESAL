"""
API module for external services
"""

try:
    from .ntis_client import get_cctv_list, NtisFetchWorker
    from .cctv_api import get_cctv_list as api_get_cctv_list
except ImportError:
    # Handle import errors gracefully
    pass

__all__ = [
    "get_cctv_list",
    "NtisFetchWorker",
    "api_get_cctv_list",
]