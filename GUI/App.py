import logging
import sys
from functools import partial

import cv2
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import QImage, QPixmap, QFont, QMovie, QIcon
from PyQt5.QtWidgets import *
from enum import Enum

from GUI.DefineErrors import DefineErrors
from GUI.EnumFiles import ExcersiceState, SqutsState, ExcersiceType
from GUI.ExcersicePrc import ExrProcessing
from GUI.TrainerWait import TrainerWait
from GUI.TrainerWaitWindow import TimeWindow
from GUI.VideoWorker import VideoThreadWork
from Bot.TeleBotError import Mail
from GUI.WaitFunc import TrainerWaitThreadWork


class App(QWidget):
    def __init__(self, cam_list, ex_type=ExcersiceType.Squats):

        super().__init__()
        self.listCam = cam_list
        self.messageBot = Mail()
        self.landmarks = None
        self.val = 0
        if ex_type == ExcersiceType.Squats:
            self.exercise = ExrProcessing(req_ang_start={'left_knee': [170, 180]}, req_ang_proc={'left_knee': [70, 100]}, req_ang_end={'left_knee': [170, 180]}, req_dist=[[12, 24],[11, 23]], req_coord=[29], key_angle_name=['left_knee', -1], name='SQUATS')
        elif ex_type == ExcersiceType.Hand:
            self.exercise = ExrProcessing(req_ang_start={'right_elbow': [80, 100]},
                                         req_ang_proc={'right_elbow': [10, 50]},
                                         req_ang_end={'right_elbow': [80, 180]},
                                         req_dist=[],
                                         req_coord=[],
                                         key_angle_name=['right_elbow', -1],
                                         name='SQUATS')

        self.excCurrentState = ExcersiceState.Waiting
        self.camFirst = False
        self.camSec = False
        self.errors_manager = DefineErrors()
        self.state = SqutsState.Sitting
        self.legsPos = list()
        self.sharedMem = list()
        self.errorTimer = QTimer()
        self.allowChangeVideo = True
        self.amount = 0
        self.sqatsMem = list()
        self.initUI()



    @pyqtSlot(QImage, int)
    def setImage(self, image, num):
        if self.listCam[0] == num:
            self.labelFirst.setPixmap(QPixmap.fromImage(image))
        else:
            self.labelSecond.setPixmap(QPixmap.fromImage(image))

    @pyqtSlot(tuple, int, name='text')
    def setTextModern(self, data, num):
        # print(num)
        if len(self.listCam) == 2:
            if num == 0 and not self.camFirst:
                self.camFirst = True
                if not self.camSec:
                    return
            elif num != 0 and not self.camSec:
                self.camSec = True
                if not self.camFirst:
                    return

            if not self.sharedMem or self.sharedMem[0][1] == num:
                self.sharedMem.append((data, num))
            else:
                elements = (self.rightHandElbow, self.rightHandShoulder, self.leftHandElbow, self.leftHandShoulder)
                dataSaved, savedCam = self.sharedMem.pop()
                for pos, resFunc in enumerate(elements):
                    if data[pos][1] > dataSaved[pos][1]:
                        camResNum = num
                        dataRes = data[pos][0]
                    else:
                        camResNum = savedCam
                        dataRes = dataSaved[pos][1]
                    resFunc.setText(f'{dataRes:.2f}, cam - {camResNum}')
        else:
            dataSolo = []
            for elem in data:
                dataSolo.append(elem[0])
            self.setText(dataSolo)

    @pyqtSlot(dict, int, name='squats')
    def setTextSquats(self, data, num):
        if len(self.listCam) == 2:
            if num == 0 and not self.camFirst:
                self.camFirst = True
                if not self.camSec:
                    return
            elif num != 0 and not self.camSec:
                self.camSec = True
                if not self.camFirst:
                    return
            if not self.sqatsMem or self.sqatsMem[0][1] == num:
                self.sqatsMem.append((data, num))
            else:
                saved, numb = self.sqatsMem.pop()
                if self.allowChangeVideo:
                    self.errors_manager.reset_mistake()

                if self.val == 0:
                    print('start')
                    self.exercise.startAnalyze(data, data)
                    self.val = 1
                else:
                    self.exercise.continueAnalyze(data, data)
                    state = self.exercise.currentExcState
                    self.amount = self.exercise.done_exercises


                    for key, value in self.exercise.mistakes.items():

                        if key == 'ANGLE':
                            self.errors_manager.define_angle_mistake(self.exercise.name,
                                                                     self.exercise.mistakes[key], state)
                        if key == 'COORDINATE':
                            self.errors_manager.define_coordinate_mistake(self.exercise.name,
                                                                          self.exercise.mistakes[key])
                        # if key == 'DISTANCE':
                        #    errors_manager.define_distance_mistake(self.exercise.name, self.exercise.mistakes[key])
                        if key == 'START':
                            self.errors_manager.define_other_mistake(self.exercise.name, self.exercise.mistakes[key])

                    mistake, videoError = self.errors_manager.get_error(self.exercise.name)
                    self.exercise.mistakes = {'ANGLE': {},
                                              'DISTANCE': [],
                                              'COORDINATE': [],
                                              'START': []
                                              }
                    # self.completeNum.setText(str(self.amount))
                    self.NumberAmount.setText(f'<font color=\"red\">{str(self.amount)}</font>')


                    if videoError and self.allowChangeVideo:
                        pict = QPixmap('pictures/status/fail.jpg')
                        self.PictureStatus.setPixmap(pict.scaledToHeight(100))

                        self.allowChangeVideo = False
                        self.errorTimer.timeout.connect(self.changeError)
                        self.errorTimer.start(2500)

                        self.video.setMovie(videoError)
                        videoError.start()

                        self.ErrorMess.setText(mistake)
                    elif not videoError:
                        self.ErrorMess.setText('everything in ok')
                        pict = QPixmap('pictures/status/suc.jpg')
                        self.video.setMovie(QMovie())
                        # videoError.start()
                        self.PictureStatus.setPixmap(pict.scaledToHeight(100))



                    # Reaction for 1 camera data (see setModernText)
                return None
                    # self.isExcCorrect.setText('KRUTO!!!!')

            # Reaction for 1 camera data (see setModernText)
            return None

    @pyqtSlot(list)
    def setText(self, elementList):
        elements = (self.rightHandElbow, self.rightHandShoulder, self.leftHandElbow, self.leftHandShoulder)
        for pos, el in enumerate(elements):
            el.setText(f'{elementList[pos]:.2f}')

    @pyqtSlot(dict)
    def getDict(self, point_dict):
        self.landmarks = point_dict

    @pyqtSlot(str, str)
    def handExcersice(self, currentHand, isCorrect):
        # self.priorityHand.setText(currentHand)
        # self.isExcCorrect.setText(isCorrect)
        pass

    @pyqtSlot(int)
    def completeChange(self, amount):
        # print('!')
        pass

    def checkSquatSoloCam(self, saved):
        delta = 0.1  ###how to get it?
        angleFinishBorders = (60, 120)
        error_list = ('Right elbow', 'Right shoulder', 'Right hip', 'Right knee',
                      'Left elbow', 'Left shoulder', 'Left hip', 'Left knee')
        # angleErrorBorders = [(10, 70), (50, 70), (1, 100), (35, 100),
        #                      (10, 70), (50, 70), (1, 100), (35, 100)]
        angleErrorBorders = [(1, 180), (1, 180), (1, 180), (1, 180),
                             (1, 180), (1, 180), (1, 180), (5, 180)]
        lenErrorBorders = (0.2, 0.46)
        angles, legs, back = saved[0], saved[1], saved[2]
        stateVariable = False
        succ = False
        error_occured = False

        for pos, el in enumerate(angles):
            angle, vis = el
            # cam = camSaved if angle == angle1 else camResv
            if vis < 0.4:
                print(f'{error_list[pos]} in dead zone')
                error_occured = True
                self.state = SqutsState.Sitting

                # excFinished = False

            if self.state == SqutsState.Sitting:
                if angle < angleErrorBorders[pos][0] or angle > angleErrorBorders[pos][1]:
                    print(f'Error in {error_list[pos]}. Current - {angle} Waiting angle was in {angleErrorBorders[pos][0]} - {angleErrorBorders[pos][1]}')
                    error_occured = True
                if pos == 3:  ##HardCode ebaniu
                    if angle < angleFinishBorders[0]:
                        stateVariable = True
                elif pos == 7:
                    if stateVariable and angle < angleFinishBorders[0] and not error_occured :
                        self.state = SqutsState.Standing
                        print('ang - ', angle, 'border - ', angleFinishBorders[0])

            elif self.state == SqutsState.Standing:
                if angle < angleErrorBorders[pos][0] or angle > angleErrorBorders[pos][1]:
                    print(f'Error in {error_list[pos]}. Waiting angle was in {angleErrorBorders[pos][0]} - {angleErrorBorders[pos][1]}')
                    error_occured = True
                    self.state = SqutsState.Sitting


                if pos == 3:  ##HardCode ebaniu
                    if angle > angleFinishBorders[1]:
                        stateVariable = True
                elif pos == 7:
                    if stateVariable and angle > angleFinishBorders[1] and not error_occured:
                        self.state = SqutsState.Sitting
                        print('ang - ', angle, 'border - ', angleFinishBorders[0])
                        succ = True

        for pos, el in enumerate(legs):
            point, vis = el

            x, y = point
            xTar, yTar = self.legsPos[pos]
            if vis > 0.4:
                if np.sqrt((x - xTar) ** 2 + (y - yTar) ** 2) > 0.01:
                    self.isExcCorrect.setText("Problem in the heels\nDon't lift your hils of the floor")
                    # self.isExcCorrect.setText('Heels have eyes')
                    succ = False

            xNew = xTar + delta * (x - xTar)
            yNew = yTar + delta * (y - yTar)
            self.legsPos[pos] = [xNew, yNew]

        # for el in back:
        #     len, vis = el
            # if len < lenErrorBorders[0] or len > lenErrorBorders[1]:
            #     print(len, ' - LENG')
        return succ

    def create_text_instance(self, labelName: QLabel, labelComment: str):
        frame = QFrame(self)
        hbox = QHBoxLayout()

        comment = QLabel(self)
        comment.setText(labelComment)
        hbox.addWidget(comment)

        hbox.addWidget(labelName)

        frame.setLayout(hbox)
        return frame

    def changeError(self):
        self.allowChangeVideo = True
        self.errorTimer.disconnect()

    def startEx(self):
        self.buttonSt.setEnabled(False)
        self.messageBot.sendMessage('Trouble')
        self.buttonEn.setEnabled(True)
        self.timer = QTimer(self)
        self.timer.start(3000)
        self.timer.timeout.connect(self.GetCurrentUserPosition)

    def endEx(self):
        self.excCurrentState = ExcersiceState.Waiting
        self.buttonSt.setEnabled(True)
        self.buttonEn.setEnabled(False)

    def GetCurrentUserPosition(self):
        try:
            self.timer.disconnect()
            self.excCurrentState = ExcersiceState.Preparing
        except TypeError:
            pass

    def react(self):
        pass

    def create_button(self, text, react):

        but = QPushButton(text)
        but.clicked.connect(react)
        but.setFont(QFont('Arial', 18))
        but.setFixedSize(QSize(300, 100))
        # self.start.setStyleSheet("QPushButton{border-radius: 20; border: 2px solid black; background-color: Silver;  "
        #                          "selection-color: yellow; selection-background-color: blue;}")
        but.setStyleSheet(
            """
                QPushButton {
                    background-color: #7B9DBF;
                    color: white;
                    border: 2px solid black;
                    border-radius: 20;

                }
                QPushButton:pressed {
                    border-style: inset;
                    background-color: #c2c2c2;
                }
                QPushButton:disabled {
                    background-color:#ff0000;
                }
        """)

        return but

    def trainer_button(self):
            TrainerWait().send_message_to_trainer('0')
            th = TrainerWaitThreadWork()
            th.getAnswer.connect(self.TrainerWait)
            th.start()
            self.className = TimeWindow()

    def initUI(self):

        hbox = QHBoxLayout()

        frameUnity = QFrame(self)
        vboxVideoUnity = QVBoxLayout()

        frameVideo = QFrame(self)
        hboxVideo = QHBoxLayout()

        self.labelFirst = QLabel()
        hboxVideo.addWidget(self.labelFirst)

        if len(self.listCam) == 2:
            self.labelSecond = QLabel()
            hboxVideo.addWidget(self.labelSecond)

        frameVideo.setLayout(hboxVideo)
        vboxVideoUnity.addWidget(frameVideo)

        hboxButtons = QHBoxLayout()

        frameButtons = QFrame(self)



        self.pause = self.create_button('Pause', self.react)
        hboxButtons.addWidget(self.pause)

        self.call = self.create_button('Call trainer', self.react)
        self.call.clicked.connect(self.trainer_button)
        hboxButtons.addWidget(self.call)

        self.finish = self.create_button('Finish', self.react)
        hboxButtons.addWidget(self.finish)


        frameButtons.setLayout(hboxButtons)
        vboxVideoUnity.addWidget(frameButtons)

        hboxInform = QHBoxLayout()
        frameInform = QFrame()

        progName = QLabel("<font color=\"blue\">Digital</font> <font color=\"red\">trainer</font>")
        progName.setFont(QFont("Arial", 26, QFont.Bold))
        hboxInform.addWidget(progName)

        pict_widget = QPixmap('pictures/logo.png')
        pict_widget = pict_widget.scaledToHeight(80)
        lbl = QLabel(self)
        lbl.setPixmap(pict_widget)
        hboxInform.addWidget(lbl)

        frameInform.setLayout(hboxInform)
        vboxVideoUnity.addWidget(frameInform)

        frameUnity.setLayout(vboxVideoUnity)
        hbox.addWidget(frameUnity)

        frameFullInfrom = QFrame()
        vboxInform = QVBoxLayout()


        frameStatistic = QFrame()
        hboxText = QHBoxLayout()

        frameComplete = QFrame()
        vboxComplete = QVBoxLayout()


        CompText = QLabel("<font color=\"blue\">Completed: </font>")
        CompText.setFont(QFont("Arial", 26, QFont.Bold))
        vboxComplete.addWidget(CompText)
        vboxComplete.addStretch(1)


        self.NumberAmount = QLabel("<font color=\"red\">0</font>")
        self.NumberAmount.setFont(QFont("Arial", 40, QFont.Bold))
        self.NumberAmount.setAlignment(Qt.AlignCenter)
        vboxComplete.addWidget(self.NumberAmount)
        vboxComplete.addStretch(5)


        frameComplete.setLayout(vboxComplete)
        hboxText.addWidget(frameComplete)


        frameStatus = QFrame()
        vboxStatus = QVBoxLayout()


        StatText = QLabel("<font color=\"blue\">Status: </font>")
        StatText.setFont(QFont("Arial", 26, QFont.Bold))
        StatText.setAlignment(Qt.AlignCenter)
        vboxStatus.addWidget(StatText)
        vboxStatus.addStretch(1)

        self.PictureStatus = QLabel()
        pict = QPixmap('pictures/status/suc.jpg')
        self.PictureStatus.setPixmap(pict.scaledToHeight(100))
        self.PictureStatus.setAlignment(Qt.AlignCenter)
        vboxStatus.addWidget(self.PictureStatus)
        vboxStatus.addStretch(5)


        frameStatus.setLayout(vboxStatus)
        hboxText.addWidget(frameStatus)
        hboxText.addStretch(1)

        frameStatistic.setLayout(hboxText)
        vboxInform.addWidget(frameStatistic)

        StateMess = QLabel('State')
        StateMess.setFont(QFont("Arial", 26, QFont.Bold))
        vboxInform.addWidget(StateMess)

        self.ErrorMess = QLabel('Preparing')
        self.ErrorMess.setFont(QFont("Arial", 26, QFont.Bold))
        vboxInform.addWidget(self.ErrorMess)

        self.video = QLabel()
        self.video.setGeometry(QRect(25, 25, 200, 200))
        self.video.setMinimumSize(QSize(300, 300))
        self.video.setMaximumSize(QSize(300, 300))
        self.video.setObjectName("label")

        self.movie = QMovie("pictures/ExcersiceGif/wait.gif")
        # self.movie = QMovie()
        self.video.setMovie(self.movie)
        self.movie.start()

        vboxInform.addWidget(self.video, alignment=Qt.AlignCenter)
        frameFullInfrom.setLayout(vboxInform)

        hbox.addWidget(frameFullInfrom)

        self.setLayout(hbox)


        self.setGeometry(300, 100, 200, 200)

        th = VideoThreadWork(cam_num=self.listCam[0], parent=self)
        th.changePixmap.connect(self.setImage)
        # th.changeText.connect(self.setText)
        # th.changeTextModern.connect(self.setTextModern)
        # th.startExcercise.connect(self.handExcersice)
        th.startExcerciseSquats.connect(self.setTextSquats)
        # th.exCounter.connect(self.completeChange)
        th.start()

        if (len(self.listCam) == 2):
            th = VideoThreadWork(cam_num=self.listCam[1], parent=self)
            th.changePixmap.connect(self.setImage)
            # th.changeText.connect(self.setText)
            # th.startExcercise.connect(self.handExcersice)
            # th.changeTextModern.connect(self.setTextModern)
            th.startExcerciseSquats.connect(self.setTextSquats)
            #
            # th.exCounter.connect(self.completeChange)
            th.start()
        self.setStyleSheet("background-color: white;")
        self.show()

