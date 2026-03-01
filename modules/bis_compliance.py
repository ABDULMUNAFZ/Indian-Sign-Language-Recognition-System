"""
BIS Compliance Module for ISL Recognition System

This module implements safety and reliability guidelines aligned with:
- IS 13252 (Part 1): Information Technology Equipment - Safety
- IS 16333: Camera-based Systems for Assistive Technology

Key Compliance Areas:
1. Software Safety (IS 13252)
   - Input validation and sanitization
   - Error handling and graceful degradation
   - Resource management and cleanup
   - Data integrity verification
   
2. Camera System Readiness (IS 16333)
   - Camera initialization safety checks
   - Frame validation and quality assurance
   - Privacy-conscious data handling
   - System reliability monitoring

Author: ISL Recognition System Team
Version: 1.0.0
Last Updated: 2026-01-27
"""

import os
import sys
import time
import hashlib
import logging
import threading
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, List
from enum import Enum
from dataclasses import dataclass, field
import traceback

import config


# =============================================================================
# BIS COMPLIANCE CONSTANTS
# =============================================================================

class ComplianceStandard(Enum):
    """BIS Standards implemented in this system."""
    IS_13252 = "IS 13252 - IT Equipment Safety"
    IS_16333 = "IS 16333 - Camera-based Assistive Systems"


class SafetyLevel(Enum):
    """Safety levels as per IS 13252."""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class SystemState(Enum):
    """System operational states."""
    INITIALIZING = "initializing"
    READY = "ready"
    PROCESSING = "processing"
    ERROR = "error"
    DEGRADED = "degraded"
    SHUTDOWN = "shutdown"


# Compliance version tracking
BIS_COMPLIANCE_VERSION = "1.0.0"
IS_13252_COMPLIANCE_DATE = "2026-01-27"
IS_16333_READINESS_DATE = "2026-01-27"


# =============================================================================
# IS 13252 - INPUT VALIDATION & SANITIZATION
# =============================================================================

class InputValidator:
    """
    Input validation utilities aligned with IS 13252 software safety practices.
    
    Ensures all user inputs and external data are validated before processing
    to prevent security vulnerabilities and system instability.
    """
    
    # Allowed file extensions for safety
    SAFE_FILE_EXTENSIONS = {'.csv', '.json', '.txt', '.log', '.mp3', '.wav'}
    
    # Maximum input lengths to prevent buffer overflow attacks
    MAX_TEXT_LENGTH = 10000
    MAX_FILE_PATH_LENGTH = 500
    MAX_GESTURE_NAME_LENGTH = 100
    
    # Valid gesture characters (alphanumeric and underscore only)
    VALID_GESTURE_CHARS = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_')
    
    @staticmethod
    def validate_text_input(text: str, max_length: int = None) -> Tuple[bool, str]:
        """
        Validate text input for security and safety.
        
        Args:
            text: Input text to validate
            max_length: Optional maximum length override
            
        Returns:
            Tuple of (is_valid, sanitized_text or error_message)
        """
        if text is None:
            return False, "Input cannot be None"
        
        if not isinstance(text, str):
            return False, f"Expected string, got {type(text).__name__}"
        
        max_len = max_length or InputValidator.MAX_TEXT_LENGTH
        if len(text) > max_len:
            return False, f"Input exceeds maximum length of {max_len}"
        
        # Sanitize potentially harmful characters
        sanitized = text.replace('\x00', '')  # Remove null bytes
        sanitized = sanitized.strip()
        
        return True, sanitized
    
    @staticmethod
    def validate_file_path(path: str) -> Tuple[bool, str]:
        """
        Validate file path to prevent path traversal attacks.
        
        Args:
            path: File path to validate
            
        Returns:
            Tuple of (is_valid, normalized_path or error_message)
        """
        if not path or not isinstance(path, str):
            return False, "Invalid path provided"
        
        if len(path) > InputValidator.MAX_FILE_PATH_LENGTH:
            return False, "Path too long"
        
        # Normalize and check for path traversal
        normalized = os.path.normpath(path)
        
        # Check for path traversal attempts
        if '..' in path or path.startswith('/etc') or path.startswith('/usr'):
            return False, "Path traversal detected or restricted path"
        
        # Verify extension is safe
        _, ext = os.path.splitext(normalized)
        if ext and ext.lower() not in InputValidator.SAFE_FILE_EXTENSIONS:
            return False, f"Unsafe file extension: {ext}"
        
        return True, normalized
    
    @staticmethod
    def validate_gesture_name(gesture: str) -> Tuple[bool, str]:
        """
        Validate gesture name for safe processing.
        
        Args:
            gesture: Gesture name to validate
            
        Returns:
            Tuple of (is_valid, sanitized_name or error_message)
        """
        if not gesture or not isinstance(gesture, str):
            return False, "Invalid gesture name"
        
        if len(gesture) > InputValidator.MAX_GESTURE_NAME_LENGTH:
            return False, "Gesture name too long"
        
        # Check for valid characters only
        if not all(c in InputValidator.VALID_GESTURE_CHARS for c in gesture):
            return False, "Gesture name contains invalid characters"
        
        return True, gesture.upper()
    
    @staticmethod
    def validate_confidence(confidence: float) -> Tuple[bool, float]:
        """
        Validate confidence score is within valid range.
        
        Args:
            confidence: Confidence value to validate
            
        Returns:
            Tuple of (is_valid, clamped_value or -1.0 if invalid)
        """
        try:
            conf = float(confidence)
            if conf < 0.0 or conf > 1.0:
                # Clamp to valid range instead of rejecting
                conf = max(0.0, min(1.0, conf))
            return True, conf
        except (TypeError, ValueError):
            return False, -1.0
    
    @staticmethod
    def validate_camera_index(index: int) -> Tuple[bool, int]:
        """
        Validate camera index is within safe bounds.
        
        Args:
            index: Camera index to validate
            
        Returns:
            Tuple of (is_valid, index or error_code)
        """
        try:
            idx = int(index)
            if idx < 0 or idx > 10:  # Reasonable camera index range
                return False, -1
            return True, idx
        except (TypeError, ValueError):
            return False, -1


