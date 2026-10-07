import pygame

from src.gamestate import GameState
from src.keys import DOWN_KEYS, LEFT_KEYS, RIGHT_KEYS, UP_KEYS
from src.scenes.scene import Scene
from src.text import ORANGE, WHITE_BIG, WHITE_SMALL, draw_text

SOUND_OPTIONS = [('On', True), ('Off', False)]
RESOLUTIONS = [(320, 240), (640, 480), (960, 720), (1280, 960)]


class OptionsMenuScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.y = 0
        self.logo = game.assets['player_idle']

    def change_option(self, step):
        # the chosen values live on the game so they are still there when this scene is rebuilt
        game = self.game
        if self.y == 0:
            game.sound_index = (game.sound_index + step) % len(SOUND_OPTIONS)
            game.soundon = SOUND_OPTIONS[game.sound_index][1]
        elif self.y == 1:
            game.res_index = (game.res_index + step) % len(RESOLUTIONS)
            game.screen = pygame.display.set_mode(
                RESOLUTIONS[game.res_index], flags=pygame.SCALED, vsync=1
            )

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game.change_scene(GameState.MAIN_MENU)
            if event.type == pygame.KEYUP:
                if event.key in UP_KEYS:
                    self.y = (self.y - 1) % 2
                elif event.key in DOWN_KEYS:
                    self.y = (self.y + 1) % 2
                elif event.key in LEFT_KEYS:
                    self.change_option(-1)
                elif event.key in RIGHT_KEYS:
                    self.change_option(1)

    def update(self):
        self.logo.update()

    def render(self, surf):
        surf.fill(ORANGE)

        draw_text(surf, 'Options', (120, 20), WHITE_BIG)
        draw_text(surf, 'Sound:', (30, 50), WHITE_BIG)
        draw_text(surf, 'Resolution:', (30, 70), WHITE_BIG)
        draw_text(surf, '[ESC]', (10, 10), WHITE_SMALL)
        draw_text(surf, 'Use arrow keys', (140, 170), WHITE_SMALL)
        draw_text(surf, 'to change', (140, 180), WHITE_SMALL)

        draw_text(surf, SOUND_OPTIONS[self.game.sound_index][0], (220, 50), WHITE_BIG)
        width, height = RESOLUTIONS[self.game.res_index]
        draw_text(surf, f'{width}x{height}', (220, 76), WHITE_SMALL)

        draw_text(surf, '>', (10, 50 + self.y * 20), WHITE_BIG)

        surf.blit(pygame.transform.scale(self.logo.img(), (132, 90)), (10, 150))
