import json
import os
import queue
import sys
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
import sounddevice as sd
from vosk import KaldiRecognizer, Model

# ----------------------------------------------------
# Microphone Background Thread (Audio: Vosk STT + Hazard Noise Detection)
# ----------------------------------------------------
class AudioThread(QThread):
    text_signal = pyqtSignal(str) 
    hazard_signal = pyqtSignal(str)  # Signal triggered when sudden loud noise occurs

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.q = queue.Queue()
        
        # Peak threshold raised to 25000 to prevent false positives from normal speech
        self.peak_threshold = 25000 
        
        # Absolute path to load Vosk model
        model_path = os.path.abspath("vosk_model")
        print(f"🎤 [DEBUG] Loading Vosk model from: {model_path}")
        
        if not os.path.exists(model_path):
            print(f"❌ [ERROR] Folder does NOT exist: {model_path}")
            self._run_flag = False
            return

        try:
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, 16000)
            print("✅ [DEBUG] Vosk model loaded successfully!")
        except Exception as e:
            print("❌ [ERROR] Model loading failed:", e)
            self._run_flag = False

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        
        # Convert audio buffer to int16 numpy array
        audio_data = np.frombuffer(indata, dtype=np.int16)
        
        # Peak Detection: Capture maximum amplitude spike (suited for clapping, screams, or bangs)
        peak_volume = np.max(np.abs(audio_data))
        
        # Debugging: Print peak level in terminal for real-time monitoring
        if peak_volume > 10000:
            print(f"🔊 [AUDIO PEAK]: {peak_volume}")

        if peak_volume > self.peak_threshold:
            self.hazard_signal.emit(f"AUDIO HAZARD DETECTED! ({peak_volume} Peak)")

        self.q.put(bytes(indata))

    def run(self):
        if not self._run_flag:
            return
            
        print("🎤 [DEBUG] Audio thread started, listening...")
        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                               channels=1, callback=self.audio_callback):
            while self._run_flag:
                data = self.q.get()
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "")
                    if text:
                        print(f"[DEBUG Full Sentence] {text}")
                        self.text_signal.emit(f"🗣️ {text}")
                else:
                    partial = json.loads(self.recognizer.PartialResult())
                    partial_text = partial.get("partial", "")
                    if partial_text:
                        print(f"[DEBUG Recognizing...] {partial_text}")
                        self.text_signal.emit(f"💬 {partial_text}...")

    def stop(self):
        self._run_flag = False
        self.wait()