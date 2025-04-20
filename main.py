import cv2
import mediapipe as mp
import pyautogui
import pygetwindow as gw
import time

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# Webcam capture
cap = cv2.VideoCapture(0)
screen_width, screen_height = pyautogui.size()

# Gesture click control variables
right_click_timer = 0
right_click_done = False

def get_active_platform():
    title = gw.getActiveWindowTitle() or ""
    return "youtube" if "YouTube" in title else "other"

def get_finger_status(landmarks):
    tips = [mp_hands.HandLandmark.THUMB_TIP,
            mp_hands.HandLandmark.INDEX_FINGER_TIP,
            mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
            mp_hands.HandLandmark.RING_FINGER_TIP,
            mp_hands.HandLandmark.PINKY_TIP]

    pips = [mp_hands.HandLandmark.THUMB_IP,
            mp_hands.HandLandmark.INDEX_FINGER_PIP,
            mp_hands.HandLandmark.MIDDLE_FINGER_PIP,
            mp_hands.HandLandmark.RING_FINGER_PIP,
            mp_hands.HandLandmark.PINKY_PIP]

    return [landmarks.landmark[tip].y < landmarks.landmark[pip].y for tip, pip in zip(tips, pips)]

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for landmarks in results.multi_hand_landmarks:
            platform = get_active_platform()
            fingers = get_finger_status(landmarks)
            thumb_open, index_open, middle_open, ring_open, pinky_open = fingers

            # Get index and thumb tip coordinates
            index = landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            thumb = landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]

            # Move cursor
            pyautogui.moveTo(int(index.x * screen_width), int(index.y * screen_height), duration=0.01)

            # Distance for pinch
            pinch_x_diff = abs(index.x - thumb.x)
            pinch_y_diff = abs(index.y - thumb.y)
            is_pinch = index_open and thumb_open and pinch_x_diff < 0.05 and pinch_y_diff < 0.05

            if platform == "youtube":
                if index_open and not any([middle_open, ring_open, pinky_open, thumb_open]):
                    print("➡️ Next Reel")
                    pyautogui.press('down')

                elif index_open and middle_open and not any([ring_open, pinky_open, thumb_open]):
                    print("⬅️ Previous Reel")
                    pyautogui.press('up')

                elif all(fingers):
                    print("▶️ Resume")
                    pyautogui.press('space')

                elif not any(fingers):
                    print("⏸️ Pause")
                    pyautogui.press('space')

                elif thumb_open and not any([index_open, middle_open, ring_open, pinky_open]) and thumb.x < 0.2:
                    print("⬅️ Back Page")
                    pyautogui.hotkey('alt', 'left')

                elif pinky_open and not any([index_open, middle_open, ring_open, thumb_open]) and \
                     landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP].x > \
                     landmarks.landmark[mp_hands.HandLandmark.PINKY_PIP].x + 0.1:
                    print("➡️ Forward Page")
                    pyautogui.hotkey('alt', 'right')

                elif index_open and not thumb_open and index.y < 0.4:
                    print("⬆️ Scroll Up")
                    pyautogui.scroll(20)

                elif index_open and thumb_open and pinch_x_diff > 0.15:
                    print("⬇️ Scroll Down")
                    pyautogui.scroll(-20)

                elif is_pinch:
                    print("🔘 Select/Pause")
                    pyautogui.click()
                    time.sleep(0.5)

            # Universal mouse left click
            if is_pinch and not right_click_done:
                print("🖱️ Left Click")
                pyautogui.click()
                right_click_done = True
                time.sleep(0.3)
            elif not is_pinch:
                right_click_done = False

            # Right click when holding pinch >1.2s
            if is_pinch:
                if right_click_timer == 0:
                    right_click_timer = time.time()
                elif time.time() - right_click_timer > 1.2:
                    print("🖱️ Right Click")
                    pyautogui.click(button='right')
                    time.sleep(0.5)
                    right_click_timer = 0
            else:
                right_click_timer = 0

            mp_drawing.draw_landmarks(frame, landmarks, mp_hands.HAND_CONNECTIONS)

    cv2.imshow("Gesture + Virtual Mouse (Right Hand)", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()