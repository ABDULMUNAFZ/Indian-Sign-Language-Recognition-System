"""
Text-to-Speech Engine
Multi-language support for English, Hindi, and Tamil
"""

import os
import threading
import tempfile
import config

# Try different TTS backends
TTS_BACKEND = None

try:
    import pyttsx3
    TTS_BACKEND = 'pyttsx3'
except ImportError:
    pass

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except:
    PYGAME_AVAILABLE = False


class TTSEngine:
    """
    Text-to-Speech engine with multi-language support.
    
    Languages:
    - English (en): pyttsx3 or gTTS
    - Hindi (hi): pyttsx3 (if voice available) or gTTS
    - Tamil (ta): gTTS (required for proper pronunciation)
    """
    
    def __init__(self):
        self.current_language = 'en'
        self.is_speaking = False
        self.pyttsx_engine = None
        self.temp_files = []
        
        # Initialize pyttsx3 if available
        if TTS_BACKEND == 'pyttsx3':
            try:
                self.pyttsx_engine = pyttsx3.init()
                self.pyttsx_engine.setProperty('rate', 150)  # Slower for clarity
                self.pyttsx_engine.setProperty('volume', 1.0)
            except:
                self.pyttsx_engine = None
        
        # Language code mappings
        self.lang_codes = {
            'en': 'en',
            'English': 'en',
            'hi': 'hi',
            'Hindi': 'hi', 
            'ta': 'ta',
            'Tamil': 'ta'
        }
        
        # Translations for common phrases
        self.translations = {
            'hi': {
                'Hello': 'नमस्ते',
                'Goodbye': 'अलविदा',
                'Thank you': 'धन्यवाद',
                'Please': 'कृपया',
                'Sorry': 'माफ़ कीजिए',
                'Yes': 'हाँ',
                'No': 'नहीं',
                'Help': 'मदद',
                'Emergency': 'आपातकाल',
                'Doctor': 'डॉक्टर',
                'Hospital': 'अस्पताल',
                'Police': 'पुलिस',
                'Water': 'पानी',
                'Food': 'खाना',
                'I am': 'मैं हूँ',
                'How are you?': 'आप कैसे हैं?',
                'I am fine': 'मैं ठीक हूँ',
                'Stop': 'रुको',
                'Come here': 'यहाँ आओ',
                'My name is': 'मेरा नाम है',
                'I need the washroom': 'मुझे शौचालय जाना है',
                'I am in pain': 'मुझे दर्द हो रहा है',
                'Good': 'अच्छा',
                'Bad': 'बुरा',
                'I love you': 'मैं तुमसे प्यार करता हूँ',
                'Rock on!': 'बहुत बढ़िया',
                'I promise': 'मैं वादा करता हूँ',
                'Victory!': 'जीत',
                'Call me': 'मुझे फोन करो',
                'Wait': 'रुको',
                'Three': 'तीन',
                'Four': 'चार',
            },
            'ta': {
                'Hello': 'வணக்கம்',
                'Goodbye': 'பிரியாவிடை',
                'Thank you': 'நன்றி',
                'Please': 'தயவுசெய்து',
                'Sorry': 'மன்னிக்கவும்',
                'Yes': 'ஆம்',
                'No': 'இல்லை',
                'Help': 'உதவி',
                'Emergency': 'அவசரநிலை',
                'Doctor': 'மருத்துவர்',
                'Hospital': 'மருத்துவமனை',
                'Police': 'காவல்துறை',
                'Water': 'தண்ணீர்',
                'Food': 'உணவு',
                'I am': 'நான்',
                'How are you?': 'நீங்கள் எப்படி இருக்கிறீர்கள்?',
                'I am fine': 'நான் நலமாக இருக்கிறேன்',
                'Stop': 'நிறுத்து',
                'Come here': 'இங்கே வா',
                'My name is': 'என் பெயர்',
                'I need the washroom': 'எனக்கு கழிவறை தேவை',
                'I am in pain': 'எனக்கு வலிக்கிறது',
            }
        }
    
    def set_language(self, language):
        """Set the output language."""
        self.current_language = self.lang_codes.get(language, 'en')
    
    def get_language(self):
        """Get current language code."""
        return self.current_language
    
    def translate(self, text, target_lang=None):
        """Translate text to target language if translation exists."""
        lang = target_lang or self.current_language
        
        if lang == 'en':
            return text
        
        if lang in self.translations:
            # Check for exact match first
            if text in self.translations[lang]:
                return self.translations[lang][text]
            
            # Try to translate parts
            translated = text
            for en, trans in sorted(self.translations[lang].items(), key=lambda x: -len(x[0])):
                translated = translated.replace(en, trans)
            
            return translated
        
        return text
    
    def speak(self, text, language=None):
        """
        Speak the text in the specified language.
        
        Args:
            text: Text to speak
            language: Optional language override
        """
        if not text:
            return
        
        lang = self.lang_codes.get(language, None) or self.current_language
        
        # Translate if needed
        translated_text = self.translate(text, lang)
        
        # Speak in a separate thread to not block UI
        thread = threading.Thread(target=self._speak_async, args=(translated_text, lang))
        thread.daemon = True
        thread.start()
    
    def _speak_async(self, text, lang):
        """Async speech synthesis."""
        self.is_speaking = True
        
        try:
            # For Tamil, always use gTTS (required for proper pronunciation)
            if lang == 'ta' and GTTS_AVAILABLE:
                self._speak_gtts(text, lang)
            # For Hindi, prefer gTTS for better pronunciation
            elif lang == 'hi' and GTTS_AVAILABLE:
                self._speak_gtts(text, lang)
            # For English, use pyttsx3 if available (faster, offline)
            elif self.pyttsx_engine is not None:
                self._speak_pyttsx3(text)
            # Fallback to gTTS
            elif GTTS_AVAILABLE:
                self._speak_gtts(text, lang)
            else:
                print(f"[TTS] No TTS engine available. Text: {text}")
        except Exception as e:
            print(f"[TTS Error] {e}")
        finally:
            self.is_speaking = False
    
    def _speak_pyttsx3(self, text):
        """Speak using pyttsx3 (offline)."""
        try:
            self.pyttsx_engine.say(text)
            self.pyttsx_engine.runAndWait()
        except Exception as e:
            print(f"[pyttsx3 Error] {e}")
    
    def _speak_gtts(self, text, lang):
        """Speak using Google TTS."""
        try:
            # Create temp file
            fd, temp_path = tempfile.mkstemp(suffix='.mp3')
            os.close(fd)
            
            # Generate speech
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(temp_path)
            
            # Play using pygame
            if PYGAME_AVAILABLE:
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                pygame.mixer.music.unload()
            
            # Clean up
            try:
                os.remove(temp_path)
            except:
                pass
                
        except Exception as e:
            print(f"[gTTS Error] {e}")
            # Fallback to pyttsx3 for English
            if self.pyttsx_engine and lang == 'en':
                self._speak_pyttsx3(text)
    
    def stop(self):
        """Stop any ongoing speech."""
        self.is_speaking = False
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.music.stop()
            except:
                pass
    
    def cleanup(self):
        """Clean up resources."""
        self.stop()
        for temp_file in self.temp_files:
            try:
                os.remove(temp_file)
            except:
                pass
