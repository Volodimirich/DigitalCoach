from PyQt5.QtGui import QMovie

from GUI.EnumFiles import SqutsState


class DefineErrors:
    def __init__(self):
        self.error_dict = {'error1' : 'вы присели недостаточно низко',
                            'error2' : 'вы присели слишком низко',
                            'error3' : 'держите колени уже, на ширине плеч',
                            'error4' : 'держите колени шире, на ширине плеч'}
        self.errors = {
            'SQUATS': {
                'YOU_SQATED_TOO_LOW': 'you crouched too low',
                'YOU_SQATED_TOO_HIGHT': 'you didnt crouch low \nenough',
                'YOU_KNEES_TOO_NARROW':'keep your knees wider,\nshoulder-width apart',
                'YOU_KNEES_TOO_WIDE':'keep your knees narrower,\nshoulder width apart',
                'CURVE_BACK':'keep your back straight',
                'HEELS_IS_FLYING':'do not lift your heels off\nthe ground',
                'WRONG_ON_START': 'please, go back'

            }
        }
        self.errors_video = {
            'SQUATS': {
                'YOU_SQATED_TOO_LOW': QMovie("pictures/ExcersiceGif/low.gif"),
                'YOU_SQATED_TOO_HIGHT': QMovie("pictures/ExcersiceGif/high.gif"),
                'YOU_KNEES_TOO_NARROW': QMovie("pictures/ExcersiceGif/stay.gif"),
                'YOU_KNEES_TOO_WIDE': QMovie("pictures/ExcersiceGif/stay.gif"),
                'CURVE_BACK': QMovie("pictures/ExcersiceGif/back.gif"),
                'HEELS_IS_FLYING': QMovie("pictures/ExcersiceGif/pyatki.gif"),
                'WRONG_ON_START': QMovie("pictures/ExcersiceGif/goback.gif")
            }
        }
        self.mistake = ''
        self.answer = []

    def define_angle_mistake(self, exercise_name, mistakes, state):
        # mistake = {'right_knee':[90,[45,60]]}
        if mistakes:
            print(mistakes, state)
        if exercise_name == 'SQUATS':
            for key, value in mistakes.items():
                value[0] = 180 - value[0] if value[0] < 20 else value[0]
                if value[0] > value[1][1]:
                    # if key == 'left_knee' and state == SqutsState.Standing:
                    if key == 'left_knee':
                        self.mistake = 'YOU_SQATED_TOO_HIGHT'
                        # self.mistake.append('YOU_SQATED_TOO_HIGHT')
                        print(value[0], value[1][0], 'debug', 'im in to hight')

                    elif key in {'left_hip', 'right_hip'}:
                        # self.mistake.append('YOU_KNEES_TOO_NARROW')
                        self.mistake = 'YOU_KNEES_TOO_NARROW'
                if value[0] < value[1][0]:
                    # if key == 'left_knee' and state == SqutsState.Sitting:
                    if key == 'left_knee':
                        # self.mistake.append('YOU_SQATED_TOO_LOW')
                        self.mistake = 'YOU_SQATED_TOO_LOW'
                        print(value[0], value[1][0], 'debug', 'im in too low')
                    elif key in {'left_hip', 'right_hip'}:
                        self.mistake = 'YOU_KNEES_TOO_WIDE'
                        # self.mistake.append('YOU_KNEES_TOO_WIDE')

    def define_distance_mistake(self, exercise_name, mistakes):
        # mistake = ['back','heels']
        if exercise_name == 'SQUATS':
            for mistake in mistakes:
                if mistake == 'back':
                    self.mistake = 'CURVE_BACK'
                    # self.mistake.append('CURVE_BACK')


    def define_coordinate_mistake(self, exercise_name, mistakes):
        # mistake = ['heels']
        if exercise_name == 'SQUATS':
            for mistake in mistakes:
                if mistake == 'HEELS':
                    self.mistake = 'HEELS_IS_FLYING'
                    # self.mistake.append('HEELS_IS_FLYING')


    def define_other_mistake(self,exercise_name, mistakes):
        # misatake = ['wrong on start']
        if exercise_name == 'SQUATS':
            for mistake in mistakes:
                if mistake == 'WRONG_ON_START':
                    self.mistake = 'WRONG_ON_START'


    def get_error(self, state, exercise_name='SQUATS'):
        return (self.errors[exercise_name][self.mistake], self.errors_video[exercise_name][self.mistake]) if self.mistake else ('everything is ok', None)

    def reset_mistake(self):
        self.mistake = None
