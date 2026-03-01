
import sys
import os
from unittest.mock import MagicMock

# Mock cv2 and mediapipe
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['mediapipe.tasks'] = MagicMock()
sys.modules['mediapipe.tasks.python'] = MagicMock()
sys.modules['mediapipe.tasks.python.vision'] = MagicMock()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.gesture_recognizer import GestureRecognizer

def test_issues():
    recognizer = GestureRecognizer()
    
    print("--- 1. PROMISE vs NO ---")
    # User shows Crossed Fingers (Index+Middle). Currently detected as NO (_IM__).
    # Key: Tips are close/crossed, Mcps are normal.
    hand_promise = {
        'label': 'Right',
        'features': {
            'finger_states': {'thumb': False, 'index': True, 'middle': True, 'ring': False, 'pinky': False},
            'palm_center': (0.5, 0.5),
            'fingertips': {
                'index': (0.5, 0.3), 'middle': (0.52, 0.3), # Tips close
                'thumb': (0.6, 0.6)
            },
            'hand_openness': 0.1,
            'wrist': (0.5, 0.8)
        },
        'landmarks': [
             # Simple mock landmarks for distance checks
             # Wrist
             {'x': 0.5, 'y': 0.9, 'z': 0},
             {}, {}, {}, {}, 
             # Index MCP (5)
             {'x': 0.48, 'y': 0.6, 'z': 0},
             {}, {}, 
             # Index Tip (8)
             {'x': 0.50, 'y': 0.3, 'z': 0},
             # Middle MCP (9)
             {'x': 0.52, 'y': 0.6, 'z': 0},
             {}, {}, 
             # Middle Tip (12)
             {'x': 0.52, 'y': 0.3, 'z': 0}, # Tips very close (dist=0.02)
             {},{},{},{},{},{},{},{},{}
        ]
    }
    # MCP dist = 0.04. Tip dist = 0.02. Ratio = 0.5 (Converging)
    
    res = recognizer.recognize([hand_promise])
    print(f"Input: Crossed Fingers (_IM__), Tips Converging. Expected: PROMISE. Got: {res['gesture']}")


    print("\n--- 2. YOU vs I ---")
    # User points to SIDE (Right). Currently "I".
    # Pattern: _I___
    hand_you = {
        'label': 'Right',
        'features': {
            'finger_states': {'thumb': False, 'index': True, 'middle': False, 'ring': False, 'pinky': False},
            'palm_center': (0.4, 0.5), # Central palm
            'fingertips': {
                'index': (0.8, 0.5), # Tip far RIGHT (large x)
                'thumb': (0.4, 0.5)
            },
            'wrist': (0.3, 0.5), # Wrist on left
            'hand_openness': 0.1
        }
    }
    res = recognizer.recognize([hand_you])
    print(f"Input: Pointing Right (Tip x=0.8, Wrist x=0.3). Expected: YOU. Got: {res['gesture']}")
    
    
    print("\n--- 3. GO vs YOU ---")
    # User points LEFT. Currently "YOU".
    # Pattern: _I___
    hand_go = {
        'label': 'Right',
        'features': {
            'finger_states': {'thumb': False, 'index': True, 'middle': False, 'ring': False, 'pinky': False},
            'palm_center': (0.6, 0.5), # Central palm
            'fingertips': {
                'index': (0.2, 0.5), # Tip far LEFT (small x)
                'thumb': (0.6, 0.5)
            },
            'wrist': (0.7, 0.5), # Wrist on right
            'hand_openness': 0.1
        }
    }
    res = recognizer.recognize([hand_go])
    print(f"Input: Pointing Left (Tip x=0.2, Wrist x=0.7). Expected: GO. Got: {res['gesture']}")

if __name__ == "__main__":
    test_issues()
