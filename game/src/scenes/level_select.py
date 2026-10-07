from random import randint

import pygame

from src.gamestate import UNFINISHED_LEVELS, GameState
from src.keys import DOWN_KEYS, ENTER_KEYS, LEFT_KEYS, RIGHT_KEYS, UP_KEYS
from src.scenes.scene import Scene
from src.text import HINT, MARKER, MENU, SELECTED, TITLE, draw_text


class LevelSelectScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.option_index = 0
        self.r1 = randint(-100, -50)
        self.r2 = randint(-100, 0)

        self.bg_rect = pygame.Surface((265, 130))
        self.bg_rect.set_alpha(150)
        self.bg_rect.fill((255, 255, 255))

        self.logo = game.assets['player_idle']

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in ENTER_KEYS and self.option_index not in UNFINISHED_LEVELS:
                    self.game.level = self.option_index
                    self.game.change_scene(GameState.GAME_MENU)
                if event.key == pygame.K_ESCAPE:
                    self.game.change_scene(GameState.MAIN_MENU)

            if event.type == pygame.KEYUP:
                # the min/max stop the marker wrapping around the edges of the grid
                if event.key in UP_KEYS:
                    self.option_index = min((self.option_index - 5) % 20, self.option_index)
                elif event.key in DOWN_KEYS:
                    self.option_index = max((self.option_index + 5) % 20, self.option_index)
                elif event.key in LEFT_KEYS:
                    self.option_index = min((self.option_index - 1) % 20, self.option_index)
                elif event.key in RIGHT_KEYS:
                    self.option_index = max((self.option_index + 1) % 20, self.option_index)

    def update(self):
        self.logo.update()

    def render(self, surf):
        surf.blit(self.game.assets['backgrounds'][0], (self.r1, 0))
        surf.blit(self.game.assets['backgrounds'][1], (self.r2, 0))
        surf.blit(self.bg_rect, (30, 50))

        draw_text(surf, 'Levels', (120, 20), TITLE)
        draw_text(surf, 'Press [ENTER]', (140, 200), HINT)
        draw_text(surf, 'to select', (140, 210), HINT)
        draw_text(surf, '[ESC]', (10, 10), HINT)
        for n in range(20):
            x, y = 50 + (n % 5) * 50, 60 + (n // 5) * 30
            if n == self.option_index:
                draw_text(surf, str(n + 1), (x + 1, y - 1), SELECTED)
            else:
                draw_text(surf, str(n + 1), (x, y), MENU)

        surf.blit(pygame.transform.scale(self.logo.img(), (132, 90)), (10, 150))

        column, row = self.option_index % 5, self.option_index // 5
        draw_text(surf, '>', (37 + 50 * column, 58 + 30 * row), MARKER)
