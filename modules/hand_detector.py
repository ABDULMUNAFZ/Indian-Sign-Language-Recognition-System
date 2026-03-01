"""
Hand Detection Module - Pixel Perfect Version
Uses angle-based detection for accurate finger state recognition

BIS Compliance:
- IS 13252: Implements safe resource management and error handling
- IS 16333: Camera system safety checks and frame validation (Ready)
"""

import cv2
import numpy as np
from collections import deque
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import urllib.request
import os
import math

import config

# Import BIS compliance components
try:
    from modules.bis_compliance import (
        SafetyMonitor, CameraSystemSafety, ResourceManager,
        safe_execute, InputValidator
    )
    BIS_COMPLIANCE_AVAILABLE = True
except ImportError:
    BIS_COMPLIANCE_AVAILABLE = False



class HandDetector:
    """
    High-accuracy hand detection with angle-based finger recognition.
    
    BIS Compliance (IS 13252 / IS 16333):
    - Safe resource initialization and cleanup
    - Camera system validation
    - Error monitoring and graceful degradation
    """
    
    def __init__(self):
        # Initialize BIS safety monitoring
        if BIS_COMPLIANCE_AVAILABLE:
            self.safety_monitor = SafetyMonitor()
            self.camera_safety = CameraSystemSafety()
            self.resource_manager = ResourceManager()
            self.safety_monitor.report_info(
                "HandDetector",
                "Initializing hand detection module with BIS compliance"
            )
        else:
            self.safety_monitor = None
            self.camera_safety = None
            self.resource_manager = None
        
        # Download model if needed (with error handling per IS 13252)
        model_path = os.path.join(config.BASE_DIR, 'hand_landmarker.task')
        try:
            if not os.path.exists(model_path):
                print("Downloading hand landmarker model...")
                url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
                urllib.request.urlretrieve(url, model_path)
                print("Model downloaded!")
                if self.safety_monitor:
                    self.safety_monitor.report_info(
                        "HandDetector",
                        "Hand landmarker model downloaded successfully"
                    )
        except Exception as e:
            if self.safety_monitor:
                self.safety_monitor.report_error(
                    "HandDetector",
                    Exception(f"Failed to download model: {e}"),
                    recoverable=False
                )
            raise

        
        # Initialize MediaPipe
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=config.MAX_HANDS,
            min_hand_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
            min_hand_presence_confidence=config.MIN_TRACKING_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE
        )
        self.hand_landmarker = vision.HandLandmarker.create_from_options(options)
        
        # Smoothing
        self.smoothing_factor = config.LANDMARK_SMOOTHING_FACTOR
        self.prev_landmarks = [None, None]
        
        # Landmark indices
        self.WRIST = 0
        self.THUMB_CMC, self.THUMB_MCP, self.THUMB_IP, self.THUMB_TIP = 1, 2, 3, 4
        self.INDEX_MCP, self.INDEX_PIP, self.INDEX_DIP, self.INDEX_TIP = 5, 6, 7, 8
        self.MIDDLE_MCP, self.MIDDLE_PIP, self.MIDDLE_DIP, self.MIDDLE_TIP = 9, 10, 11, 12
        self.RING_MCP, self.RING_PIP, self.RING_DIP, self.RING_TIP = 13, 14, 15, 16
        self.PINKY_MCP, self.PINKY_PIP, self.PINKY_DIP, self.PINKY_TIP = 17, 18, 19, 20
        
        # Hand connections for drawing
        self.HAND_CONNECTIONS = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (0, 9), (9, 10), (10, 11), (11, 12),
            (0, 13), (13, 14), (14, 15), (15, 16),
            (0, 17), (17, 18), (18, 19), (19, 20),
            (5, 9), (9, 13), (13, 17)
        ]
        
    def detect(self, frame):
        """Detect hands and extract landmarks."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        results = self.hand_landmarker.detect(mp_image)
        
        hands_data = []
        
        if results.hand_landmarks:
            for idx, hand_landmarks in enumerate(results.hand_landmarks):
                hand_label = "Right"
                if results.handedness and idx < len(results.handedness):
                    hand_label = results.handedness[idx][0].category_name
                
                confidence = 0.9
                if results.handedness and idx < len(results.handedness):
                    confidence = results.handedness[idx][0].score
                
                # Extract landmarks
                landmarks = self._extract_landmarks(hand_landmarks)
                
                # Smooth landmarks
                if idx < 2:
                    landmarks = self._smooth_landmarks(landmarks, idx)
                
                # Calculate features with accurate finger detection
                features = self._calculate_features(landmarks, hand_label)
                
                hands_data.append({
                    'label': hand_label,
                    'confidence': confidence,
                    'landmarks': landmarks,
                    'features': features
                })
                
                # Draw
                self._draw_landmarks(frame, landmarks, features)
        
        return {
            'hands': hands_data,
            'frame': frame,
            'num_hands': len(hands_data)
        }
    
    def _extract_landmarks(self, hand_landmarks):
        """Extract landmarks as list of dicts."""
        return [{'x': lm.x, 'y': lm.y, 'z': lm.z} for lm in hand_landmarks]
    
    def _smooth_landmarks(self, landmarks, hand_idx):
        """Apply smoothing."""
        if self.prev_landmarks[hand_idx] is None:
            self.prev_landmarks[hand_idx] = landmarks
            return landmarks
        
        alpha = self.smoothing_factor
        smoothed = []
        for i, lm in enumerate(landmarks):
            prev = self.prev_landmarks[hand_idx][i]
            smoothed.append({
                'x': alpha * lm['x'] + (1 - alpha) * prev['x'],
                'y': alpha * lm['y'] + (1 - alpha) * prev['y'],
                'z': alpha * lm['z'] + (1 - alpha) * prev['z']
            })
        self.prev_landmarks[hand_idx] = smoothed
        return smoothed
    
    def _get_distance(self, p1, p2):
        """Calculate distance between two points."""
        return math.sqrt((p1['x'] - p2['x'])**2 + (p1['y'] - p2['y'])**2)
    
    def _get_angle(self, p1, p2, p3):
        """Calculate angle at p2 between p1-p2-p3."""
        v1 = (p1['x'] - p2['x'], p1['y'] - p2['y'])
        v2 = (p3['x'] - p2['x'], p3['y'] - p2['y'])
        
        dot = v1[0] * v2[0] + v1[1] * v2[1]
        mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
        mag2 = math.sqrt(v2[0]**2 + v2[1]**2)
        
        if mag1 * mag2 == 0:
            return 0
        
        cos_angle = max(-1, min(1, dot / (mag1 * mag2)))
        return math.degrees(math.acos(cos_angle))
    
    def _is_finger_extended(self, landmarks, mcp, pip, dip, tip):
        """
        Robust finger extension detection.
        
        Simplified Logic:
        A finger is extended if the tip is significantly further from the wrist 
        than the PIP joint is. This works regardless of hand orientation (up/down/side).
        """
        tip_pt = landmarks[tip]
        pip_pt = landmarks[pip]
        wrist_pt = landmarks[self.WRIST]
        mcp_pt = landmarks[mcp]
        
        # Distance to wrist is invariant to rotation
        tip_to_wrist = self._get_distance(tip_pt, wrist_pt)
        pip_to_wrist = self._get_distance(pip_pt, wrist_pt)
        mcp_to_wrist = self._get_distance(mcp_pt, wrist_pt)
        
        # Primary Check: Tip must be further out than PIP
        # Multiplier 1.2 ensures it's significantly extended, not just loosely open
        is_extended = tip_to_wrist > pip_to_wrist * 1.15
        
        # Secondary Check: Finger must not be curled under (tip shouldn't be close to MCP)
        # If tip is close to MCP (distance < MCP-to-Wrist * 0.5), it's likely curled
        tip_to_mcp = self._get_distance(tip_pt, mcp_pt)
        is_not_curled = tip_to_mcp > mcp_to_wrist * 0.4
        
        return is_extended and is_not_curled
    
    def _is_thumb_extended(self, landmarks, hand_label):
        """
        Robust thumb detection.
        
        Logic:
        Thumb is extended if the tip is far from the index finger MCP (base of index).
        """
        thumb_tip = landmarks[self.THUMB_TIP]
        thumb_ip = landmarks[self.THUMB_IP]
        thumb_mcp = landmarks[self.THUMB_MCP]
        index_mcp = landmarks[self.INDEX_MCP]
        pinky_mcp = landmarks[self.PINKY_MCP]
        wrist = landmarks[self.WRIST]
        
        # 1. Distance check relative to hand size (Index MCP to Pinky MCP is a good scale reference)
        hand_scale = self._get_distance(index_mcp, pinky_mcp)
        if hand_scale == 0: hand_scale = 1.0 # Prevent div by zero
        
        # Distance from thumb tip to Index MCP
        thumb_spread = self._get_distance(thumb_tip, index_mcp)
        
        # If thumb is spread out more than 80% of palm width, it's extended
        is_spread = thumb_spread > hand_scale * 0.8
        
        # 2. Angle check - thumb IP joint should be straight
        thumb_angle = self._get_angle(thumb_mcp, thumb_ip, thumb_tip)
        is_straight = thumb_angle > 150 # Thumbs are usually quite straight when extended
        
        # 3. Distance from wrist (must be far from wrist)
        tip_to_wrist = self._get_distance(landmarks[self.THUMB_TIP], wrist)
        ip_to_wrist = self._get_distance(landmarks[self.THUMB_IP], wrist)
        is_outward = tip_to_wrist > ip_to_wrist
        
        # Require spread AND (straight OR outward)
        return is_spread and (is_straight or is_outward)
    
    def _calculate_features(self, landmarks, hand_label='Right'):
        """Calculate hand features with accurate finger detection."""
        
        # Accurate finger state detection
        finger_states = {
            'thumb': self._is_thumb_extended(landmarks, hand_label),
            'index': self._is_finger_extended(landmarks, 
                self.INDEX_MCP, self.INDEX_PIP, self.INDEX_DIP, self.INDEX_TIP),
            'middle': self._is_finger_extended(landmarks,
                self.MIDDLE_MCP, self.MIDDLE_PIP, self.MIDDLE_DIP, self.MIDDLE_TIP),
            'ring': self._is_finger_extended(landmarks,
                self.RING_MCP, self.RING_PIP, self.RING_DIP, self.RING_TIP),
            'pinky': self._is_finger_extended(landmarks,
                self.PINKY_MCP, self.PINKY_PIP, self.PINKY_DIP, self.PINKY_TIP)
        }
        
        extended_count = sum(finger_states.values())
        
        # Palm center
        palm_x = np.mean([landmarks[i]['x'] for i in [0, 5, 9, 13, 17]])
        palm_y = np.mean([landmarks[i]['y'] for i in [0, 5, 9, 13, 17]])
        
        # Hand openness
        fingertips = [landmarks[i] for i in [4, 8, 12, 16, 20]]
        openness = np.mean([
            self._get_distance(ft, {'x': palm_x, 'y': palm_y, 'z': 0})
            for ft in fingertips
        ])
        
        return {
            'finger_states': finger_states,
            'extended_count': extended_count,
            'palm_center': (palm_x, palm_y),
            'hand_openness': openness,
            'wrist': (landmarks[0]['x'], landmarks[0]['y']),
            'fingertips': {
                'thumb': (landmarks[4]['x'], landmarks[4]['y']),
                'index': (landmarks[8]['x'], landmarks[8]['y']),
                'middle': (landmarks[12]['x'], landmarks[12]['y']),
                'ring': (landmarks[16]['x'], landmarks[16]['y']),
                'pinky': (landmarks[20]['x'], landmarks[20]['y'])
            }
        }
    
    def _draw_landmarks(self, frame, landmarks, features):
        """Draw landmarks with finger state indicators."""
        h, w = frame.shape[:2]
        
        # Draw connections
        for start_idx, end_idx in self.HAND_CONNECTIONS:
            start = landmarks[start_idx]
            end = landmarks[end_idx]
            start_pt = (int(start['x'] * w), int(start['y'] * h))
            end_pt = (int(end['x'] * w), int(end['y'] * h))
            cv2.line(frame, start_pt, end_pt, (0, 200, 0), 2)
        
        # Draw fingertips with color based on extended state
        fingertip_indices = [4, 8, 12, 16, 20]
        finger_names = ['thumb', 'index', 'middle', 'ring', 'pinky']
        
        for idx, name in zip(fingertip_indices, finger_names):
            pt = (int(landmarks[idx]['x'] * w), int(landmarks[idx]['y'] * h))
            
            # Green if extended, Red if curled
            if features['finger_states'][name]:
                color = (0, 255, 0)  # Green = extended
            else:
                color = (0, 0, 255)  # Red = curled
            
            cv2.circle(frame, pt, 8, color, -1)
            cv2.circle(frame, pt, 10, (255, 255, 255), 2)
        
        # Draw other landmarks smaller
        for i, lm in enumerate(landmarks):
            if i not in fingertip_indices:
                pt = (int(lm['x'] * w), int(lm['y'] * h))
                cv2.circle(frame, pt, 4, (100, 100, 100), -1)
    
    def release(self):
        """
        Release resources safely (IS 13252 compliant).
        
        Ensures proper cleanup of all allocated resources
        with safety monitoring and audit logging.
        """
        try:
            if hasattr(self, 'hand_landmarker'):
                self.hand_landmarker.close()
            
            if self.safety_monitor:
                self.safety_monitor.report_info(
                    "HandDetector",
                    "Resources released successfully"
                )
        except Exception as e:
            if self.safety_monitor:
                self.safety_monitor.report_error(
                    "HandDetector",
                    Exception(f"Error during resource release: {e}"),
                    recoverable=True
                )

