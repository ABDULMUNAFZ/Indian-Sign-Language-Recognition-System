"""
Gesture Recognition Module - Extended Version
More gestures with reliable pattern-based detection
"""

from enum import Enum


class GestureMode(Enum):
    SENTENCE = "sentence"
    ALPHABET = "alphabet"
    NUMBERS = "numbers"


class GestureRecognizer:
    """
    Extended gesture recognition with 50+ gestures.
    Uses pattern matching + position for accurate detection.
    """
    
    def __init__(self):
        self.mode = GestureMode.SENTENCE
        self.gesture_history = []
        self.history_size = 3
        
    def set_mode(self, mode_str):
        """Set recognition mode."""
        mode_map = {
            'sentence': GestureMode.SENTENCE,
            'alphabet': GestureMode.ALPHABET,
            'numbers': GestureMode.NUMBERS
        }
        self.mode = mode_map.get(mode_str, GestureMode.SENTENCE)
        self.gesture_history = []
    
    def _stabilize(self, gesture, confidence):
        """
        Stabilize gesture detection to reduce flickering.
        
        Improved algorithm:
        - Requires same gesture 2 times in last 3 frames
        - Weights confidence based on consistency
        """
        if gesture is None:
            # Don't immediately clear history on single None
            if len(self.gesture_history) > 0:
                self.gesture_history.append(None)
                if len(self.gesture_history) > self.history_size:
                    self.gesture_history.pop(0)
                # Only return None if multiple consecutive Nones
                none_count = sum(1 for g in self.gesture_history if g is None)
                if none_count >= 2:
                    self.gesture_history = []
                    return None, 0.0
                # Otherwise keep last valid gesture
                for g in reversed(self.gesture_history):
                    if g is not None:
                        return g, confidence * 0.7  # Lower confidence for held gesture
            return None, 0.0
        
        self.gesture_history.append(gesture)
        if len(self.gesture_history) > self.history_size:
            self.gesture_history.pop(0)
        
        # Count occurrences of current gesture in history
        valid_history = [g for g in self.gesture_history if g is not None]
        if not valid_history:
            return None, 0.0
        
        # Check if current gesture appears enough times
        gesture_count = sum(1 for g in valid_history if g == gesture)
        
        # Require gesture to appear at least once (immediate response)
        # For high confidence (>0.85), accept immediately
        # For lower confidence, require 2 matches
        if confidence > 0.85:
            return gesture, confidence
        elif gesture_count >= 2:
            return gesture, confidence
        elif len(valid_history) >= 2 and valid_history[-1] == valid_history[-2]:
            return gesture, confidence
        elif gesture_count >= 1 and confidence > 0.7:
            # Accept single occurrence with good confidence
            return gesture, confidence * 0.9
        
        return None, 0.0
    
    def recognize(self, hands_data):
        """Recognize gesture from hand data."""
        if not hands_data:
            self.gesture_history = []
            return {'gesture': None, 'confidence': 0.0, 'mode': self.mode.value}
        
        # Get hands
        primary = None
        secondary = None
        
        # Sort hands by label if possible
        right_hand = next((h for h in hands_data if h['label'] == 'Right'), None)
        left_hand = next((h for h in hands_data if h['label'] == 'Left'), None)
        
        if right_hand and left_hand:
            primary = right_hand
            secondary = left_hand
        elif right_hand:
            primary = right_hand
        elif left_hand:
            primary = left_hand
        elif hands_data:
            # Fallback if labels are weird (e.g. both same label)
            primary = hands_data[0]
            if len(hands_data) > 1:
                secondary = hands_data[1]
        
        # Recognize
        if self.mode == GestureMode.SENTENCE:
            gesture, conf = self._recognize_sentence(primary, secondary)
        elif self.mode == GestureMode.ALPHABET:
            gesture, conf = self._recognize_alphabet(primary)
        else:
            gesture, conf = self._recognize_number(primary, secondary)
        
        gesture, conf = self._stabilize(gesture, conf)
        
        return {'gesture': gesture, 'confidence': conf, 'mode': self.mode.value}
    
    def _pattern(self, fingers):
        """Create 5-char pattern: T=thumb, I=index, M=middle, R=ring, P=pinky."""
        p = ""
        p += "T" if fingers['thumb'] else "_"
        p += "I" if fingers['index'] else "_"
        p += "M" if fingers['middle'] else "_"
        p += "R" if fingers['ring'] else "_"
        p += "P" if fingers['pinky'] else "_"
        return p
    
    def _recognize_sentence(self, hand, hand2=None):
        """
        Recognize daily-life gestures using patterns + position.
        """
        if hand is None:
            return None, 0.0
        
        f = hand['features']
        fingers = f['finger_states']
        palm_x, palm_y = f['palm_center']
        openness = f['hand_openness']
        
        pat = self._pattern(fingers)
        ext = sum(fingers.values())
        
        # ========== TWO-HAND GESTURES ==========
        if hand2:
            f2 = hand2['features']
            pat2 = self._pattern(f2['finger_states'])
            ext2 = sum(f2['finger_states'].values())
            
            # EMERGENCY - Both hands waving (open)
            if pat == "TIMRP" and pat2 == "TIMRP":
                return "EMERGENCY", 0.94
                
            # HELP - Both hands present with 4+ fingers
            if ext >= 4 and ext2 >= 4:
                return "HELP", 0.96
            
            # PAIN - Both pointing
            if pat == "_I___" and pat2 == "_I___":
                return "PAIN", 0.95
                
            # CLAP / SCHOOL - Both open palms together
            if ext >= 4 and ext2 >= 4 and openness > 0.1:
                return "SCHOOL", 0.88
        
        # ========== UNIQUE 3-FINGER COMBOS ==========
        
        # ILY: Thumb + Index + Pinky = I LOVE YOU 🤟
        if pat == "TI__P":
            return "I_LOVE_YOU", 0.98
        
        # ========== UNIQUE 2-FINGER COMBOS ==========
        
        # Shaka: Thumb + Pinky only = HOW ARE YOU 🤙
        if pat == "T___P":
            return "HOW_ARE_YOU", 0.98
        
        # Horns: Index + Pinky = ROCK 🤘
        if pat == "_I__P":
            return "ROCK", 0.95
        
        # L-Shape: Thumb + Index = L (or phone gesture)
        if pat == "TI___":
            # "CALL" is typically near the ear (high y). 
            # "I/ME" can be L-shape pointing to self (chest level).
            if palm_y < 0.5:
                # Upper half -> CALL/PHONE
                return "CALL", 0.92
            else:
                # Lower half (Chest/Chin) -> I/ME
                # This accommodates the user's specific "L-shape for I/ME" variant
                return "I", 0.90
        
        # ========== SINGLE FINGER ==========
        
        # Only Thumb = THUMBS UP / GOOD / FINE 👍
        if pat == "T____":
            thumb_y = f['fingertips']['thumb'][1]
            if thumb_y < palm_y:  # Thumb pointing up
                return "GOOD", 0.96
            else:
                return "BAD", 0.85
        
        # Only Index = POINTING 👆
        if pat == "_I___":
            # Use Vector math for pointing direction (more robust than position)
            # Vector from Wrist to Index Tip
            wrist = f['wrist']
            tip = f['fingertips']['index']
            dx = tip[0] - wrist[0]
            dy = tip[1] - wrist[1]
            
            # Significant Horizontal movement
            if abs(dx) > abs(dy):
                if dx > 0.1:  # Pointing Right (increasing x)
                    return "YOU", 0.92
                elif dx < -0.1: # Pointing Left (decreasing x)
                    return "GO", 0.92
            
            # Significant Vertical movement
            else:
                if dy < -0.1: # Pointing Up
                    # Near center = What, High up = one
                    if palm_y < 0.3:
                         return "ONE_FINGER", 0.8
                    return "WHAT", 0.88
                else: # Pointing Down/In
                    return "I", 0.94
            
            # Fallback based on position if vector is ambiguous
            if palm_y > 0.5:
                 return "I", 0.90
            return "WHAT", 0.85
        
        # Only Pinky = Promise/Pinky
        if pat == "____P":
            return "PROMISE", 0.9
        
        # Only Middle = ... (rude, skip)
        
        # ========== TWO FINGERS ==========
        
        # Peace/V: Index + Middle = NO / PEACE ✌️
        if pat == "_IM__":
            # Check for PROMISE (Crossed Fingers)
            # Distance between tips vs distance between MCPs
            idx_tip = f['fingertips']['index']
            mid_tip = f['fingertips']['middle']
            tip_dist = ((idx_tip[0]-mid_tip[0])**2 + (idx_tip[1]-mid_tip[1])**2)**0.5
            
            if tip_dist < 0.05: # Tips very close/crossed
                return "PROMISE", 0.95
            
            if palm_y < 0.4:  # High
                return "VICTORY", 0.92
            else:
                return "NO", 0.94
        
        # Scout: Index + Middle + Ring = WATER / W 💧
        if pat == "_IMR_":
            if palm_y < 0.5:
                return "WATER", 0.95
            else:
                return "THREE", 0.9
        
        # ========== POSITION-BASED (5 fingers open) ==========
        
        
        # ========== POSITION-BASED (5 fingers open) ==========
        
        # All fingers open (or just 4 fingers with thumb tucked)
        if pat == "TIMRP" or pat == "_IMRP":
            if palm_y < 0.3:
                return "STOP", 0.95  # Raised high
            elif palm_y < 0.45:
                # If near chin/mouth, it might be THANK YOU (even with thumb)
                if 0.35 < palm_x < 0.65:
                    return "THANK_YOU", 0.9
                return "HELLO", 0.94  # Mid-high (greeting)
            elif palm_y < 0.6:
                if palm_x < 0.4:
                    return "BYE", 0.9  # Side wave
                else:
                    return "HI", 0.85
            else:
                return "PLEASE", 0.88  # Low position
        
        # ========== FIST (all closed) ==========
        
        # Strictly closed OR thumb slightly out (common error)
        if pat == "_____" or pat == "T____" or pat == "_____":
            # If thumb is out but pointing DOWN, it's BAD
            if pat == "T____" and f['fingertips']['thumb'][1] > palm_y:
                 return "BAD", 0.85
                 
            if palm_y < 0.4:
                return "YES", 0.95  # Fist up = yes/power
            elif 0.35 < palm_x < 0.65:
                return "SORRY", 0.85  # Fist on chest = sorry
            else:
                return "FIST", 0.88
        
        # ========== OTHER PATTERNS ==========
        
        # TIM__: Thumb + Index + Middle
        if pat == "TIM__":
            return "OK_SIGN", 0.88
        
        # TIMR_: 4 with pinky down
        if pat == "TIMR_":
            return "FOUR_UP", 0.85
        
        # __MRP: Middle + Ring + Pinky
        if pat == "__MRP":
            return "ALIEN", 0.82
        
        # T_MRP: Thumb + last 3 (no index) - OK Sign
        if pat == "T_MRP":
            return "OK_SIGN", 0.88
        
        # _IM_P: Index + Middle + Pinky
        if pat == "_IM_P":
            return "WHATEVER", 0.85
        
        # TI_RP: Thumb + Index + Ring + Pinky
        if pat == "TI_RP":
            return "SPIDER", 0.82
        
        # Fallback by count
        if ext == 0:
            return "FIST", 0.8
        elif ext == 1:
            return "ONE_FINGER", 0.75
        elif ext == 2:
            return "TWO_FINGERS", 0.75
        elif ext == 3:
            return "THREE_FINGERS", 0.75
        elif ext == 4:
            return "FOUR_FINGERS", 0.75
        
        return None, 0.0
    
    def _get_distance(self, p1, p2):
        """Calculate distance between two points."""
        return ((p1['x'] - p2['x'])**2 + (p1['y'] - p2['y'])**2) ** 0.5

    def _is_c_shape(self, hand):
        """
        Check if hand is forming a 'C' shape.
        Distinguishes 'C' from '5' (Open Palm) based on finger curvature and tip distance.
        """
        lm = hand['landmarks']
        
        # Indices
        THUMB_TIP = 4
        INDEX_TIP = 8
        INDEX_MCP = 5
        PINKY_MCP = 17
        WRIST = 0
        MIDDLE_PIP = 10
        MIDDLE_TIP = 12
        
        # 1. Scale reference (width of palm)
        palm_width = self._get_distance(lm[INDEX_MCP], lm[PINKY_MCP])
        if palm_width == 0: return False
        
        # 2. Check Thumb-Index Tip Distance
        # In '5' (Open Palm), this is usually large relative to palm width (> 1.5x)
        # In 'C', this is smaller as tips curve in (< 1.2x) however not touching (< 0.2x would be O)
        ti_dist = self._get_distance(lm[THUMB_TIP], lm[INDEX_TIP])
        ratio = ti_dist / palm_width
        
        # 3. Check Curvature (Middle Finger)
        # In '5', Middle Tip is far from Wrist.
        # In 'C', Middle Tip is closer to Wrist than in '5'?
        # Better: Check angle or simplified distance ratio
        # Tip-to-Wrist vs MCP-to-Wrist
        tip_wrist = self._get_distance(lm[MIDDLE_TIP], lm[WRIST])
        pip_wrist = self._get_distance(lm[MIDDLE_PIP], lm[WRIST])
        
        # If fingers are curved, Tip-to-Wrist is not MAXIMIZED.
        # But the binary detector says "Extended", so they are somewhat out.
        
        # Primary Metric: The ratio.
        # '5' usually has ratio > 1.3 or 1.4
        # 'C' usually has ratio roughly 0.5 to 1.3
        
        is_c_ratio = 0.4 < ratio < 1.3
        
        return is_c_ratio

    def _recognize_alphabet(self, hand):
        """Alphabet recognition."""
        if hand is None:
            return None, 0.0
        
        fingers = hand['features']['finger_states']
        pat = self._pattern(fingers)
        
        # Special check for 'C' (which often looks like '5' / all open)
        if pat == "TIMRP" or pat == "TIMR_" or pat == "_IMRP":
            if self._is_c_shape(hand):
                return "C", 0.90
        
        PATTERNS = {
            "T____": "A",
            "_IMRP": "B",
            # "TIMRP": "C", # Handled dynamically above
            "_I___": "D",
            "_____": "E",
            "__MRP": "F",
            "TI___": "G",
            "_IM__": "H",
            "____P": "I",
            "TIM__": "K",
            "TI___": "L",
            "_IMR_": "W",
            "T___P": "Y",
            "TIMRP": "5",
        }
        
        if pat in PATTERNS:
            return PATTERNS[pat], 0.92
        
        return None, 0.0
    
    def _recognize_number(self, hand, hand2=None):
        """Number recognition 0-10."""
        if hand is None:
            return None, 0.0
        
        fingers = hand['features']['finger_states']
        pat = self._pattern(fingers)
        
        PATTERNS = {
            "_____": "0",
            "_I___": "1",
            "_IM__": "2",
            "_IMR_": "3",
            "_IMRP": "4",
            "TIMRP": "5",
        }
        
        if pat in PATTERNS:
            return PATTERNS[pat], 0.95
        
        # Two hands
        if hand2:
            ext1 = sum(fingers.values())
            ext2 = sum(hand2['features']['finger_states'].values())
            total = ext1 + ext2
            if 6 <= total <= 10:
                return str(total), 0.9
        
        return str(sum(fingers.values())), 0.75


