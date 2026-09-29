from scene import Scene
from src.utils import Text
import pygame
from src.gamestate import GameState

class OptionMenu(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.y=0
        self.texts = {
            Text('Options', 16, (255,255,255), (120, 20)),
            Text('Sound:', 16, (255, 255, 255), (30, 50)),
            Text('Resolution:', 16, (255, 255, 255), (30, 70)),
            Text('[ESC]', 8, (255,255,255), (10, 10)),
            Text('Use arrow keys', 8, (255,255,255), (140, 170)),
            Text('to change', 8, (255,255,255), (140, 180)),
        }
        self.options={
            'sound': {
                'images': [
                    Text('On', 16, (255, 255, 255), (220, 50)),
                    Text('Off', 16, (255, 255, 255), (220, 50)),
                ],
                'vals': [
                    True,
                    False
                ]

            },
            'resolution': {
                'images': [
                    Text('320x240', 8, (255, 255, 255), (220, 76)),
                    Text('640x480', 8, (255, 255, 255), (220, 76)),
                    Text('960x720', 8, (255, 255, 255), (220, 76)),
                    Text('1280x960', 8, (255, 255, 255), (220, 76)),
                ],
                'vals': [
                    (320,240),
                    (640,480),
                    (960,720),
                    (1280,960)
                ]
            }
        }
    
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game.gamestate = GameState.MAIN_MENU
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_UP:
                    self.y = (self.y - 1)%2
                    x=0
                elif event.key == pygame.K_DOWN:
                    self.y = (self.y + 1)%2
                    x=0
                elif event.key == pygame.K_LEFT:
                    if self.y == 0:
                        self.game.sound_index = (self.game.sound_index - 1)%2
                        self.game.soundon = self.options['sound']['vals'][self.game.sound_index]

                    elif self.y == 1:
                        self.game.res_index = (self.game.res_index - 1)%4
                        self.game.screen = pygame.display.set_mode((self.options['resolution']['vals'][self.game.res_index]))

                elif event.key == pygame.K_RIGHT:
                    if self.y == 0:
                        self.game.sound_index = (self.game.sound_index + 1) % 2
                        self.game.soundon = self.options['sound']['vals'][self.game.sound_index]

                    elif self.y == 1:
                        self.game.res_index = (self.game.res_index + 1) % 4
                        self.game.screen = pygame.display.set_mode((self.options['resolution']['vals'][self.game.res_index]))

    def 
