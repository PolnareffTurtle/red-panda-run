from enum import Enum


class GameState(Enum):
    MAIN_MENU = 0
    LEVEL_SELECT = 1
    GAME_MENU = 2
    GAME_RUNNING = 3
    OPTIONS = 4
    TRANSITION_OUT = 5
    TRANSITION_IN = 6
    LOSE = 7
    WIN = 8
