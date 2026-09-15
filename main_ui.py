import time
import sys
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Native PyQt Thread-safe Text-To-Speech
try:
    from PyQt5.QtTextToSpeech import QTextToSpeech
except ImportError:
    QTextToSpeech = None

from audio_worker import AudioThread
from camera_worker import CameraThread


class DeafGuardianApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Deaf-Guardian MVP - Two-Way Communication & Auto Reset Guardian")
        self.setGeometry(100, 100, 1050, 600)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # === Left Side: Camera Video Feed ===
        left_panel = QVBoxLayout()
        self.video_label = QLabel(self)
        self.video_label.setStyleSheet("background-color: black; border-radius: 10px;")
        self.video_label.setFixedSize(640, 480)
        left_panel.addWidget(self.video_label)
        main_layout.addLayout(left_panel)

        # === Right Side: Status Display & Live Transcript ===
        right_panel = QVBoxLayout()

        self.status_box = QFrame()
        self.status_box.setStyleSheet("background-color: #2c3e50; border-radius: 12px;")
        status_layout = QVBoxLayout(self.status_box)

        self.status_label = QLabel("SYSTEM READY")
        self.status_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.status_label.setStyleSheet("color: white;")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_label)
        right_panel.addWidget(self.status_box)

        self.transcript_box = QTextEdit()
        self.transcript_box.setReadOnly(True)
        self.transcript_box.setPlaceholderText("Two-way conversation history and hazard evidence logs...")
        self.transcript_box.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #f1c40f;
                font-size: 15px;
                font-weight: bold;
                border: 2px solid #34495e;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        right_panel.addWidget(self.transcript_box)

        self.sos_btn = QPushButton("PRESS FOR HELP")
        self.sos_btn.setFont(QFont("Arial", 18, QFont.Bold))
        self.sos_btn.setStyleSheet("""
            QPushButton { background-color: #e74c3c; color: white; border-radius: 15px; padding: 15px; }
            QPushButton:pressed { background-color: #c0392b; }
        """)
        self.sos_btn.clicked.connect(self.trigger_manual_sos)
        right_panel.addWidget(self.sos_btn)

        main_layout.addLayout(right_panel)

        # --- Variables & Timers ---
        self.is_danger = False
        self.flash_timer = QTimer()
        self.flash_timer.timeout.connect(self.toggle_flash)
        self.flash_state = False

        # Danger Auto-Reset Timer (2 seconds auto clear)
        self.danger_reset_timer = QTimer()
        self.danger_reset_timer.setSingleShot(True)
        self.danger_reset_timer.timeout.connect(lambda: self.reset_normal("LISTENING..."))

        # Qt Native TTS Engine
        if QTextToSpeech:
            self.tts = QTextToSpeech(self)
        else:
            self.tts = None

        # --- Threads ---
        self.camera_thread = CameraThread()
        self.camera_thread.change_pixmap_signal.connect(self.update_image)
        self.camera_thread.gesture_signal.connect(self.update_status)
        self.camera_thread.sign_translation_signal.connect(self.handle_sign_translation)
        self.camera_thread.visual_hazard_signal.connect(self.handle_visual_hazard)
        self.camera_thread.start()

        self.audio_thread = AudioThread()
        self.audio_thread.text_signal.connect(self.update_subtitle)
        self.audio_thread.hazard_signal.connect(self.handle_audio_hazard)
        self.audio_thread.start()

    def update_image(self, qt_img):
        self.video_label.setPixmap(
            QPixmap.fromImage(qt_img).scaled(
                self.video_label.width(),
                self.video_label.height(),
                Qt.KeepAspectRatio,
            )
        )

    def update_status(self, gesture, score):
        if not self.is_danger:
            if gesture != "None":
                self.status_label.setText(f"SIGN: {gesture}")
            else:
                self.status_label.setText("LISTENING...")

    def update_subtitle(self, text):
        if text.startswith("🗣️"):
            self.transcript_box.append(text)
            self.transcript_box.verticalScrollBar().setValue(
                self.transcript_box.verticalScrollBar().maximum()
            )

    def handle_sign_translation(self, gesture_name, phrase):
        timestamp = time.strftime("[%H:%M:%S]")
        formatted_msg = f"{timestamp} 🧏 [Deaf User]: \"{phrase}\""
        
        self.transcript_box.append(f"<span style='color: #00ffff;'>{formatted_msg}</span>")
        self.transcript_box.verticalScrollBar().setValue(
            self.transcript_box.verticalScrollBar().maximum()
        )

        # Non-blocking Qt TTS (can be called continuously without freezing)
        if self.tts:
            self.tts.say(phrase)

    def handle_visual_hazard(self, alert_status, log_entry):
        self.trigger_danger(alert_status)
        if log_entry:
            self.transcript_box.append(f"<span style='color: #e74c3c;'>{log_entry}</span>")
            self.transcript_box.verticalScrollBar().setValue(
                self.transcript_box.verticalScrollBar().maximum()
            )

    def handle_audio_hazard(self, alert_status):
        self.trigger_danger(alert_status)
        timestamp_log = time.strftime("[%H:%M:%S]")
        log_entry = f"{timestamp_log} 🔊 {alert_status}"
        self.transcript_box.append(f"<span style='color: #e67e22;'>{log_entry}</span>")
        self.transcript_box.verticalScrollBar().setValue(
            self.transcript_box.verticalScrollBar().maximum()
        )

    def trigger_manual_sos(self):
        self.trigger_danger("MANUAL SOS TRIGGERED!")
        timestamp_log = time.strftime("[%H:%M:%S]")
        log_entry = f"{timestamp_log} 🚨 MANUAL SOS BUTTON PRESSED!"
        self.transcript_box.append(f"<span style='color: #e74c3c;'>{log_entry}</span>")

    def trigger_danger(self, msg):
        self.is_danger = True
        self.status_label.setText(msg)
        if not self.flash_timer.isActive():
            self.flash_timer.start(300)
            try:
                import winsound
                winsound.Beep(2500, 300)
            except:
                print("\a")

        # Refresh the 2-second countdown for danger auto-clear
        self.danger_reset_timer.start(2000)

    def toggle_flash(self):
        if self.flash_state:
            self.status_box.setStyleSheet("background-color: red; border-radius: 12px;")
            self.status_label.setStyleSheet("color: white;")
        else:
            self.status_box.setStyleSheet("background-color: yellow; border-radius: 12px;")
            self.status_label.setStyleSheet("color: black;")
        self.flash_state = not self.flash_state

    def reset_normal(self, msg):
        self.is_danger = False
        self.flash_timer.stop()
        self.status_box.setStyleSheet("background-color: #2c3e50; border-radius: 12px;")
        self.status_label.setStyleSheet("color: white;")
        self.status_label.setText(msg)

    def closeEvent(self, event):
        self.camera_thread.stop()
        self.audio_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DeafGuardianApp()
    window.show()
    sys.exit(app.exec_())