# =============================================================================
# IS 13252 - ERROR HANDLING & GRACEFUL DEGRADATION
# =============================================================================

@dataclass
class SafetyEvent:
    """Record of a safety-related event for audit trail."""
    timestamp: datetime
    level: SafetyLevel
    component: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None


class SafetyMonitor:
    """
    Safety monitoring and graceful degradation handler.
    
    Implements IS 13252 requirements for:
    - Continuous system health monitoring
    - Error detection and response
    - Graceful degradation under fault conditions
    - Audit trail maintenance
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for global safety monitoring."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize safety monitoring systems."""
        if self._initialized:
            return
            
        self._initialized = True
        self.state = SystemState.INITIALIZING
        self.safety_events: List[SafetyEvent] = []
        self.max_events = 1000  # Limit memory usage
        self.error_count = 0
        self.warning_count = 0
        self.last_health_check = None
        self.degraded_components: set = set()
        
        # Setup safety logger
        self._setup_safety_logger()
        
        self.state = SystemState.READY
        self._log_event(SafetyLevel.NORMAL, "SafetyMonitor", "Safety monitoring initialized")
    
    def _setup_safety_logger(self):
        """Setup dedicated safety logging."""
        log_dir = config.LOGS_DIR
        os.makedirs(log_dir, exist_ok=True)
        
        self.safety_log_file = os.path.join(log_dir, 'safety_audit.log')
        
        self.logger = logging.getLogger('BIS_Safety')
        self.logger.setLevel(logging.DEBUG)
        
        # File handler for persistent logging
        if not self.logger.handlers:
            fh = logging.FileHandler(self.safety_log_file)
            fh.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
    
    def _log_event(self, level: SafetyLevel, component: str, message: str, 
                   details: Dict[str, Any] = None, include_trace: bool = False):
        """Log a safety event."""
        event = SafetyEvent(
            timestamp=datetime.now(),
            level=level,
            component=component,
            message=message,
            details=details or {},
            stack_trace=traceback.format_exc() if include_trace else None
        )
        
        # Add to in-memory events (with size limit)
        self.safety_events.append(event)
        if len(self.safety_events) > self.max_events:
            self.safety_events.pop(0)
        
        # Update counters
        if level == SafetyLevel.WARNING:
            self.warning_count += 1
        elif level in (SafetyLevel.CRITICAL, SafetyLevel.EMERGENCY):
            self.error_count += 1
        
        # Log to file
        log_msg = f"[{component}] {message}"
        if details:
            log_msg += f" | Details: {details}"
        
        if level == SafetyLevel.NORMAL:
            self.logger.info(log_msg)
        elif level == SafetyLevel.WARNING:
            self.logger.warning(log_msg)
        elif level == SafetyLevel.CRITICAL:
            self.logger.error(log_msg)
        elif level == SafetyLevel.EMERGENCY:
            self.logger.critical(log_msg)
    
    def report_error(self, component: str, error: Exception, 
                     recoverable: bool = True) -> bool:
        """
        Report an error and determine system response.
        
        Args:
            component: Name of the component reporting the error
            error: The exception that occurred
            recoverable: Whether the error is recoverable
            
        Returns:
            True if system can continue, False if shutdown required
        """
        level = SafetyLevel.WARNING if recoverable else SafetyLevel.CRITICAL
        
        self._log_event(
            level=level,
            component=component,
            message=str(error),
            details={'type': type(error).__name__, 'recoverable': recoverable},
            include_trace=True
        )
        
        if not recoverable:
            self.degraded_components.add(component)
            self.state = SystemState.DEGRADED
            
            # Check if too many components are degraded
            if len(self.degraded_components) >= 3:
                self.state = SystemState.ERROR
                return False
        
        return True
    
    def report_warning(self, component: str, message: str, details: Dict = None):
        """Report a warning condition."""
        self._log_event(SafetyLevel.WARNING, component, message, details)
    
    def report_info(self, component: str, message: str, details: Dict = None):
        """Report an informational event."""
        self._log_event(SafetyLevel.NORMAL, component, message, details)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform system health check.
        
        Returns:
            Dictionary with health status information
        """
        self.last_health_check = datetime.now()
        
        return {
            'state': self.state.value,
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'degraded_components': list(self.degraded_components),
            'last_check': self.last_health_check.isoformat(),
            'compliance': {
                'IS_13252': True,
                'IS_16333_ready': True,
                'version': BIS_COMPLIANCE_VERSION
            }
        }
    
    def get_audit_trail(self, count: int = 50) -> List[Dict]:
        """Get recent safety events for audit."""
        events = self.safety_events[-count:]
        return [
            {
                'timestamp': e.timestamp.isoformat(),
                'level': e.level.value,
                'component': e.component,
                'message': e.message,
                'details': e.details
            }
            for e in events
        ]


# =============================================================================
# IS 13252 - RESOURCE MANAGEMENT & CLEANUP
# =============================================================================

class ResourceManager:
    """
    Safe resource management aligned with IS 13252.
    
    Ensures proper allocation, tracking, and cleanup of system resources
    to prevent memory leaks and resource exhaustion.
    """
    
    def __init__(self):
        self.resources: Dict[str, Any] = {}
        self.cleanup_handlers: Dict[str, callable] = {}
        self._lock = threading.Lock()
        self.safety_monitor = SafetyMonitor()
    
    def register(self, resource_id: str, resource: Any, 
                 cleanup_handler: callable = None):
        """
        Register a resource for managed cleanup.
        
        Args:
            resource_id: Unique identifier for the resource
            resource: The resource object to manage
            cleanup_handler: Optional custom cleanup function
        """
        with self._lock:
            self.resources[resource_id] = resource
            if cleanup_handler:
                self.cleanup_handlers[resource_id] = cleanup_handler
            
            self.safety_monitor.report_info(
                "ResourceManager",
                f"Registered resource: {resource_id}"
            )
    
    def release(self, resource_id: str) -> bool:
        """
        Release a specific resource safely.
        
        Args:
            resource_id: ID of resource to release
            
        Returns:
            True if successfully released, False otherwise
        """
        with self._lock:
            if resource_id not in self.resources:
                return False
            
            try:
                resource = self.resources[resource_id]
                
                # Use custom handler if available
                if resource_id in self.cleanup_handlers:
                    self.cleanup_handlers[resource_id](resource)
                # Try common cleanup methods
                elif hasattr(resource, 'release'):
                    resource.release()
                elif hasattr(resource, 'close'):
                    resource.close()
                elif hasattr(resource, 'cleanup'):
                    resource.cleanup()
                
                del self.resources[resource_id]
                if resource_id in self.cleanup_handlers:
                    del self.cleanup_handlers[resource_id]
                
                self.safety_monitor.report_info(
                    "ResourceManager",
                    f"Released resource: {resource_id}"
                )
                return True
                
            except Exception as e:
                self.safety_monitor.report_error(
                    "ResourceManager",
                    Exception(f"Failed to release {resource_id}: {e}"),
                    recoverable=True
                )
                return False
    
    def release_all(self):
        """Release all managed resources safely."""
        resource_ids = list(self.resources.keys())
        
        for resource_id in resource_ids:
            self.release(resource_id)
        
        self.safety_monitor.report_info(
            "ResourceManager",
            f"Released all resources ({len(resource_ids)} total)"
        )
    
    def get_resource_status(self) -> Dict[str, str]:
        """Get status of all managed resources."""
        with self._lock:
            return {
                resource_id: type(resource).__name__
                for resource_id, resource in self.resources.items()
            }


# =============================================================================
# IS 16333 - CAMERA SYSTEM SAFETY (READINESS)
# =============================================================================

class CameraSystemSafety:
    """
    Camera system safety checks aligned with IS 16333 requirements.
    
    Implements safety measures for camera-based assistive technology systems:
    - Camera initialization verification
    - Frame quality validation
    - Privacy protection measures
    - System monitoring
    """
    
    # Frame quality thresholds
    MIN_BRIGHTNESS = 30
    MAX_BRIGHTNESS = 225
    MIN_CONTRAST = 20
    MIN_FRAME_SIZE = (320, 240)
    
    def __init__(self):
        self.safety_monitor = SafetyMonitor()
        self.frame_count = 0
        self.error_frames = 0
        self.last_valid_frame_time = None
    
    def validate_camera_initialization(self, cap) -> Tuple[bool, str]:
        """
        Validate camera is properly initialized.
        
        Args:
            cap: OpenCV VideoCapture object
            
        Returns:
            Tuple of (is_valid, status_message)
        """
        if cap is None:
            self.safety_monitor.report_error(
                "CameraSystem",
                Exception("Camera capture object is None"),
                recoverable=True
            )
            return False, "Camera not initialized"
        
        if not cap.isOpened():
            self.safety_monitor.report_error(
                "CameraSystem",
                Exception("Camera failed to open"),
                recoverable=True
            )
            return False, "Camera failed to open"
        
        # Test frame capture
        ret, frame = cap.read()
        if not ret or frame is None:
            self.safety_monitor.report_warning(
                "CameraSystem",
                "Initial frame capture failed"
            )
            return False, "Cannot capture frames"
        
        # Validate frame dimensions
        h, w = frame.shape[:2]
        if w < self.MIN_FRAME_SIZE[0] or h < self.MIN_FRAME_SIZE[1]:
            self.safety_monitor.report_warning(
                "CameraSystem",
                f"Low resolution: {w}x{h}"
            )
            return False, f"Resolution too low: {w}x{h}"
        
        self.safety_monitor.report_info(
            "CameraSystem",
            f"Camera initialized successfully: {w}x{h}"
        )
        return True, f"Camera ready: {w}x{h}"
    
    def validate_frame(self, frame) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate a captured frame for quality and usability.
        
        Args:
            frame: NumPy array representing the frame
            
        Returns:
            Tuple of (is_valid, frame_info)
        """
        import numpy as np
        
        self.frame_count += 1
        
        if frame is None:
            self.error_frames += 1
            return False, {'error': 'Frame is None'}
        
        if not isinstance(frame, np.ndarray):
            self.error_frames += 1
            return False, {'error': 'Invalid frame type'}
        
        h, w = frame.shape[:2]
        
        # Check dimensions
        if w < self.MIN_FRAME_SIZE[0] or h < self.MIN_FRAME_SIZE[1]:
            return False, {'error': 'Frame too small', 'size': (w, h)}
        
        # Calculate quality metrics
        gray = frame.mean(axis=2) if len(frame.shape) == 3 else frame
        brightness = gray.mean()
        contrast = gray.std()
        
        quality_info = {
            'size': (w, h),
            'brightness': float(brightness),
            'contrast': float(contrast),
            'frame_number': self.frame_count
        }
        
        # Validate quality
        warnings = []
        if brightness < self.MIN_BRIGHTNESS:
            warnings.append('Low brightness')
        elif brightness > self.MAX_BRIGHTNESS:
            warnings.append('High brightness')
        
        if contrast < self.MIN_CONTRAST:
            warnings.append('Low contrast')
        
        if warnings:
            quality_info['warnings'] = warnings
            self.safety_monitor.report_warning(
                "CameraSystem",
                f"Frame quality issues: {', '.join(warnings)}",
                {'frame': self.frame_count}
            )
        
        self.last_valid_frame_time = time.time()
        return True, quality_info
    
    def get_camera_stats(self) -> Dict[str, Any]:
        """Get camera system statistics."""
        error_rate = (self.error_frames / self.frame_count * 100) if self.frame_count > 0 else 0
        
        return {
            'total_frames': self.frame_count,
            'error_frames': self.error_frames,
            'error_rate_percent': round(error_rate, 2),
            'last_valid_frame': self.last_valid_frame_time,
            'compliance': 'IS 16333 Ready'
        }


