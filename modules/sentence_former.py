"""
Sentence Formation Module
Combines recognized gestures into natural sentences
"""

import time
from collections import deque
import config


class SentenceFormer:
    """
    Forms natural sentences from a sequence of recognized gestures.
    
    Features:
    - 10-second gesture buffer
    - Pause detection for gesture boundaries
    - Intelligent merging of gestures
    - Grammar correction for natural output
    """
    
    def __init__(self):
        self.buffer_duration = config.GESTURE_BUFFER_DURATION
        self.gesture_buffer = deque()
        self.is_recording = False
        self.recording_start_time = None
        
        # Gesture tracking
        self.last_gesture = None
        self.last_gesture_time = None
        self.gesture_hold_time = config.GESTURE_HOLD_TIME
        
        # Confirmed gestures (held long enough)
        self.confirmed_gestures = []
        
        # Sentence formation rules
        self.grammar_rules = {
            ('I', 'AM'): 'I am',
            ('I', 'NEED'): 'I need',
            ('HOW', 'ARE', 'YOU'): 'How are you?',
            ('I', 'AM', 'FINE'): 'I am fine.',
            ('THANK', 'YOU'): 'Thank you.',
            ('COME', 'HERE'): 'Come here.',
        }
        
        # Word mappings for natural output - COMPLETE
        self.word_map = {
            # Iconic signs
            'I_LOVE_YOU': 'I love you',
            'HOW_ARE_YOU': 'How are you?',
            'ROCK': 'Rock on!',
            
            # Single finger
            'GOOD': 'Good',
            'BAD': 'Bad',
            'I': 'I',
            'YOU': 'You',
            'GO': 'Go',
            'WHAT': 'What?',
            'PROMISE': 'I promise',
            
            # Two fingers
            'NO': 'No',
            'VICTORY': 'Victory!',
            'CALL': 'Call me',
            
            # Three fingers
            'WATER': 'Water',
            'THREE': 'Three',
            
            # Open palm
            'STOP': 'Stop',
            'HELLO': 'Hello',
            'BYE': 'Goodbye',
            'PLEASE': 'Please',
            'HI': 'Hi',
            
            # Four fingers
            'THANK_YOU': 'Thank you',
            'WAIT': 'Wait',
            'FOUR': 'Four',
            
            # Fist
            'YES': 'Yes',
            'SORRY': 'Sorry',
            'FIST': 'Yes',
            
            # Two hands
            'HELP': 'Help!',
            'PAIN': 'I am in pain',
            'EMERGENCY': 'Emergency!',
            'SCHOOL': 'School',
            
            # Other
            'OK_SIGN': 'OK',
            'OKAY': 'Okay',
            'I_AM_FINE': 'I am fine',
            
            # Legacy support
            'COME_HERE': 'Come here',
            'NAME': 'My name is',
            'WASHROOM': 'I need the washroom',
        }
    
    def start_recording(self):
        """Start a new recording session."""
        self.is_recording = True
        self.recording_start_time = time.time()
        self.gesture_buffer.clear()
        self.confirmed_gestures = []
        self.last_gesture = None
        self.last_gesture_time = None
    
    def stop_recording(self):
        """Stop recording and return the formed sentence."""
        self.is_recording = False
        sentence = self.form_sentence()
        return sentence
    
    def add_gesture(self, gesture, confidence, mode='sentence'):
        """
        Add a recognized gesture to the buffer.
        
        Args:
            gesture: The recognized gesture string
            confidence: Confidence level (0-1)
            mode: Recognition mode
            
        Returns:
            dict with recording status and current gestures
        """
        current_time = time.time()
        
        if not self.is_recording:
            return {
                'is_recording': False,
                'gestures': [],
                'elapsed_time': 0
            }
        
        elapsed = current_time - self.recording_start_time
        
        # Check if buffer duration exceeded
        if elapsed >= self.buffer_duration:
            sentence = self.stop_recording()
            return {
                'is_recording': False,
                'gestures': self.confirmed_gestures.copy(),
                'sentence': sentence,
                'elapsed_time': elapsed,
                'completed': True
            }
        
        # Add to buffer with timestamp (lowered threshold from 0.6 to 0.5)
        if gesture and confidence > 0.5:
            self.gesture_buffer.append({
                'gesture': gesture,
                'confidence': confidence,
                'time': current_time,
                'mode': mode
            })
            
            # Track gesture hold time
            if gesture == self.last_gesture:
                hold_duration = current_time - self.last_gesture_time
                if hold_duration >= self.gesture_hold_time:
                    # Gesture held long enough - confirm it
                    if not self.confirmed_gestures or self.confirmed_gestures[-1] != gesture:
                        self.confirmed_gestures.append(gesture)
                        # Reset hold timer for next confirmation
                        self.last_gesture_time = current_time
            else:
                # New gesture detected
                self.last_gesture = gesture
                self.last_gesture_time = current_time
                
                # For very high confidence, confirm immediately
                if confidence > 0.9:
                    if not self.confirmed_gestures or self.confirmed_gestures[-1] != gesture:
                        self.confirmed_gestures.append(gesture)
        
        return {
            'is_recording': True,
            'gestures': self.confirmed_gestures.copy(),
            'elapsed_time': elapsed,
            'current_gesture': gesture,
            'completed': False
        }
    
    def form_sentence(self):
        """
        Form a natural sentence from confirmed gestures.
        
        Returns:
            Natural language sentence string
        """
        if not self.confirmed_gestures:
            return ""
        
        gestures = self.confirmed_gestures.copy()
        
        # Check if any contain alphabet letters (name spelling)
        words = []
        spelling_buffer = []
        
        for g in gestures:
            # Check if it's a single letter (alphabet mode)
            if len(g) == 1 and g.isalpha():
                spelling_buffer.append(g)
            else:
                # If we have accumulated letters, form a name
                if spelling_buffer:
                    name = ''.join(spelling_buffer)
                    words.append(name.capitalize())
                    spelling_buffer = []
                
                # Add the word
                if g in self.word_map:
                    words.append(self.word_map[g])
                else:
                    words.append(g.replace('_', ' ').title())
        
        # Handle any remaining spelling
        if spelling_buffer:
            name = ''.join(spelling_buffer)
            words.append(name.capitalize())
        
        # Form the sentence
        if not words:
            return ""
        
        sentence = self._apply_grammar(words)
        
        return sentence
    
    def _apply_grammar(self, words):
        """Apply grammar rules to form natural sentences."""
        # Join words
        raw_sentence = ' '.join(words)
        
        # Fix common patterns
        corrections = [
            ('I am am', 'I am'),
            ('I I', 'I'),
            ('am am', 'am'),
            ('is is', 'is'),
            ('Hello Hello', 'Hello'),
            ('Thank you you', 'Thank you'),
            ('  ', ' '),
        ]
        
        sentence = raw_sentence
        for old, new in corrections:
            sentence = sentence.replace(old, new)
        
        # Ensure proper capitalization
        if sentence:
            sentence = sentence[0].upper() + sentence[1:]
        
        # Add punctuation if missing
        if sentence and sentence[-1] not in '.!?':
            if any(q in sentence.lower() for q in ['how', 'what', 'where', 'when', 'why', 'who']):
                sentence += '?'
            else:
                sentence += '.'
        
        return sentence.strip()
    
    def get_recording_progress(self):
        """Get the current recording progress."""
        if not self.is_recording:
            return {
                'is_recording': False,
                'progress': 0,
                'elapsed': 0,
                'remaining': self.buffer_duration
            }
        
        elapsed = time.time() - self.recording_start_time
        progress = min(elapsed / self.buffer_duration, 1.0)
        
        return {
            'is_recording': True,
            'progress': progress,
            'elapsed': elapsed,
            'remaining': max(0, self.buffer_duration - elapsed),
            'gesture_count': len(self.confirmed_gestures)
        }
    
    def clear(self):
        """Clear all buffers."""
        self.gesture_buffer.clear()
        self.confirmed_gestures = []
        self.last_gesture = None
        self.last_gesture_time = None
        self.is_recording = False
        self.recording_start_time = None
