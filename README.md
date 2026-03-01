# 🤟 Indian Sign Language Recognition System

A production-grade Python desktop application for real-time Indian Sign Language (ISL) recognition with continuous sentence formation, multi-language text-to-speech, and accessibility-first design.

## ✨ Features

### Three Recognition Modes
- **🔴 Sentence Mode**: Recognize daily-life ISL phrases and form natural sentences
- **🟡 Alphabet Mode**: Recognize A-Z letters for name spelling
- **🟢 Numbers Mode**: Recognize 0-20 using finger counting

### Key Capabilities
- ✅ Real-time hand detection using MediaPipe
- ✅ 10-second continuous gesture recording
- ✅ Natural sentence formation from multiple gestures
- ✅ Multi-language TTS (English, Hindi, Tamil)
- ✅ Accessibility-first UI design
- ✅ Session logging for therapists/caregivers

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /home/invinciblx777/mvp
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python main.py
```

## 📋 Supported Gestures

### Sentence Mode (Daily Life)
| Category | Gestures |
|----------|----------|
| Emergency | HELP, EMERGENCY, DOCTOR, HOSPITAL, PAIN, POLICE |
| Greetings | HELLO, BYE, HOW_ARE_YOU, I_AM_FINE |
| Essential | THANK_YOU, PLEASE, SORRY, YES, NO |
| Actions | STOP, COME_HERE |
| Needs | WATER, FOOD, WASHROOM |
| Identity | I, AM, NAME |

### How to Sign (Examples)
- **HELLO**: Wave with open palm, all fingers extended
- **HELP**: Both hands raised with palms open
- **YES**: Closed fist with nodding motion
- **NO**: Peace sign (V) with palm forward
- **THANK_YOU**: Flat hand moving from chin outward
- **WATER**: W shape (3 fingers) moving to mouth

## 🎯 Usage Example

1. Launch the application
2. Select **Mode: Sentence** and **Language: English**
3. Click **▶ Start Recording**
4. Sign: HELLO → I → AM → [spell your name]
5. The system outputs: **"Hello, I am [Name]."**
6. The sentence is spoken aloud automatically

## 📁 Project Structure

```
mvp/
├── main.py                 # Application entry point
├── config.py               # Configuration settings
├── requirements.txt        # Dependencies
├── modules/
│   ├── hand_detector.py    # MediaPipe hand detection
│   ├── gesture_recognizer.py # Gesture recognition (3 modes)
│   ├── sentence_former.py  # Continuous gesture → sentence
│   ├── tts_engine.py       # Multi-language TTS
│   └── logger.py           # Session logging
├── ui/
│   ├── app.py              # Main application UI
│   └── styles.py           # Accessibility-first styling
└── data/
    └── logs/               # Session logs (CSV)
```

## 🌐 Language Support

| Language | TTS Engine | Status |
|----------|------------|--------|
| English  | pyttsx3    | ✅ Full support |
| Hindi    | gTTS       | ✅ Full support |
| Tamil    | gTTS       | ✅ Full support |

## ♿ Accessibility Features

- Large, readable fonts (16px minimum)
- High contrast dark theme
- Large click targets (48px minimum)
- Clear visual feedback
- Keyboard navigation support

## 📊 Logging

Sessions are automatically logged to `data/logs/session_YYYY-MM-DD.csv` with:
- Timestamp
- Mode used
- Language
- Detected gestures
- Final output
- Confidence score

## ⚙️ Configuration

Edit `config.py` to customize:
- Camera settings (index, resolution)
- Detection confidence thresholds
- Recording duration (default: 10 seconds)
- UI colors and fonts
- BIS compliance settings (IS 13252 / IS 16333)

## 🛡️ BIS Compliance

This system is developed following Bureau of Indian Standards (BIS) guidelines for software safety and reliability:

### IS 13252 - Information Technology Equipment Safety

The software implementation adheres to IS 13252 principles:

| Feature | Implementation |
|---------|----------------|
| **Input Validation** | All user inputs and external data are validated before processing |
| **Error Handling** | Graceful degradation under fault conditions with recovery mechanisms |
| **Resource Management** | Proper allocation, tracking, and cleanup of system resources |
| **Data Integrity** | Checksums and validation for data integrity verification |
| **Audit Logging** | Comprehensive safety event logging in `data/logs/safety_audit.log` |

### IS 16333 - Camera-based Systems (Ready for Hardware Integration)

The system is designed for future compliance with IS 16333:

| Feature | Implementation |
|---------|----------------|
| **Camera Validation** | Initialization verification and frame quality checks |
| **Frame Quality** | Brightness and contrast monitoring for reliable detection |
| **Privacy Protection** | Privacy mode option to prevent frame storage |
| **System Monitoring** | Continuous health monitoring and error tracking |

### Compliance Files

- `modules/bis_compliance.py` - Core BIS compliance module
- `data/logs/safety_audit.log` - Safety event audit trail
- `data/logs/compliance_report.txt` - Generated compliance report (on shutdown)

### Generating Compliance Report

```python
from modules.bis_compliance import generate_compliance_report, get_compliance_info

# Get compliance info as dictionary
info = get_compliance_info()

# Generate human-readable report
report = generate_compliance_report()
print(report)
```

## 🔧 Requirements

- Python 3.8+
- Webcam
- Internet connection (for Tamil/Hindi TTS)

## 📁 Project Structure

```
mvp/
├── main.py                 # Application entry point
├── config.py               # Configuration settings (inc. BIS compliance)
├── requirements.txt        # Dependencies
├── modules/
│   ├── hand_detector.py    # MediaPipe hand detection (IS 16333 ready)
│   ├── gesture_recognizer.py # Gesture recognition (3 modes)
│   ├── sentence_former.py  # Continuous gesture → sentence
│   ├── tts_engine.py       # Multi-language TTS
│   ├── logger.py           # Session logging
│   └── bis_compliance.py   # BIS compliance module (IS 13252 / IS 16333)
├── ui/
│   ├── app.py              # Main application UI (BIS compliant)
│   └── styles.py           # Accessibility-first styling
└── data/
    └── logs/               # Session logs, safety audit, compliance reports
```

## 📝 License

Built for accessibility and inclusion. Use responsibly.

## 🏛️ Standards Compliance Statement

> "At the software level, this sign language detection system follows BIS-aligned guidelines such as IS 13252 for safe and reliable IT systems, with future readiness for IS 16333 camera-based compliance when hardware integration is done."

