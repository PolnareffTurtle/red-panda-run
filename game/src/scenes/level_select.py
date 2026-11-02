from random import randint

import pygame

from src.gamestate import UNFINISHED_LEVELS, GameState
from src.keys import DOWN_KEYS, ENTER_KEYS, LEFT_KEYS, RIGHT_KEYS, UP_KEYS
from src.scenes.scene import Scene
from src.text import BROWN, GREY, HINT, MARKER, MENU, ORANGE, SELECTED, TITLE, draw_text

# how see-through the selected padlock is, so it still reads as locked
SELECTED_LOCK_ALPHA = 170


def draw_lock(surf, pos, color):
    x, y = pos
    pygame.draw.rect(surf, color, (x + 5, y + 1, 10, 8), width=2)
    pygame.draw.rect(surf, color, (x + 2, y + 7, 16, 10))


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

        # the same raised look as SELECTED text: orange over a brown shadow. Both are drawn on
        # one surface first, so the shadow doesn't show through the orange when it's faded
        self.selected_lock = pygame.Surface((20, 19), pygame.SRCALPHA)
        draw_lock(self.selected_lock, (0, 1), BROWN)
        draw_lock(self.selected_lock, (1, 0), ORANGE)
        self.selected_lock.set_alpha(SELECTED_LOCK_ALPHA)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                # option_index is a position in the grid, levels are numbered from 1
                if event.key in ENTER_KEYS and self.option_index + 1 not in UNFINISHED_LEVELS:
                    self.game.level = self.option_index + 1
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
        if self.option_index + 1 in UNFINISHED_LEVELS:
            draw_text(surf, 'Coming soon', (140, 205), HINT)
        else:
            draw_text(surf, 'Press [ENTER]', (140, 200), HINT)
            draw_text(surf, 'to select', (140, 210), HINT)
        draw_text(surf, '[ESC]', (10, 10), HINT)
        for n in range(20):
            x, y = 50 + (n % 5) * 50, 60 + (n // 5) * 30
            if n + 1 in UNFINISHED_LEVELS:
                if n == self.option_index:
                    surf.blit(self.selected_lock, (x, y - 1))
                else:
                    draw_lock(surf, (x, y), GREY)
            elif n == self.option_index:
                draw_text(surf, str(n + 1), (x + 1, y - 1), SELECTED)
            else:
                draw_text(surf, str(n + 1), (x, y), MENU)

        surf.blit(pygame.transform.scale(self.logo.img(), (132, 90)), (10, 150))

        column, row = self.option_index % 5, self.option_index // 5
        draw_text(surf, '>', (37 + 50 * column, 58 + 30 * row), MARKER)
