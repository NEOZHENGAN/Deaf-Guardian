# 🛡️ Deaf-Guardian

**Bridging the Accessibility Gap through Edge AI and Open-Hardware**

**Hackathon Track:** Track 03: Open (General Technical Invention)

Deaf-Guardian is a cross-disciplinary hardware-software IoT prototype designed to equalize situational awareness and enhance two-way communication for deaf and hard-of-hearing individuals. By combining real-time Edge AI with a production-ready custom PCB architecture, we deliver a scalable, privacy-first accessibility solution.

---

## ✨ Core Features & Safety Logic

### 1. Two-Way Inclusive Communication
- **Deaf-to-Hearing (Gesture AI):** Real-time, one-handed gesture recognition (MediaPipe) translates simple sign language into UI text logs and automatically outputs spoken audio for others to hear.
- **Hearing-to-Deaf (Audio AI):** Real-time speech-to-text processing (Vosk) captures spoken words and converts them into visual yellow text captions on the UI log.

### 2. Multi-Modal Hazard Perception
- **Ambient Audio Monitoring:** A 16kHz I2S audio pipeline continuously monitors environmental noise levels. Sudden loud noises exceeding our safety threshold (Peak > 25,000) immediately trigger visual warnings (e.g., `AUDIO HAZARD DETECTED!`) and haptic vibration feedback.
- **Vision-Based Threat Detection:** Powered by YOLOv8, the system identifies dangerous objects in the environment (such as scissors or knives), autonomously triggering a visual hazard alert and instantly capturing a snapshot of the threat.

### 3. Emergency SOS System
Users can trigger a distress signal via a prominent manual UI button or by performing a specific "closed-fist" gesture. This autonomously logs the SOS event and saves an immediate camera snapshot for evidentiary reference.

### 4. Privacy-First Data Architecture
To protect user privacy and optimize storage, **all real-time communication logs are highly volatile and completely cleared upon system shutdown.** However, critical safety snapshots triggered by autonomous hazard alerts or manual SOS events are securely and permanently saved to local storage.

---

## 🛠️ Technology Stack

- **Edge AI & Software Pipeline:** Python, PyQt5 (UI Interface), YOLOv8 (Object/Hazard Detection), MediaPipe (Gesture Tracking), Vosk (Offline Speech-to-Text), OpenCV (Computer Vision).
- **Hardware Architecture:** Custom 2-layer Raspberry Pi HAT PCB featuring isolated ground-poured I2S audio routing and a low-side MOSFET haptic motor driver.

> **💡 Note on MVP Strategy:**
> Our current MVP deliberately prioritizes the rigorous validation of our complex AI software pipeline and the finalization of our DFM (Design for Manufacturing) PCB blueprints. Instead of presenting a messy breadboard prototype, we have fully de-risked the intelligent "brain" (Edge AI) and designed the complete "skeleton" (100% production-ready schematics). The core engineering is proven and strictly ready for physical manufacturing.

---

## 📁 Repository Structure

```
Deaf-Guardian/
├── docs/                  # Documentation
├── hardware&production/   # PCB design files & production-ready schematics
└── Snapshots/             # Auto-saved hazard/SOS snapshot images
```

---

## 🚀 How to Run Locally

### Prerequisites
Ensure you have Python 3.8+ installed. You will also need a functional webcam and microphone connected to your system.

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/NEOZHENGAN/Deaf-Guardian.git
   cd Deaf-Guardian
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Ensure you have created a `requirements.txt` containing packages like `PyQt5`, `opencv-python`, `mediapipe`, `ultralytics`, `vosk`, and `pyaudio`)*

3. **Verify AI Models:**
   Ensure the following model files are present in your root directory:
   - `yolov8n.pt`
   - `gesture_recognizer.task`
   - `vosk_model/` (Extracted Vosk language model folder)

4. **Launch the Application:**
   ```bash
   python main_ui.py
   ```