# ========== GESTURE GUIDE ==========
GESTURE_GUIDE = {
    'sentence': {
        # === UNIQUE ICONIC GESTURES ===
        'I_LOVE_YOU': {'name': 'I Love You', 'description': '🤟 Thumb + Index + Pinky', 'category': 'Love', 'emoji': '🤟'},
        'HOW_ARE_YOU': {'name': 'How Are You?', 'description': '🤙 Thumb + Pinky (Shaka)', 'category': 'Greeting', 'emoji': '🤙'},
        'ROCK': {'name': 'Rock On!', 'description': '🤘 Index + Pinky only', 'category': 'Fun', 'emoji': '🤘'},
        
        # === SINGLE FINGER ===
        'GOOD': {'name': 'Good / Fine', 'description': '👍 Only Thumb up', 'category': 'Response', 'emoji': '👍'},
        'BAD': {'name': 'Bad / Thumbs Down', 'description': '👎 Only Thumb down', 'category': 'Response', 'emoji': '👎'},
        'I': {'name': 'I / Me', 'description': '👆 Index pointing to self (center)', 'category': 'Pronoun', 'emoji': '👆'},
        'YOU': {'name': 'You', 'description': '👉 Index pointing right', 'category': 'Pronoun', 'emoji': '👉'},
        'GO': {'name': 'Go', 'description': '👈 Index pointing left', 'category': 'Action', 'emoji': '👈'},
        'WHAT': {'name': 'What?', 'description': '☝️ Index up (questioning)', 'category': 'Question', 'emoji': '❓'},
        'PROMISE': {'name': 'Promise', 'description': '🤙 Only Pinky extended', 'category': 'Trust', 'emoji': '🤞'},
        
        # === TWO FINGERS ===
        'NO': {'name': 'No / Peace', 'description': '✌️ Index + Middle', 'category': 'Response', 'emoji': '✌️'},
        'VICTORY': {'name': 'Victory', 'description': '✌️ Peace sign raised high', 'category': 'Success', 'emoji': '✌️'},
        'CALL': {'name': 'Call / Phone', 'description': '🤙 Thumb + Index (L shape)', 'category': 'Action', 'emoji': '📞'},
        
        # === THREE FINGERS ===
        'WATER': {'name': 'Water', 'description': '💧 Index + Middle + Ring (W)', 'category': 'Needs', 'emoji': '💧'},
        
        # === OPEN PALM ===
        'STOP': {'name': 'Stop', 'description': '✋ All 5 fingers, raised high', 'category': 'Action', 'emoji': '✋'},
        'HELLO': {'name': 'Hello / Hi', 'description': '👋 All 5 fingers, mid position', 'category': 'Greeting', 'emoji': '👋'},
        'BYE': {'name': 'Goodbye', 'description': '👋 Wave to the side', 'category': 'Greeting', 'emoji': '👋'},
        'HI': {'name': 'Hi', 'description': '✋ Open palm', 'category': 'Greeting', 'emoji': '✋'},
        'PLEASE': {'name': 'Please', 'description': '🙏 Open palm, low position', 'category': 'Request', 'emoji': '🙏'},
        
        # === FOUR FINGERS ===
        'THANK_YOU': {'name': 'Thank You', 'description': '🙏 4 fingers (no thumb) near chin', 'category': 'Gratitude', 'emoji': '🙏'},
        'WAIT': {'name': 'Wait', 'description': '✋ 4 fingers up, palm forward', 'category': 'Action', 'emoji': '⏳'},
        
        # === FIST ===
        'YES': {'name': 'Yes / Power', 'description': '✊ Closed fist raised', 'category': 'Response', 'emoji': '✊'},
        'SORRY': {'name': 'Sorry', 'description': '✊ Fist on chest area', 'category': 'Apology', 'emoji': '😔'},
        
        # === TWO HANDS ===
        'HELP': {'name': 'Help!', 'description': '🆘 Both hands open raised', 'category': 'Emergency', 'emoji': '🆘'},
        'PAIN': {'name': 'Pain / Hurt', 'description': '💔 Both hands pointing', 'category': 'Emergency', 'emoji': '🤕'},
        'EMERGENCY': {'name': 'Emergency', 'description': '🚨 Both palms waving', 'category': 'Emergency', 'emoji': '🚨'},
        'SCHOOL': {'name': 'School', 'description': '📚 Both hands clapping', 'category': 'Places', 'emoji': '🏫'},
        
        # === OTHER ===
        'OK_SIGN': {'name': 'OK / Perfect', 'description': '👌 Thumb + Index + Middle', 'category': 'Response', 'emoji': '👌'},
        'OKAY': {'name': 'Okay', 'description': '👌 OK gesture (thumb circles)', 'category': 'Response', 'emoji': '👌'},
    },
    'alphabet': {letter: {
        'name': letter, 'description': f'Letter {letter}', 'category': 'Alphabet', 'emoji': '🔤'
    } for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'},
    'numbers': {str(n): {
        'name': str(n), 'description': f'{n} finger(s)', 'category': 'Numbers', 'emoji': '🔢'
    } for n in range(11)}
}
