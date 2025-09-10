"""
Car Detection ESAL (Equivalent Single Axle Load) Analysis System

A comprehensive system for vehicle detection and pavement load analysis
using YOLOv8 and ESAL-based maintenance scheduling.
"""

__version__ = "1.0.0"
__author__ = "Car Detection ESAL Team"
__email__ = "contact@example.com"

try:
    from .core.config import Config
    from .core.detector import VehicleDetector
    from .core.esal_calculator import ESALCalculator
except ImportError:
    # Handle import errors gracefully
    pass

__all__ = [
    "Config",
    "VehicleDetector", 
    "ESALCalculator",
]