
import unittest
import math
from modules.hand_detector import HandDetector
from modules.gesture_recognizer import GestureRecognizer

class MockLandmark:
    def __init__(self, x, y, z=0):
        self.x = x
        self.y = y
        self.z = z

class TestGestureRecognition(unittest.TestCase):
    def setUp(self):
        self.detector = HandDetector()
        self.recognizer = GestureRecognizer()
        
        # Define common keypoints (normalized coordinates)
        self.WRIST = 0
        self.THUMB_CMC = 1
        self.THUMB_MCP = 2
        self.THUMB_IP = 3
        self.THUMB_TIP = 4
        self.INDEX_MCP = 5
        self.INDEX_TIP = 8
        self.MIDDLE_MCP = 9
        self.MIDDLE_TIP = 12
        self.RING_MCP = 13
        self.RING_TIP = 16
        self.PINKY_MCP = 17
        self.PINKY_TIP = 20

    def create_hand(self, thumb_open=False, index_open=False, middle_open=False, ring_open=False, pinky_open=False):
        """Creates a mock hand with specified fingers open/closed."""
        # Initialize with dicts instead of objects
        landmarks = [{'x': 0.5, 'y': 0.9, 'z': 0}] * 21 
        
        # Wrist
        landmarks[self.WRIST] = {'x': 0.5, 'y': 0.9, 'z': 0}
        
        # Set base MCPs
        landmarks[self.THUMB_CMC] = {'x': 0.4, 'y': 0.8, 'z': 0}
        landmarks[self.THUMB_MCP] = {'x': 0.35, 'y': 0.7, 'z': 0}
        landmarks[self.INDEX_MCP] = {'x': 0.45, 'y': 0.6, 'z': 0}
        landmarks[self.MIDDLE_MCP] = {'x': 0.5, 'y': 0.6, 'z': 0}
        landmarks[self.RING_MCP] = {'x': 0.55, 'y': 0.6, 'z': 0}
        landmarks[self.PINKY_MCP] = {'x': 0.6, 'y': 0.65, 'z': 0}
        
        # PIP/DIP joints
        # Index
        landmarks[6] = {'x': 0.45, 'y': 0.5, 'z': 0} 
        landmarks[7] = {'x': 0.45, 'y': 0.4, 'z': 0}
        # Middle
        landmarks[10] = {'x': 0.5, 'y': 0.5, 'z': 0} 
        landmarks[11] = {'x': 0.5, 'y': 0.4, 'z': 0} 
        # Ring
        landmarks[14] = {'x': 0.55, 'y': 0.5, 'z': 0}
        landmarks[15] = {'x': 0.55, 'y': 0.4, 'z': 0}
        # Pinky
        landmarks[18] = {'x': 0.6, 'y': 0.55, 'z': 0}
        landmarks[19] = {'x': 0.6, 'y': 0.45, 'z': 0}
        
        # Helper to set finger
        def set_finger(tip_idx, mcp_idx, is_open, x_offset):
            mcp_y = landmarks[mcp_idx]['y']
            if is_open:
                # Open: Tip far above MCP
                landmarks[tip_idx] = {'x': landmarks[mcp_idx]['x'] + x_offset, 'y': mcp_y - 0.3, 'z': 0}
            else:
                # Closed: Tip close to MCP
                landmarks[tip_idx] = {'x': landmarks[mcp_idx]['x'] + x_offset, 'y': mcp_y + 0.05, 'z': 0}
                
        # Helper for thumb
        def set_thumb(is_open):
            if is_open:
                # Open: Tip far from palm center/index MCP
                landmarks[self.THUMB_TIP] = {'x': 0.2, 'y': 0.5, 'z': 0}
                landmarks[self.THUMB_IP] = {'x': 0.25, 'y': 0.6, 'z': 0}
            else:
                # Closed: Tip close to Index MCP
                landmarks[self.THUMB_TIP] = {'x': 0.42, 'y': 0.6, 'z': 0}
                landmarks[self.THUMB_IP] = {'x': 0.4, 'y': 0.65, 'z': 0}

        set_thumb(thumb_open)
        set_finger(self.INDEX_TIP, self.INDEX_MCP, index_open, 0)
        set_finger(self.MIDDLE_TIP, self.MIDDLE_MCP, middle_open, 0)
        set_finger(self.RING_TIP, self.RING_MCP, ring_open, 0)
        set_finger(self.PINKY_TIP, self.PINKY_MCP, pinky_open, 0)
        
        return landmarks

    def test_finger_states(self):
        """Test if finger states are correctly detected."""
        # Test Open Palm (All Open)
        landmarks = self.create_hand(True, True, True, True, True)
        features = self.detector._calculate_features(landmarks)
        states = features['finger_states']
        self.assertTrue(all(states.values()), "All fingers should be detected as open")
        
        # Test Fist (All Closed)
        landmarks = self.create_hand(False, False, False, False, False)
        features = self.detector._calculate_features(landmarks)
        states = features['finger_states']
        self.assertFalse(any(states.values()), "All fingers should be detected as closed")
        
        # Test Victory (Index + Middle)
        landmarks = self.create_hand(False, True, True, False, False)
        features = self.detector._calculate_features(landmarks)
        states = features['finger_states']
        self.assertTrue(states['index'] and states['middle'])
        self.assertFalse(states['ring'] or states['pinky'])

    def test_gesture_recognition(self):
        """Test if gestures are correctly recognized from features."""
        # Test 'HELLO' (Open Palm, High Up)
        landmarks = self.create_hand(True, True, True, True, True)
        # Move hand high up (y coordinates close to 0)
        for lm in landmarks: lm['y'] -= 0.5 
        
        # Reset smoothing history to avoid blending with previous unshifted hand
        self.detector.prev_landmarks = [None, None]
        
        # Mock the data structure expected by recognizer
        features = self.detector._calculate_features(landmarks)
        hand_data = {'label': 'Right', 'features': features, 'landmarks': landmarks}
        
        result = self.recognizer.recognize([hand_data])
        # Note: stabilization might return None on first frame, loop needed usually
        # But let's check internal recognition logic
        gesture, conf = self.recognizer._recognize_sentence(hand_data)
        self.assertIn(gesture, ['HELLO', 'STOP', 'HI'])

if __name__ == '__main__':
    unittest.main()