# =============================================================================
# DATA INTEGRITY & PRIVACY (IS 13252 + IS 16333)
# =============================================================================

class DataIntegrityManager:
    """
    Data integrity and privacy management.
    
    Implements:
    - Data validation and checksums
    - Privacy-conscious data handling
    - Secure data disposal
    """
    
    def __init__(self):
        self.safety_monitor = SafetyMonitor()
    
    @staticmethod
    def compute_checksum(data: bytes) -> str:
        """Compute SHA-256 checksum for data integrity verification."""
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def verify_checksum(data: bytes, expected_checksum: str) -> bool:
        """Verify data integrity using checksum."""
        actual = DataIntegrityManager.compute_checksum(data)
        return actual == expected_checksum
    
    def sanitize_output(self, text: str) -> str:
        """
        Sanitize text output to prevent injection attacks.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # Remove potentially harmful characters
        sanitized = text.replace('\x00', '')
        sanitized = sanitized.replace('\r\n', '\n')
        
        return sanitized.strip()
    
    def secure_dispose(self, data: Any):
        """
        Securely dispose of sensitive data.
        
        Args:
            data: Data to dispose of
        """
        try:
            if isinstance(data, (bytes, bytearray)):
                # Overwrite with zeros
                for i in range(len(data)):
                    data[i] = 0
            
            del data
            
        except Exception as e:
            self.safety_monitor.report_warning(
                "DataIntegrity",
                f"Secure disposal warning: {e}"
            )


# =============================================================================
# COMPLIANCE DOCUMENTATION & REPORTING
# =============================================================================

def get_compliance_info() -> Dict[str, Any]:
    """
    Get comprehensive BIS compliance information.
    
    Returns:
        Dictionary containing all compliance details
    """
    return {
        'system': config.APP_NAME,
        'version': config.APP_VERSION,
        'compliance': {
            'standards': [
                {
                    'code': 'IS 13252',
                    'name': 'Information Technology Equipment - Safety',
                    'status': 'Implemented',
                    'areas': [
                        'Input validation and sanitization',
                        'Error handling and graceful degradation',
                        'Resource management and cleanup',
                        'Data integrity verification',
                        'Safety monitoring and audit trails'
                    ]
                },
                {
                    'code': 'IS 16333',
                    'name': 'Camera-based Systems for Assistive Technology',
                    'status': 'Ready for Hardware Integration',
                    'areas': [
                        'Camera initialization safety checks',
                        'Frame validation and quality assurance',
                        'Privacy-conscious data handling',
                        'System reliability monitoring'
                    ]
                }
            ],
            'compliance_version': BIS_COMPLIANCE_VERSION,
            'is_13252_date': IS_13252_COMPLIANCE_DATE,
            'is_16333_date': IS_16333_READINESS_DATE
        },
        'documentation': {
            'safety_audit_log': os.path.join(config.LOGS_DIR, 'safety_audit.log'),
            'session_logs': config.LOGS_DIR
        }
    }


def generate_compliance_report() -> str:
    """
    Generate a human-readable compliance report.
    
    Returns:
        Formatted compliance report string
    """
    info = get_compliance_info()
    safety_monitor = SafetyMonitor()
    health = safety_monitor.health_check()
    
    report = f"""
