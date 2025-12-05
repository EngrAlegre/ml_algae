"""
AMLAC Robot System
Automated Machine Learning Algae Collector

A complete Python system for autonomous algae detection and collection
using Raspberry Pi 5, machine learning, and multiple sensors.

Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "AMLAC Development Team"
__description__ = "Automated Machine Learning Algae Collector Robot System"

# Module exports
from .main import AMLACRobot
from .core.motors import MotorController
from .core.ml_inference import AlgaeDetector
from .core.data_logger import DataLogger
from .core.display import LCDDisplay

__all__ = [
    'AMLACRobot',
    'MotorController',
    'AlgaeDetector',
    'DataLogger',
    'LCDDisplay'
]

