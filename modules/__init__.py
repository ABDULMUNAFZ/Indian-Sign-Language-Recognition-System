"""
ISL Recognition System - Core Modules

BIS Compliance:
- IS 13252: IT Equipment Safety
- IS 16333: Camera-based Systems (Ready)
"""

from .hand_detector import HandDetector
from .gesture_recognizer import GestureRecognizer
from .sentence_former import SentenceFormer
from .tts_engine import TTSEngine
from .logger import SessionLogger

# BIS Compliance Module
try:
    from .bis_compliance import (
        SafetyMonitor,
        ResourceManager,
        CameraSystemSafety,
        InputValidator,
        DataIntegrityManager,
        get_compliance_info,
        generate_compliance_report
    )
    BIS_COMPLIANCE_AVAILABLE = True
except ImportError:
    BIS_COMPLIANCE_AVAILABLE = False

__all__ = [
    'HandDetector',
    'GestureRecognizer', 
    'SentenceFormer',
    'TTSEngine',
    'SessionLogger',
    # BIS Compliance
    'SafetyMonitor',
    'ResourceManager',
    'CameraSystemSafety',
    'InputValidator',
    'DataIntegrityManager',
    'get_compliance_info',
    'generate_compliance_report',
    'BIS_COMPLIANCE_AVAILABLE'
]