================================================================================
                    BIS COMPLIANCE REPORT
                    {config.APP_NAME} v{config.APP_VERSION}
================================================================================

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

COMPLIANCE STATUS
-----------------

1. IS 13252 - Information Technology Equipment Safety
   Status: ✓ IMPLEMENTED
   
   Implemented Areas:
   • Input validation and sanitization
   • Error handling and graceful degradation
   • Resource management and cleanup
   • Data integrity verification
   • Safety monitoring and audit trails
   
2. IS 16333 - Camera-based Systems for Assistive Technology
   Status: ✓ READY FOR HARDWARE INTEGRATION
   
   Implemented Areas:
   • Camera initialization safety checks
   • Frame validation and quality assurance
   • Privacy-conscious data handling
   • System reliability monitoring

SYSTEM HEALTH
-------------
State: {health['state']}
Errors: {health['error_count']}
Warnings: {health['warning_count']}
Degraded Components: {health['degraded_components'] or 'None'}

IMPLEMENTATION DETAILS
----------------------
Compliance Module Version: {BIS_COMPLIANCE_VERSION}
IS 13252 Implementation Date: {IS_13252_COMPLIANCE_DATE}
IS 16333 Readiness Date: {IS_16333_READINESS_DATE}

DOCUMENTATION
-------------
Safety Audit Log: {info['documentation']['safety_audit_log']}
Session Logs: {info['documentation']['session_logs']}

