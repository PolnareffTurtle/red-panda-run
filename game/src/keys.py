import pygame

# Safari on macOS reports arrow keys as being on the numeric keypad, and SDL's web backend
# turns keypad arrows into keypad 8/2/4/6, so under pygbag in Safari the arrows arrive as
# K_KP8 etc. instead of K_UP. Accept those alongside the arrows and WASD.
UP_KEYS = {pygame.K_UP, pygame.K_w, pygame.K_KP8}
DOWN_KEYS = {pygame.K_DOWN, pygame.K_s, pygame.K_KP2}
LEFT_KEYS = {pygame.K_LEFT, pygame.K_a, pygame.K_KP4}
RIGHT_KEYS = {pygame.K_RIGHT, pygame.K_d, pygame.K_KP6}
ENTER_KEYS = {pygame.K_RETURN, pygame.K_KP_ENTER}
