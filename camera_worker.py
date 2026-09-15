import os
import time
import cv2
import mediapipe as mp
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
from ultralytics import YOLO

# ----------------------------------------------------
# Camera Background Thread (Sign Translation + YOLO Tracking + Auto Reset)
# ----------------------------------------------------
class CameraThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    gesture_signal = pyqtSignal(str, float)
    sign_translation_signal = pyqtSignal(str, str)
    visual_hazard_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self._run_flag = True

        self.last_snapshot_time = 0
        self.snapshot_cooldown = 3.0
        
        # Gesture Debounce & Translation State
        self.current_holding_gesture = "None"
        self.gesture_hold_start_time = 0
        self.last_translated_gesture = "None"
        self.gesture_hold_threshold = 1.0  # Hold for 1 second to confirm

        self.sign_dictionary = {
            "ILoveYou": "Thank you! / I love you!",
            "Thumb_Up": "Yes, I agree.",
            "Thumb_Down": "No, thank you.",
            "Open_Palm": "Hello! Please wait a moment.",
            "Victory": "Everything is okay.",
            "Pointing_Up": "Excuse me, I need assistance."
        }

        self.snapshot_dir = "snapshots"
        os.makedirs(self.snapshot_dir, exist_ok=True)

        BaseOptions = mp.tasks.BaseOptions
        GestureRecognizer = mp.tasks.vision.GestureRecognizer
        options = mp.tasks.vision.GestureRecognizerOptions(
            base_options=BaseOptions(model_asset_path="gesture_recognizer.task"),
            running_mode=mp.tasks.vision.RunningMode.IMAGE,
        )
        self.recognizer = GestureRecognizer.create_from_options(options)

        print("🔍 [DEBUG] Loading YOLOv8n model...")
        self.yolo_model = YOLO("yolov8n.pt")
        self.hazard_classes = ["knife", "scissors"]

    def run(self):
        cap = cv2.VideoCapture(0)
        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                cv_img = cv2.flip(cv_img, 1)

                # --- 1. YOLOv8 Object Tracking ---
                yolo_results = self.yolo_model.track(
                    cv_img, persist=True, verbose=False, conf=0.5
                )[0]
                
                hazard_detected = False
                detected_class_name = ""
                detected_track_id = "N/A"

                if yolo_results.boxes is not None:
                    for box in yolo_results.boxes:
                        class_id = int(box.cls[0])
                        class_name = self.yolo_model.names[class_id]
                        confidence = float(box.conf[0])
                        track_id = int(box.id[0]) if box.id is not None else "N/A"

                        if class_name in self.hazard_classes:
                            hazard_detected = True
                            detected_class_name = class_name
                            detected_track_id = track_id

                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            center_x = int((x1 + x2) / 2)
                            center_y = int((y1 + y2) / 2)

                            cv2.rectangle(cv_img, (x1, y1), (x2, y2), (0, 0, 255), 3)
                            cv2.circle(cv_img, (center_x, center_y), 5, (0, 255, 255), -1)

                            cv2.putText(
                                cv_img,
                                f"TRACK #{track_id} | HAZARD: {class_name.upper()} {confidence:.2f}",
                                (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                (0, 0, 255),
                                2,
                            )

                # --- 2. MediaPipe Gesture Recognition ---
                rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_img)
                result = self.recognizer.recognize(mp_image)

                top_gesture = "None"
                score = 0.0
                if result.gestures:
                    top_gesture = result.gestures[0][0].category_name
                    score = result.gestures[0][0].score

                self.gesture_signal.emit(top_gesture, score)

                # --- 3. Sign Translation Logic (Fixed Re-triggering) ---
                now = time.time()
                if top_gesture in self.sign_dictionary:
                    if top_gesture != self.current_holding_gesture:
                        self.current_holding_gesture = top_gesture
                        self.gesture_hold_start_time = now
                    else:
                        if (now - self.gesture_hold_start_time > self.gesture_hold_threshold) and (top_gesture != self.last_translated_gesture):
                            self.last_translated_gesture = top_gesture
                            phrase = self.sign_dictionary[top_gesture]
                            self.sign_translation_signal.emit(top_gesture, phrase)
                else:
                    # Clear state immediately when gesture drops or changes
                    self.current_holding_gesture = "None"
                    self.last_translated_gesture = "None"

                # --- 4. Hazard & SOS Logic ---
                if hazard_detected:
                    alert_status = f"VISUAL HAZARD: {detected_class_name.upper()} DETECTED!"
                    log_entry = ""

                    if now - self.last_snapshot_time > self.snapshot_cooldown:
                        self.last_snapshot_time = now
                        date_str = time.strftime("%Y-%m-%d")
                        time_str = time.strftime("[%H:%M:%S]")
                        timestamp_filename = time.strftime("%Y%m%d_%H%M%S")

                        snapshot_img = cv_img.copy()
                        banner_text = f"{date_str} {time_str} HAZARD DETECTED: {detected_class_name.upper()} (TRACK #{detected_track_id})"
                        
                        cv2.rectangle(snapshot_img, (0, 0), (cv_img.shape[1], 45), (0, 0, 0), -1)
                        cv2.putText(
                            snapshot_img,
                            banner_text,
                            (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 0, 255),
                            2,
                            cv2.LINE_AA,
                        )

                        filepath = os.path.join(self.snapshot_dir, f"hazard_{timestamp_filename}.jpg")
                        cv2.imwrite(filepath, snapshot_img)

                        log_entry = f"{date_str} {time_str} 🚨 HAZARD DETECTED: {detected_class_name.upper()} (TRACK #{detected_track_id}) - Snapshot Saved."

                    self.visual_hazard_signal.emit(alert_status, log_entry)

                elif top_gesture == "Closed_Fist":
                    alert_status = "GESTURE SOS: HELP!"
                    log_entry = ""

                    if now - self.last_snapshot_time > self.snapshot_cooldown:
                        self.last_snapshot_time = now
                        date_str = time.strftime("%Y-%m-%d")
                        time_str = time.strftime("[%H:%M:%S]")
                        timestamp_filename = time.strftime("%Y%m%d_%H%M%S")

                        snapshot_img = cv_img.copy()
                        banner_text = f"{date_str} {time_str} GESTURE SOS TRIGGERED"
                        
                        cv2.rectangle(snapshot_img, (0, 0), (cv_img.shape[1], 45), (0, 0, 0), -1)
                        cv2.putText(
                            snapshot_img,
                            banner_text,
                            (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.65,
                            (0, 0, 255),
                            2,
                            cv2.LINE_AA,
                        )

                        filepath = os.path.join(self.snapshot_dir, f"sos_gesture_{timestamp_filename}.jpg")
                        cv2.imwrite(filepath, snapshot_img)

                        log_entry = f"{date_str} {time_str} 🚨 GESTURE SOS TRIGGERED - Snapshot Saved."

                    self.visual_hazard_signal.emit(alert_status, log_entry)

                # Convert frame to QImage for PyQt GUI rendering
                h, w, ch = rgb_img.shape
                bytes_per_line = ch * w
                qt_img = QImage(
                    rgb_img.data, w, h, bytes_per_line, QImage.Format_RGB888
                )
                self.change_pixmap_signal.emit(qt_img)

        cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()