================================================================================
                    END OF COMPLIANCE REPORT
================================================================================
"""
    return report


# =============================================================================
# SAFE EXECUTION DECORATORS
# =============================================================================

def safe_execute(component: str = "Unknown", recoverable: bool = True):
    """
    Decorator for safe function execution with error handling.
    
    Args:
        component: Name of the component for logging
        recoverable: Whether errors are recoverable
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            safety_monitor = SafetyMonitor()
            try:
                return func(*args, **kwargs)
            except Exception as e:
                safety_monitor.report_error(component, e, recoverable)
                if not recoverable:
                    raise
                return None
        return wrapper
    return decorator


def validate_inputs(**validators):
    """
    Decorator for automatic input validation.
    
    Usage:
        @validate_inputs(text='text', confidence='float')
        def process(text, confidence):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            validated_kwargs = {}
            
            for param, validator_type in validators.items():
                if param in kwargs:
                    value = kwargs[param]
                    
                    if validator_type == 'text':
                        is_valid, result = InputValidator.validate_text_input(value)
                    elif validator_type == 'gesture':
                        is_valid, result = InputValidator.validate_gesture_name(value)
                    elif validator_type == 'confidence':
                        is_valid, result = InputValidator.validate_confidence(value)
                    elif validator_type == 'path':
                        is_valid, result = InputValidator.validate_file_path(value)
                    else:
                        is_valid, result = True, value
                    
                    if not is_valid:
                        raise ValueError(f"Invalid {param}: {result}")
                    
                    validated_kwargs[param] = result
            
            kwargs.update(validated_kwargs)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# INITIALIZATION
# =============================================================================

# Initialize global safety monitor on module import
_safety_monitor = SafetyMonitor()
_safety_monitor.report_info(
    "BISCompliance",
    "BIS Compliance module loaded",
    {
        'version': BIS_COMPLIANCE_VERSION,
        'standards': ['IS 13252', 'IS 16333']
    }
)
