import numpy as np

from GUI.EnumFiles import SqutsState


class ExrProcessing:

    def __init__(self, req_ang_start, req_ang_proc, req_ang_end, req_dist, key_angle_name, req_coord, name):
        self.key_angle_name = key_angle_name #['left_knee', -1]
        self.key_angle = []
        self.key_angle_new = 0
        self.key_angle_old = None
        self.req_ang_start = req_ang_start #{left_knee: [90,120], right_knee: [90,120]}
        self.req_ang_proc = req_ang_proc #{left_knee: [90,120], right_knee: [90,120]}
        self.req_ang_end = req_ang_end #{left_knee: [90,120], right_knee: [90,120]}
        self.req_dist = req_dist # distances to be maintained [[33,32],[45,44]]
        self.req_coord = req_coord # coordinates wich have to be fixed [33,23,45]
        self.stage1 = None
        self.stage2 = None
        self.right_start_position = False
        self.currentExcState = SqutsState.Sitting
        self.dist = []
        self.start = 0
        self.fixed_distances =[]
        self.fixed_coordinates = []
        self.condition = 0
        self.start_position_recorded = False
        self.name = name
        self.done_exercises = 0
        self.start_stage = {}
        self.mistakes = {'ANGLE':{},
                         'DISTANCE':[],
                         'COORDINATE':[],
                         'START':[]
                         }
        self.all_joints = {
                'left_armpit': [13, 11, 23],
                'right_ armpit': [14, 12, 24],
                'left_shoulder': [13, 11, 12],
                'right_ shoulder': [14, 12, 11],
                'left_elbow': [11, 13, 15],
                'right_elbow': [12, 14, 16],
                'left_wrist': [13, 15, 17],
                'right_wrist': [14, 16, 18],
                'left_brush': [13, 15, 21],
                'right_brush': [14, 16, 22],
                'left_carpus': [13, 15, 19],
                'right_carpus': [14, 16, 20],
                'left_pinky': [15, 17, 19],
                'right_pinky': [16, 18, 20],
                'left_hip': [11, 23, 25],
                'right_hip': [12, 24, 26],
                'left_frame': [11, 23, 24],
                'right_frame': [12, 24, 23],
                'left_knee': [23, 25, 27],
                'right_knee': [24, 26, 28],
                'left_bridge': [25, 27, 31],
                'right_bridge': [26, 28, 32],
                'left_ankle': [25, 27, 29],
                'right_ankle': [26, 28, 30],
                'left_heel': [27, 29, 31],
                'right_heel': [28, 30, 32],
                'left_foot_index': [27, 31, 29],
                'right_foot_index': [28, 32, 30],
                }

    def get_distans(self, landmark1 , landmark2, coord1, coord2):

        Error1_1 = landmark1[coord1].visibility
        Error2_2 = landmark2[coord2].visibility
        Error2_1 = landmark2[coord1].visibility
        Error1_2 = landmark1[coord2].visibility

        Error1 = Error1_2 * Error1_1
        Error2 = Error2_2 * Error2_1

        if max(Error1, Error2) < 0.2:
            #print(f'{coord2, coord1} in dead zone')
            error_occured = True
            # excFinished = False
            #####stop doing function
        if Error1 > Error2:
            landmark = landmark1
        else:
            landmark = landmark2

        x1, y1 = landmark[coord1].x, landmark[coord1].y
        x2, y2 = landmark[coord2].x, landmark[coord2].y
        dist = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

        return dist


    def get_angle(self, joint_list, landmark1, landmark2):
        '''
        :param landmark: Counted mediapipes points
        :param joint_list: List of neighbours points, of angle what we need to count
        Middle point - top of the counted angle. Example ([1,2,3], [2,3,4]). In this case we count angle in 2, and 3.
        :return: list of counted angles with errors. Output is [(angle, errorInThisPoint), (error2, errorInThisPoint2),..., ]
        '''
        aError1 = landmark1[joint_list[0]].visibility
        bError1 = landmark1[joint_list[1]].visibility
        cError1 = landmark1[joint_list[2]].visibility

        resError1 = aError1 * bError1 * cError1


        aError2 = landmark2[joint_list[0]].visibility
        bError2 = landmark2[joint_list[1]].visibility
        cError2 = landmark2[joint_list[2]].visibility

        resError2 = aError2 * bError2 * cError2

        if max(resError1, resError2) < 0.2:
            return None
            #error_occured = True
            # excFinished = False
            #####stop doing function
        if resError1 > resError2:
            landmark = landmark1
        else:
            landmark = landmark2

        a = np.array([landmark[joint_list[0]].x,
                      landmark[joint_list[0]].y])  # First coordinate
        b = np.array([landmark[joint_list[1]].x,
                      landmark[joint_list[1]].y])  # Second coordinate
        c = np.array([landmark[joint_list[2]].x,
                      landmark[joint_list[2]].y])  # Third coordinate

        aError = landmark[joint_list[0]].visibility
        bError = landmark[joint_list[1]].visibility
        cError = landmark[joint_list[2]].visibility

        resError = aError * bError * cError

        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(
            a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        angle = angle - 180 if angle > 180.0 else angle
        if angle < 20:
            angle = 180
        # angle = angle - 180 if angle > 180.0 else angle
        #print(angle)

        return angle

    def get_coordinates(self, landmark1, landmark2, point):
        coord = []
        Error1 = landmark1[point].visibility
        Error2 = landmark2[point].visibility

        if max(Error1, Error2) < 0.2:
            return None
            #error_occured = True
            # excFinished = False
            #####stop doing function
        if Error1 > Error2:
            landmark = landmark1
        else:
            landmark = landmark2

        coord.append(landmark[point].x)
        coord.append(landmark[point].y)
        # coord.append(landmark[point].z)

        return coord

    def startPosition(self, landmark1, landmark2):
        print('im in start')
        self.stage1 = landmark1
        self.stage2 = landmark2
        self.key_angle_old = self.get_angle(self.key_angle, landmark1,
                                            landmark2)
        if self.req_coord != []:
            for point in self.req_coord:
                if self.get_coordinates(landmark1, landmark2, point) is None:
                    print('Vas ne vidno v coordinatax')
                    return None
                self.fixed_coordinates.append(self.get_coordinates(landmark1, landmark2, point))

                    #vis = 0
        if self.req_dist != []:
            for points in self.req_dist:

                if self.get_distans(landmark1,landmark2, points[0], points[1]) is None:
                    print('Vas ne vidno v rasstoyaniyax')
                    return None
                self.fixed_distances.append(self.get_distans(landmark1,landmark2, points[0], points[1]))

        self.start_position_recorded = True
        return True


    def analyzeProc(self, landmark1, landmark2):
        print('im in proc')




        self.key_angle_new = self.get_angle(self.key_angle, landmark1, landmark2)
        #print(1, self.key_angle_name[1], self.key_angle_old, self.key_angle_new)
        if self.key_angle_new is None:
            print('Vas ne vidno v uglax v proc')

        elif self.key_angle_name[1] * (self.key_angle_old - self.key_angle_new) < 0:
            #print(2, self.key_angle_name[1],self.key_angle_old, self.key_angle_new)
            self.key_angle_old = self.key_angle_new
            self.currentExcState = SqutsState.Sitting
            self.stage1 = landmark1
            self.stage2 = landmark2


        elif self.key_angle_name[1] * (self.key_angle_old - self.key_angle_new) > 20:
            #print(3, self.key_angle_name[1], self.key_angle_old,
            #      self.key_angle_new)
            self.condition = 1
            self.done_exercises += 1
            #print('hand stop')
            stateVariable = False
            error_occured = False

            succ = False
            for key, value in self.req_ang_proc.items():
                angle = self.get_angle(self.all_joints[key], landmark1, landmark2)
                if angle is not None:
                    if value[1] < angle or value[0] > angle:
                        self.mistakes['ANGLE'][key] = [angle, value]
                        #print('proebalis v proc')
                        print(f'Error in {key}. Current - {angle} Waiting angle was in {value[0]} - {value[1]}')

                        #print('mistake in procccccccccccccccc')
                        #error_occured = True

    def analyzeEnd(self, landmark1, landmark2):
        print('im in end')
        #print(1, self.key_angle_name[1], self.key_angle_old, self.key_angle_new)
        self.key_angle_new = self.get_angle(self.key_angle, landmark1, landmark2)
        if self.key_angle_new is None:
            print('Vas ne vidno v uglax v end')
        #self.done_exercises += 1
        elif self.key_angle_name[1] * (
                self.key_angle_old - self.key_angle_new) > 0:
            self.currentExcState = SqutsState.Standing
            #print(2, self.key_angle_name[1], self.key_angle_old,
            #      self.key_angle_new)
            #print('hand up')
            self.key_angle_old = self.key_angle_new
            self.stage1 = landmark1
            self.stage2 = landmark2
            #print('Vidno')

        elif self.key_angle_name[1] * (
                self.key_angle_new - self.key_angle_old) > 20:
            #print(3, self.key_angle_name[1], self.key_angle_old, self.key_angle_new)
            #print('hand stop')

            stateVariable = False
            error_occured = False

            succ = False
            for key, value in self.req_ang_end.items():
                angle = self.get_angle(self.all_joints[key], landmark1,
                                       landmark2)
                if angle is None:
                    print('Vas ne vidno v uglax v end')
                elif value[1] < angle or value[0] > angle:
                    # self.mistakes['ANGLE'][key] = [angle, value]
                    print('proebalis v end')
                    print(
                        f'Error in {key}. Current - {angle} Waiting angle was in {value[0]} - {value[1]}')
                    #print('mistake in enddddddddddddddddddddd')

                    error_occured = True
            self.condition = 0



    def analyzeDist(self, landmark1, landmark2):

        delta = 0.1
        distances = []
        i = 0
        for points in self.req_dist:

            if self.get_distans(landmark1, landmark2, points[0],points[1]) is None:
                print('Vas ne vidno v dist v dist')
                vis = 0
            #print(self.fixed_distances, distances[i])
            else:
                distances.append(
                self.get_distans(landmark1, landmark2, points[0],
                                 points[1]))

                if abs(distances[i] - self.fixed_distances[i]) > delta:
                    self.mistakes['DISTANCE'].append('back')
                #print(
                #    f'Error in distance {i}.')
                i += 1


            #self.isExcCorrect.setText('Heels have eyes')
            succ = False

    def analyzeCoordinates(self, landmark1, landmark2):
        coordinates = []
        delta = 0.001
        for pos, point in enumerate(self.req_coord):
            coord = self.get_coordinates(landmark1, landmark2, point)
            if coord is None:
                print('Vas ne vidno v coord v coord')

            else:
                coordinates.append(coord)
                if (coordinates[pos][0] - self.fixed_coordinates[pos][0])**2 + (coordinates[pos][1] - self.fixed_coordinates[pos][1])**2 > delta:
                    self.mistakes['COORDINATE'].append('HEELS')
                    print('heeels')
                    #print('heeeeeeeeeels',coordinates[i], self.fixed_coordinates[i])

                self.fixed_coordinates[pos][0] = self.fixed_coordinates[pos][0] \
                                                 + 0.01 * (coordinates[pos][0] - self.fixed_coordinates[pos][0])
                self.fixed_coordinates[pos][1] = self.fixed_coordinates[pos][1] \
                                                 + 0.01 * (coordinates[pos][1] - self.fixed_coordinates[pos][1])





    def analyzeStart(self, landmark1, landmark2):
        print('im in analyze start')

        for key, value in self.req_ang_start.items():
            self.right_start_position = False
            angle = self.get_angle(self.all_joints[key], landmark1,landmark2)
            if angle is not None:
                self.right_start_position = True
                if angle < value[0] or angle > value[1]:
                    print(angle, value)
                    self.mistakes['START'].append('wrong on start')
                    self.right_start_position = False
                elif self.startPosition(landmark1, landmark2) is None:
                    self.right_start_position = False
                elif self.right_start_position:
                    print('You can start')
                    #self.right_start_position = True
            else:
                print('Vas ne vidno v starte v uglax')


    def startAnalyze(self, landmark1, landmark2):
        self.key_angle = self.all_joints[self.key_angle_name[0]]

        #self.startPosition(landmark1, landmark2)
        #gde-to nado vivodit na ekran 1..2..3..start

    def continueAnalyze(self, landmark1, landmark2):

        if self.right_start_position == False:
            self.analyzeStart(landmark1, landmark2)
        elif self.condition == 0:
            self.analyzeProc(landmark1, landmark2)
            self.analyzeDist(landmark1, landmark2)  # smotrit na spinu i pyatki
            self.analyzeCoordinates(landmark1, landmark2)
        else:
            self.analyzeEnd(landmark1, landmark2)
            self.analyzeDist(landmark1, landmark2)  # smotrit na spinu i pyatki
            self.analyzeCoordinates(landmark1, landmark2)


