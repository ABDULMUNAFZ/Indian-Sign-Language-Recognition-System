"""
Main Application UI
ISL Recognition System Desktop Application

BIS Compliance:
- IS 13252: Implements safe software practices, error handling, and audit logging
- IS 16333: Camera-based system safety checks (Ready for hardware integration)
"""

import customtkinter as ctk
from PIL import Image, ImageTk
import cv2
import threading
import time

import config
from ui.styles import (
    APPEARANCE_MODE, COLORS, FONTS, 
    BUTTON_STYLES, FRAME_STYLES, LABEL_STYLES, PROGRESS_STYLES
)
from modules.hand_detector import HandDetector
from modules.gesture_recognizer import GestureRecognizer, GESTURE_GUIDE
from modules.sentence_former import SentenceFormer
from modules.tts_engine import TTSEngine
from modules.logger import SessionLogger

# Import BIS compliance components
try:
    from modules.bis_compliance import (
        SafetyMonitor, ResourceManager, CameraSystemSafety,
        get_compliance_info, generate_compliance_report,
        safe_execute
    )
    BIS_COMPLIANCE_AVAILABLE = True
except ImportError:
    BIS_COMPLIANCE_AVAILABLE = False



class ISLApp(ctk.CTk):
    """
    Main Application Class for ISL Recognition System.
    
    Features:
    - Real-time camera view with hand detection
    - Three recognition modes (Sentence, Alphabet, Numbers)
    - Multi-language TTS output
    - Gesture guide panel
    - Accessibility-first design
    
    BIS Compliance (IS 13252 / IS 16333):
    - Safety monitoring and audit logging
    - Resource management and proper cleanup
    - Camera system validation
    - Error handling and graceful degradation
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize BIS compliance first (IS 13252)
        if BIS_COMPLIANCE_AVAILABLE:
            self.safety_monitor = SafetyMonitor()
            self.resource_manager = ResourceManager()
            self.camera_safety = CameraSystemSafety()
            self.safety_monitor.report_info(
                "ISLApp",
                "Application starting with BIS compliance enabled",
                {'standards': ['IS 13252', 'IS 16333']}
            )
        else:
            self.safety_monitor = None
            self.resource_manager = None
            self.camera_safety = None
        
        # Configure window
        self.title(f"🤟 {config.APP_NAME}")
        self.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.minsize(900, 600)
        
        # Set appearance
        ctk.set_appearance_mode(APPEARANCE_MODE)
        ctk.set_default_color_theme("blue")
        
        self.configure(fg_color=COLORS['bg_dark'])
        
        # Initialize components with error handling (IS 13252)
        try:
            self.hand_detector = HandDetector()
            self.gesture_recognizer = GestureRecognizer()
            self.sentence_former = SentenceFormer()
            self.tts_engine = TTSEngine()
            self.logger = SessionLogger()
            
            # Register resources for managed cleanup (IS 13252)
            if self.resource_manager:
                self.resource_manager.register("hand_detector", self.hand_detector)
                self.resource_manager.register("tts_engine", self.tts_engine)
        except Exception as e:
            if self.safety_monitor:
                self.safety_monitor.report_error(
                    "ISLApp",
                    e,
                    recoverable=False
                )
            raise
        
        # State variables
        self.is_running = True
        self.is_camera_active = False
        self.current_mode = 'sentence'
        self.current_language = 'English'
        self.current_gesture = None
        self.final_output = ""
        self.cap = None
        
        # Build UI
        self._create_ui()
        
        # Start camera
        self._start_camera()
        
        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_ui(self):
        """Create the main UI layout."""
        # Configure grid
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        self._create_header()
        
        # Main content area
        self._create_main_content()
        
        # Status bar
        self._create_status_bar()
    
    def _create_header(self):
        """Create the header with controls."""
        header = ctk.CTkFrame(self, fg_color=COLORS['bg_medium'], corner_radius=0, height=70)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        header.grid_propagate(False)
        
        # Title
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=20, pady=10)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="🤟 ISL Recognition System",
            font=FONTS['header'],
            text_color=COLORS['text_primary']
        )
        title_label.pack(side="left")
        
        # Controls frame
        controls_frame = ctk.CTkFrame(header, fg_color="transparent")
        controls_frame.pack(side="right", padx=20, pady=10)
        
        # Language selector
        lang_label = ctk.CTkLabel(
            controls_frame,
            text="Language:",
            font=FONTS['normal'],
            text_color=COLORS['text_secondary']
        )
        lang_label.pack(side="left", padx=(0, 5))
        
        self.language_var = ctk.StringVar(value="English")
        language_menu = ctk.CTkOptionMenu(
            controls_frame,
            values=["English", "Hindi", "Tamil"],
            variable=self.language_var,
            command=self._on_language_change,
            width=120,
            height=40,
            fg_color=COLORS['bg_light'],
            button_color=COLORS['accent'],
            button_hover_color=COLORS['accent_hover'],
            font=FONTS['normal']
        )
        language_menu.pack(side="left", padx=5)
        
        # Mode selector
        mode_label = ctk.CTkLabel(
            controls_frame,
            text="Mode:",
            font=FONTS['normal'],
            text_color=COLORS['text_secondary']
        )
        mode_label.pack(side="left", padx=(20, 5))
        
        self.mode_var = ctk.StringVar(value="Sentence")
        mode_menu = ctk.CTkOptionMenu(
            controls_frame,
            values=["Sentence", "Alphabet", "Numbers"],
            variable=self.mode_var,
            command=self._on_mode_change,
            width=140,
            height=40,
            fg_color=COLORS['bg_light'],
            button_color=COLORS['accent'],
            button_hover_color=COLORS['accent_hover'],
            font=FONTS['normal']
        )
        mode_menu.pack(side="left", padx=5)
    
    def _create_main_content(self):
        """Create the main content area."""
        # Left panel (Camera + Output)
        left_panel = ctk.CTkFrame(self, fg_color="transparent")
        left_panel.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        left_panel.grid_rowconfigure(0, weight=3)
        left_panel.grid_rowconfigure(1, weight=2)
        left_panel.grid_columnconfigure(0, weight=1)
        
        # Camera view
        self._create_camera_panel(left_panel)
        
        # Output panel
        self._create_output_panel(left_panel)
        
        # Right panel (Gesture Guide)
        self._create_gesture_guide()
    
    def _create_camera_panel(self, parent):
        """Create the camera view panel."""
        camera_frame = ctk.CTkFrame(
            parent,
            fg_color=COLORS['bg_medium'],
            corner_radius=15
        )
        camera_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        camera_frame.grid_rowconfigure(1, weight=1)
        camera_frame.grid_columnconfigure(0, weight=1)
        
        # Camera header
        cam_header = ctk.CTkFrame(camera_frame, fg_color="transparent", height=40)
        cam_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 0))
        
        cam_title = ctk.CTkLabel(
            cam_header,
            text="📹 Camera View",
            font=FONTS['subheader'],
            text_color=COLORS['text_primary']
        )
        cam_title.pack(side="left")
        
        # Current gesture indicator
        self.gesture_indicator = ctk.CTkLabel(
            cam_header,
            text="",
            font=FONTS['large'],
            text_color=COLORS['success']
        )
        self.gesture_indicator.pack(side="right")
        
        # Camera canvas
        self.camera_label = ctk.CTkLabel(
            camera_frame,
            text="Camera loading...",
            font=FONTS['large'],
            text_color=COLORS['text_secondary']
        )
        self.camera_label.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
    
    def _create_output_panel(self, parent):
        """Create the output/result panel."""
        output_frame = ctk.CTkFrame(
            parent,
            fg_color=COLORS['bg_medium'],
            corner_radius=15
        )
        output_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        output_frame.grid_columnconfigure(0, weight=1)
        
        # Output header
        out_header = ctk.CTkFrame(output_frame, fg_color="transparent", height=40)
        out_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 0))
        
        out_title = ctk.CTkLabel(
            out_header,
            text="📝 Output",
            font=FONTS['subheader'],
            text_color=COLORS['text_primary']
        )
        out_title.pack(side="left")
        
        # Recording progress
        self.progress_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        self.progress_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Press 'Start Recording' to begin",
            font=FONTS['normal'],
            text_color=COLORS['text_secondary']
        )
        self.progress_label.pack(side="left")
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            width=200,
            height=10,
            progress_color=COLORS['accent'],
            fg_color=COLORS['bg_light']
        )
        self.progress_bar.pack(side="right", padx=10)
        self.progress_bar.set(0)
        
        # Output text
        self.output_text = ctk.CTkLabel(
            output_frame,
            text="Waiting for gestures...",
            font=FONTS['output'],
            text_color=COLORS['success'],
            wraplength=500
        )
        self.output_text.grid(row=2, column=0, sticky="ew", padx=15, pady=10)
        
        # Detected gestures list
        self.gestures_label = ctk.CTkLabel(
            output_frame,
            text="",
            font=FONTS['normal'],
            text_color=COLORS['text_secondary']
        )
        self.gestures_label.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 5))
        
        # Button frame
        button_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        button_frame.grid(row=4, column=0, sticky="ew", padx=15, pady=10)
        
        # Start/Stop Recording button
        self.record_button = ctk.CTkButton(
            button_frame,
            text="▶ Start Recording",
            command=self._toggle_recording,
            font=FONTS['normal'],
            height=BUTTON_STYLES['primary']['height'],
            fg_color=COLORS['success'],
            hover_color='#3db892',
            corner_radius=10
        )
        self.record_button.pack(side="left", padx=5)
        
        # Speak button
        self.speak_button = ctk.CTkButton(
            button_frame,
            text="🔊 Speak",
            command=self._speak_output,
            font=FONTS['normal'],
            height=48,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            corner_radius=10
        )
        self.speak_button.pack(side="left", padx=5)
        
        # Clear button
        self.clear_button = ctk.CTkButton(
            button_frame,
            text="🗑 Clear",
            command=self._clear_output,
            font=FONTS['normal'],
            height=48,
            fg_color=COLORS['bg_light'],
            hover_color=COLORS['bg_medium'],
            corner_radius=10
        )
        self.clear_button.pack(side="left", padx=5)
    
    def _create_gesture_guide(self):
        """Create the gesture guide panel."""
        guide_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS['bg_medium'],
            corner_radius=15
        )
        guide_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        guide_frame.grid_rowconfigure(1, weight=1)
        guide_frame.grid_columnconfigure(0, weight=1)
        
        # Guide header
        guide_header = ctk.CTkFrame(guide_frame, fg_color="transparent", height=40)
        guide_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 0))
        
        guide_title = ctk.CTkLabel(
            guide_header,
            text="📘 Gesture Guide",
            font=FONTS['subheader'],
            text_color=COLORS['text_primary']
        )
        guide_title.pack(side="left")
        
        # Scrollable gesture list
        self.guide_scroll = ctk.CTkScrollableFrame(
            guide_frame,
            fg_color="transparent",
            corner_radius=0
        )
        self.guide_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.guide_scroll.grid_columnconfigure(0, weight=1)
        
        # Populate guide
        self._populate_guide()
    
    def _populate_guide(self):
        """Populate the gesture guide based on current mode."""
        # Clear existing
        for widget in self.guide_scroll.winfo_children():
            widget.destroy()
        
        mode_key = self.current_mode
        guide_data = GESTURE_GUIDE.get(mode_key, {})
        
        row = 0
        current_category = None
        
        for gesture_id, info in guide_data.items():
            # Category header
            category = info.get('category', 'Other')
            if category != current_category:
                current_category = category
                cat_label = ctk.CTkLabel(
                    self.guide_scroll,
                    text=f"── {category} ──",
                    font=FONTS['normal'],
                    text_color=COLORS['accent']
                )
                cat_label.grid(row=row, column=0, sticky="w", pady=(10, 5))
                row += 1
            
            # Gesture card
            gesture_card = ctk.CTkFrame(
                self.guide_scroll,
                fg_color=COLORS['bg_light'],
                corner_radius=8
            )
            gesture_card.grid(row=row, column=0, sticky="ew", pady=3)
            gesture_card.grid_columnconfigure(1, weight=1)
            
            # Emoji
            emoji_label = ctk.CTkLabel(
                gesture_card,
                text=info.get('emoji', '✋'),
                font=(config.FONT_FAMILY, 20),
                width=40
            )
            emoji_label.grid(row=0, column=0, rowspan=2, padx=10, pady=5)
            
            # Name
            name_label = ctk.CTkLabel(
                gesture_card,
                text=info.get('name', gesture_id),
                font=FONTS['normal'],
                text_color=COLORS['text_primary'],
                anchor="w"
            )
            name_label.grid(row=0, column=1, sticky="w", padx=5, pady=(5, 0))
            
            # Description
            desc_label = ctk.CTkLabel(
                gesture_card,
                text=info.get('description', ''),
                font=FONTS['small'],
                text_color=COLORS['text_secondary'],
                anchor="w",
                wraplength=200
            )
            desc_label.grid(row=1, column=1, sticky="w", padx=5, pady=(0, 5))
            
            row += 1
    
    def _create_status_bar(self):
        """Create the status bar."""
        status_bar = ctk.CTkFrame(
            self,
            fg_color=COLORS['bg_medium'],
            corner_radius=0,
            height=35
        )
        status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        status_bar.grid_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            status_bar,
            text="Ready | Mode: Sentence | Language: English",
            font=FONTS['small'],
            text_color=COLORS['text_secondary']
        )
        self.status_label.pack(side="left", padx=15, pady=5)
        
        # Version
        version_label = ctk.CTkLabel(
            status_bar,
            text=f"v{config.APP_VERSION}",
            font=FONTS['small'],
            text_color=COLORS['text_secondary']
        )
        version_label.pack(side="right", padx=15, pady=5)
    
    def _start_camera(self):
        """
        Start the camera capture thread with IS 16333 safety validation.
        
        Implements camera system safety checks as per IS 16333 guidelines:
        - Camera initialization verification
        - Frame capture validation
        - Resource registration for managed cleanup
        """
        self.cap = cv2.VideoCapture(config.CAMERA_INDEX)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
        
        # IS 16333 camera validation
        if self.camera_safety:
            is_valid, status_msg = self.camera_safety.validate_camera_initialization(self.cap)
            if not is_valid:
                self.camera_label.configure(text=f"❌ {status_msg}")
                if self.safety_monitor:
                    self.safety_monitor.report_error(
                        "Camera",
                        Exception(f"Camera validation failed: {status_msg}"),
                        recoverable=True
                    )
                return
        
        if self.cap.isOpened():
            self.is_camera_active = True
            
            # Register camera for managed cleanup (IS 13252)
            if self.resource_manager:
                self.resource_manager.register(
                    "camera", 
                    self.cap,
                    cleanup_handler=lambda cap: cap.release()
                )
            
            self.camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
            self.camera_thread.start()
            
            if self.safety_monitor:
                self.safety_monitor.report_info(
                    "Camera",
                    f"Camera started successfully: {config.CAMERA_WIDTH}x{config.CAMERA_HEIGHT}"
                )
        else:
            self.camera_label.configure(text="❌ Camera not available")
            if self.safety_monitor:
                self.safety_monitor.report_error(
                    "Camera",
                    Exception("Camera failed to open"),
                    recoverable=True
                )
    
    def _camera_loop(self):
        """Main camera processing loop - optimized for performance."""
        frame_count = 0
        last_hands_data = None
        
        while self.is_running and self.is_camera_active:
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            frame_count += 1
            
            # Flip for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Only run detection every FRAME_SKIP frames to reduce lag
            if frame_count % config.FRAME_SKIP == 0:
                # Detect hands
                result = self.hand_detector.detect(frame)
                last_hands_data = result['hands']
                display_frame = result['frame']
            else:
                # Use cached hand data, just update frame
                display_frame = frame
                if last_hands_data:
                    # Draw cached landmarks
                    for hand in last_hands_data:
                        self.hand_detector._draw_landmarks(display_frame, hand['landmarks'])
            
            # Recognize gesture using latest hand data
            if last_hands_data:
                recognition = self.gesture_recognizer.recognize(last_hands_data)
                gesture = recognition['gesture']
                confidence = recognition['confidence']
                
                if gesture:
                    self.current_gesture = gesture
                    
                    # Update gesture indicator
                    self.after(0, lambda g=gesture, c=confidence: 
                        self.gesture_indicator.configure(text=f"✓ {g} ({c:.0%})"))
                    
                    # Add to sentence former if recording
                    if self.sentence_former.is_recording:
                        rec_result = self.sentence_former.add_gesture(
                            gesture, confidence, self.current_mode
                        )
                        
                        if rec_result.get('completed'):
                            self.after(0, self._on_recording_complete, rec_result['sentence'])
                        else:
                            self.after(0, self._update_recording_ui, rec_result)
                else:
                    self.after(0, lambda: self.gesture_indicator.configure(text=""))
            else:
                self.after(0, lambda: self.gesture_indicator.configure(text=""))
            
            # Convert frame for display - use faster resize
            frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            # Resize with OpenCV (faster than PIL)
            frame_resized = cv2.resize(frame_rgb, (520, 380), interpolation=cv2.INTER_LINEAR)
            img = Image.fromarray(frame_resized)
            
            # Update UI
            self.after(0, self._update_camera_display, img)
            
            # Minimal sleep - let the loop run as fast as possible
            time.sleep(0.001)
    
    def _update_camera_display(self, img):
        """Update camera display in main thread."""
        try:
            photo = ctk.CTkImage(light_image=img, dark_image=img, size=(520, 380))
            self.camera_label.configure(image=photo, text="")
            self.camera_label.image = photo
        except:
            pass
    
    def _update_recording_ui(self, result):
        """Update recording progress UI."""
        elapsed = result.get('elapsed_time', 0)
        gestures = result.get('gestures', [])
        progress = elapsed / config.GESTURE_BUFFER_DURATION
        
        self.progress_bar.set(progress)
        self.progress_label.configure(text=f"Recording: {elapsed:.1f}s / {config.GESTURE_BUFFER_DURATION}s")
        
        if gestures:
            self.gestures_label.configure(text=f"Detected: {' → '.join(gestures)}")
    
    def _toggle_recording(self):
        """Toggle recording state."""
        if self.sentence_former.is_recording:
            # Stop recording
            sentence = self.sentence_former.stop_recording()
            self._on_recording_complete(sentence)
        else:
            # Start recording
            self.sentence_former.start_recording()
            self.record_button.configure(text="⏹ Stop Recording", fg_color=COLORS['accent'])
            self.progress_label.configure(text="Recording: 0.0s / 10.0s")
            self.gestures_label.configure(text="")
            self.output_text.configure(text="Recording...", text_color=COLORS['warning'])
    
    def _on_recording_complete(self, sentence):
        """Handle recording completion."""
        self.record_button.configure(text="▶ Start Recording", fg_color=COLORS['success'])
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="Recording complete!")
        
        if sentence:
            self.final_output = sentence
            self.output_text.configure(text=sentence, text_color=COLORS['success'])
            
            # Log the recognition
            self.logger.log_recognition(
                mode=self.current_mode,
                language=self.current_language,
                gestures=self.sentence_former.confirmed_gestures,
                output=sentence
            )
            
            # Auto-speak
            self.tts_engine.speak(sentence)
        else:
            self.output_text.configure(text="No gestures detected", text_color=COLORS['text_secondary'])
    
    def _speak_output(self):
        """Speak the current output."""
        if self.final_output:
            self.tts_engine.speak(self.final_output)
    
    def _clear_output(self):
        """Clear the output and reset."""
        self.sentence_former.clear()
        self.final_output = ""
        self.output_text.configure(text="Waiting for gestures...", text_color=COLORS['text_secondary'])
        self.gestures_label.configure(text="")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Press 'Start Recording' to begin")
        self.record_button.configure(text="▶ Start Recording", fg_color=COLORS['success'])
    
    def _on_language_change(self, language):
        """Handle language selection change."""
        self.current_language = language
        self.tts_engine.set_language(language)
        self._update_status()
    
    def _on_mode_change(self, mode):
        """Handle mode selection change."""
        mode_map = {'Sentence': 'sentence', 'Alphabet': 'alphabet', 'Numbers': 'numbers'}
        self.current_mode = mode_map.get(mode, 'sentence')
        self.gesture_recognizer.set_mode(self.current_mode)
        self._populate_guide()  # Refresh guide
        self._update_status()
        self._clear_output()
    
    def _update_status(self):
        """Update status bar."""
        self.status_label.configure(
            text=f"Ready | Mode: {self.mode_var.get()} | Language: {self.current_language}"
        )
    
    def _on_close(self):
        """
        Handle window close with IS 13252 compliant resource cleanup.
        
        Ensures proper release of all resources and generates
        final compliance report before shutdown.
        """
        self.is_running = False
        self.is_camera_active = False
        
        # Log shutdown initiation
        if self.safety_monitor:
            self.safety_monitor.report_info(
                "ISLApp",
                "Application shutdown initiated"
            )
        
        # Use resource manager for managed cleanup (IS 13252)
        if self.resource_manager:
            self.resource_manager.release_all()
        else:
            # Fallback manual cleanup
            if self.cap:
                self.cap.release()
            self.hand_detector.release()
            self.tts_engine.cleanup()
        
        # Generate final compliance report
        if self.safety_monitor and BIS_COMPLIANCE_AVAILABLE:
            self.safety_monitor.report_info(
                "ISLApp",
                "Application shutdown completed successfully"
            )
            # Optionally print compliance report
            try:
                report = generate_compliance_report()
                # Save report to logs
                import os
                report_path = os.path.join(config.LOGS_DIR, 'compliance_report.txt')
                with open(report_path, 'w') as f:
                    f.write(report)
            except:
                pass
        
        self.destroy()


def main():
    """
    Entry point for the ISL Recognition System.
    
    BIS Compliance:
    - Initializes safety monitoring
    - Prints compliance information on startup
    """
    # Print BIS compliance info on startup
    if BIS_COMPLIANCE_AVAILABLE:
        print("=" * 60)
        print("ISL Recognition System - BIS Compliant")
        print("=" * 60)
        print("Standards Implemented:")
        print("  ✓ IS 13252 - IT Equipment Safety")
        print("  ✓ IS 16333 - Camera Systems (Ready)")
        print("=" * 60)
    
    app = ISLApp()
    app.mainloop()


if __name__ == "__main__":
    main()
