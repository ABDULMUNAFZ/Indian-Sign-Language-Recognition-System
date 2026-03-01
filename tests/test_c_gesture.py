
import unittest
import math

class TestCGesture(unittest.TestCase):
    def _get_distance(self, p1, p2):
        return ((p1['x'] - p2['x'])**2 + (p1['y'] - p2['y'])**2) ** 0.5
        
    def _is_c_shape(self, lm):
        # Replicating the logic from gesture_recognizer.py for testing
        THUMB_TIP = 4
        INDEX_TIP = 8
        INDEX_MCP = 5
        PINKY_MCP = 17
        
        palm_width = self._get_distance(lm[INDEX_MCP], lm[PINKY_MCP])
        if palm_width == 0: return False
        
        ti_dist = self._get_distance(lm[THUMB_TIP], lm[INDEX_TIP])
        ratio = ti_dist / palm_width
        
        print(f"Ratio: {ratio:.2f}")
        return 0.4 < ratio < 1.3

    def test_c_vs_5(self):
        # Mock Landmarks (Simplified 2D)
        # Wrist at (0,0)
        # Palm Width roughly 0.1 (common in normalized coordinates)
        
        # 1. '5' Gesture (Open Palm)
        # Thumb sticking out left/down, Index sticking up/right
        lm_5 = {
            0: {'x': 0.5, 'y': 0.9}, # Wrist
            5: {'x': 0.6, 'y': 0.6}, # Index MCP
            17: {'x': 0.4, 'y': 0.6}, # Pinky MCP
            # Palm width = 0.2
            
            4: {'x': 0.8, 'y': 0.6}, # Thumb Tip (far right)
            8: {'x': 0.6, 'y': 0.3}, # Index Tip (high up)
        }
        # Dist Thumb-Index: sqrt((0.8-0.6)^2 + (0.6-0.3)^2) = sqrt(0.04 + 0.09) = sqrt(0.13) = 0.36
        # Palm Width: 0.2
        # Ratio: 0.36 / 0.2 = 1.8
        # Should NOT be C
        
        print("\nTesting '5' Gesture:")
        self.assertFalse(self._is_c_shape(lm_5), "5 Gesture should not be detected as C")
        
        # 2. 'C' Gesture
        # Thumb and Index curved towards each other
        lm_C = {
            0: {'x': 0.5, 'y': 0.9},
            5: {'x': 0.6, 'y': 0.6},
            17: {'x': 0.4, 'y': 0.6},
            # Palm width = 0.2
            
            4: {'x': 0.7, 'y': 0.5}, # Thumb Tip (closer)
            8: {'x': 0.65, 'y': 0.4}, # Index Tip (curved down)
        }
        # Dist Thumb-Index: sqrt((0.7-0.65)^2 + (0.5-0.4)^2) = sqrt(0.0025 + 0.01) = sqrt(0.0125) = 0.1118
        # Ratio: 0.1118 / 0.2 = 0.559
        # Should be C (0.4 < 0.559 < 1.3)
        
        print("\nTesting 'C' Gesture:")
        self.assertTrue(self._is_c_shape(lm_C), "C Gesture should be detected as C")
        
        # 3. 'O' Gesture (Touching)
        lm_O = {
            0: {'x': 0.5, 'y': 0.9},
            5: {'x': 0.6, 'y': 0.6},
            17: {'x': 0.4, 'y': 0.6},
            
            4: {'x': 0.62, 'y': 0.45}, # Thumb Tip (touching index)
            8: {'x': 0.62, 'y': 0.45}, # Index Tip
        }
        # Dist = 0
        # Ratio = 0
        # Should NOT be C (Ratio < 0.4)
        
        print("\nTesting 'O' Gesture:")
        self.assertFalse(self._is_c_shape(lm_O), "O Gesture (touching) should not be detected as C")

if __name__ == '__main__':
    unittest.main()
