"""
Session Logger Module
Logs gestures and sentences to CSV files for tracking and analysis
"""

import os
import csv
from datetime import datetime
import config


class SessionLogger:
    """
    Logs recognition sessions to CSV files.
    
    Logs include:
    - Timestamp
    - Mode (sentence/alphabet/numbers)
    - Language
    - Detected gestures
    - Final output
    """
    
    def __init__(self):
        self.log_dir = config.LOGS_DIR
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Create log file for today
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        self.log_file = os.path.join(self.log_dir, f'session_{self.current_date}.csv')
        
        # Initialize CSV if needed
        self._init_csv()
        
        self.session_start = datetime.now()
        self.entries = []
    
    def _init_csv(self):
        """Initialize CSV file with headers if it doesn't exist."""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'mode',
                    'language',
                    'gestures_detected',
                    'final_output',
                    'confidence_avg'
                ])
    
    def log_recognition(self, mode, language, gestures, output, confidence=0.0):
        """
        Log a recognition event.
        
        Args:
            mode: Recognition mode (sentence/alphabet/numbers)
            language: Output language
            gestures: List of detected gestures
            output: Final sentence/output
            confidence: Average confidence score
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        gestures_str = ','.join(gestures) if isinstance(gestures, list) else str(gestures)
        
        entry = {
            'timestamp': timestamp,
            'mode': mode,
            'language': language,
            'gestures': gestures_str,
            'output': output,
            'confidence': round(confidence, 2)
        }
        
        self.entries.append(entry)
        
        # Write to CSV
        try:
            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp,
                    mode,
                    language,
                    gestures_str,
                    output,
                    round(confidence, 2)
                ])
        except Exception as e:
            print(f"[Logger Error] Failed to write log: {e}")
    
    def get_session_stats(self):
        """Get statistics for current session."""
        if not self.entries:
            return {
                'total_recognitions': 0,
                'session_duration': 0,
                'modes_used': {},
                'languages_used': {}
            }
        
        duration = (datetime.now() - self.session_start).total_seconds()
        
        modes = {}
        languages = {}
        
        for entry in self.entries:
            mode = entry['mode']
            lang = entry['language']
            modes[mode] = modes.get(mode, 0) + 1
            languages[lang] = languages.get(lang, 0) + 1
        
        return {
            'total_recognitions': len(self.entries),
            'session_duration': duration,
            'modes_used': modes,
            'languages_used': languages
        }
    
    def get_recent_entries(self, count=10):
        """Get the most recent log entries."""
        return self.entries[-count:] if self.entries else []
    
    def export_session(self, filepath=None):
        """Export current session to a separate file."""
        if not filepath:
            filepath = os.path.join(
                self.log_dir,
                f'session_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'timestamp', 'mode', 'language', 'gestures', 'output', 'confidence'
                ])
                writer.writeheader()
                writer.writerows(self.entries)
            return filepath
        except Exception as e:
            print(f"[Logger Error] Failed to export: {e}")
            return None
