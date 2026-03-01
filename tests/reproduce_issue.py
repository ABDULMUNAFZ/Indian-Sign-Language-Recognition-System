
import sys
import os
from unittest.mock import MagicMock

# Mock cv2 and mediapipe before importing modules that rely on them
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['mediapipe.tasks'] = MagicMock()
sys.modules['mediapipe.tasks.python'] = MagicMock()
sys.modules['mediapipe.tasks.python.vision'] = MagicMock()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.gesture_recognizer import GestureRecognizer

def test_ti_pattern():
    recognizer = GestureRecognizer()
    
    # Mock hand data with TI___ pattern (Thumb + Index extended)
    # Position: Slightly to the right (x=0.7), mid-height (y=0.5)
    # This approximates the user's uploaded image
    hand_data = {
        'label': 'Left',
        'features': {
            'finger_states': {
                'thumb': True,
                'index': True,
                'middle': False,
                'ring': False,
                'pinky': False
            },
            'palm_center': (0.7, 0.5), # (x, y)
            'fingertips': {
                'index': (0.7, 0.4), # Tip slightly above palm
                'thumb': (0.6, 0.5)
            },
            'hand_openness': 0.0
        }
    }
    
    # Recognize
    result = recognizer.recognize([hand_data])
    print(f"Input Pattern: TI___")
    print(f"Input Position: x=0.7, y=0.5")
    print(f"Recognized Gesture: {result['gesture']}")
    print(f"Confidence: {result['confidence']}")

    # Test distinct positions
    print("\n--- Testing Positions ---")
    
    # 1. Ear position (should be CALL)
    hand_ear = hand_data.copy()
    hand_ear['features'] = hand_data['features'].copy()
    hand_ear['features']['palm_center'] = (0.8, 0.3) # High up, side
    res_ear = recognizer.recognize([hand_ear])
    print(f"Position (0.8, 0.3) [Ear]: {res_ear['gesture']}")
    
    # 2. Chest position (should be I/ME ideally)
    hand_chest = hand_data.copy()
    hand_chest['features'] = hand_data['features'].copy()
    hand_chest['features']['palm_center'] = (0.5, 0.6) # Center, lower
    res_chest = recognizer.recognize([hand_chest])
    print(f"Position (0.5, 0.6) [Chest]: {res_chest['gesture']}")

if __name__ == "__main__":
    test_ti_pattern()
