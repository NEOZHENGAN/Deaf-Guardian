import cv2
import mediapipe as mp
import time

# 1. Initialize MediaPipe sign language recognizer
BaseOptions = mp.tasks.BaseOptions
GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# load the gesture recognition model
options = GestureRecognizerOptions(
    base_options=BaseOptions(model_asset_path='gesture_recognizer.task'),
    running_mode=VisionRunningMode.IMAGE
)

recognizer = GestureRecognizer.create_from_options(options)

# 2. open the webcam
cap = cv2.VideoCapture(0)
mp_image_format = mp.ImageFormat.SRGB

print("系统已启动！对着摄像头做手势：握拳(求救)、大拇指(OK)、张开手掌(停止)")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
        
    # flip the frame horizontally for a selfie-view display
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp_image_format, data=rgb_frame)

    # 3. recognize the gesture in the frame
    recognition_result = recognizer.recognize(mp_image)

    # 4. show the recognition result on the frame
    if recognition_result.gestures:
        # get the top gesture and its score
        top_gesture = recognition_result.gestures[0][0].category_name
        score = recognition_result.gestures[0][0].score
        
        # UI 
        display_text = ""
        color = (0, 255, 0) # default color: green
        
        if top_gesture == "Closed_Fist":
            display_text = "SOS: I NEED HELP!"
            color = (0, 0, 255) # red color for SOS
            # TODO: vibrate the phone or send an alert to the caregiver
            
        elif top_gesture == "Thumb_Up":
            display_text = "YES / I AM OK"
            
        elif top_gesture == "Open_Palm":
            display_text = "STOP / WAIT"
            
        else:
            display_text = top_gesture

        # type the text on the frame
        cv2.putText(frame, f"{display_text} ({score:.2f})", (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)

    cv2.imshow('Deaf-Guardian Prototype', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()