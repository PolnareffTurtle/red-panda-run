from enum import Enum


# One value per scene. Game.change_scene takes one of these, and SCENES in main.py maps it
# to the scene class, so scenes can send the player to each other without importing each other.
class GameState(Enum):
    MAIN_MENU = 0
    LEVEL_SELECT = 1
    GAME_MENU = 2
    GAME_RUNNING = 3
    OPTIONS = 4


UNFINISHED_LEVELS = {13, 14, 15, 16, 17, 18, 19, 20}
