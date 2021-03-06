import time
import json
import cv2
import sys
import numpy as np
import mediapipe as mp


mpPose = mp.solutions.pose
pose = mpPose.Pose()
mpDraw = mp.solutions.drawing_utils


bodyPoints = {'right_inner_foot': (30, 28, 26), 'right_out_foot': (32,28, 26), 'right_knee': (28,26,24),
              'right_elbow': (16,14,12), 'right_shoulder': (14, 12, 24), 'right_hip':(12,24,26),
              'left_inner_foot': (29,27,25),
              'left_out_foot': (31,27,25), 'left_knee': (27,25,23), 'left_elbow': (15,13,11),
              'left_shoulder': (13,11,23), 'left_hip': (11, 23, 25)}

lengPoint = {'left_body': (12, 24), 'right_body': (11, 23)}


def get_new_frame_from_neuron(img):
    """
    This function founds pose landmarks, draws them on img and returns them

    Ids from doc: https://google.github.io/mediapipe/solutions/pose.html

    :return: found landmarks
    """
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = pose.process(img_rgb)
    landmarks = {}
    if results.pose_landmarks:
        mpDraw.draw_landmarks(
            img, results.pose_landmarks, mpPose.POSE_CONNECTIONS
        )
        for mark_id, lm in enumerate(results.pose_landmarks.landmark):
            h, w, c = img.shape
            landmarks[mark_id] = lm
            cx, cy = int(lm.x * w), int(lm.y * h)
            cv2.circle(img, (cx, cy), 5, (255, 0, 0), cv2.FILLED)

    return landmarks

def get_angle(landmark, joint):
    a = np.array([landmark[joint[0]].x, landmark[joint[0]].y])  # First coordinate
    b = np.array([landmark[joint[1]].x, landmark[joint[1]].y])  # Second coordinate
    c = np.array([landmark[joint[2]].x, landmark[joint[2]].y])  # Third coordinate

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    angle = angle - 180 if angle > 180.0 else angle

    return int(angle)

def get_leng(landmark, joint):
    a = np.array([landmark[joint[0]].x, landmark[joint[0]].y])  # First coordinate
    b = np.array([landmark[joint[1]].x, landmark[joint[1]].y])  # Second coordinate


    return int(np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)*100) / 100

def launch_video(filename):
    cap = cv2.VideoCapture(filename)
    ret, frame = cap.read()
    angle_dict = {}
    start = time.time()
    for bodyPart in bodyPoints.keys():
        angle_dict[bodyPart] = {}

    for bodyLen in list(lengPoint.keys()):
        angle_dict[bodyLen] = {}

    while time.time() - start < 10:
        ret, frame = cap.read()
        if ret:
            # cv2.imshow('Frame', frame)
            # cv2.waitKey(0)

            landmarks = get_new_frame_from_neuron(frame)
            if landmarks:
                for bodyPart in bodyPoints.keys():
                    angel = get_angle(landmarks, bodyPoints[bodyPart])

                    if angel in angle_dict[bodyPart]:
                        angle_dict[bodyPart][angel] += 1
                    else:
                        angle_dict[bodyPart][angel] = 1

                for bodyLen in list(lengPoint.keys()):
                    leng = get_leng(landmarks, lengPoint[bodyLen])

                    if leng in angle_dict[bodyLen]:
                        angle_dict[bodyLen][leng] += 1
                    else:
                        angle_dict[bodyLen][leng] = 1
        else:
            break
    for bodyPart in list(bodyPoints.keys()):
        for ang in list(angle_dict[bodyPart].keys()):
            if angle_dict[bodyPart][ang] == 1:
                angle_dict[bodyPart].pop(ang)


    out_file = open(f'{filename[0:filename.find(".")]}_out.json', 'w+')
    json.dump(angle_dict, out_file,  sort_keys=True, indent=4)


if len(sys.argv) == 2:
    launch_video(str(sys.argv[1]))
else:
    print('Only one argment, video name')