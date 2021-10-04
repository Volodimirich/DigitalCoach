from enum import Enum


class SqutsState(Enum):
    Sitting = 1
    Standing = 2

class ExcersiceState(Enum):
    Waiting = 0
    Preparing = 1
    Working = 2

class ExcersiceStyle(Enum):
    Trainer = 0
    Myself = 1

class ExcersiceType(Enum):
    Squats = 0
    AnotherOne = 1
    AnotherTwo = 2
    Hand = 3
    AnotherThree = 4
    LastOne = 5

