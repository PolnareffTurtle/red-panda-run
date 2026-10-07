from random import randint

import pygame

from src.gamestate import GameState
from src.keys import DOWN_KEYS, ENTER_KEYS, UP_KEYS
from src.scenes.scene import Scene
from src.text import HINT, MARKER, MENU, SELECTED, TITLE, draw_text

MENU_ITEMS = [
    ('Continue', GameState.GAME_MENU),
    ('Level Select', GameState.LEVEL_SELECT),
    ('Options', GameState.OPTIONS),
]


class MainMenuScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.option_index = 0
        self.r1 = randint(-100, -50)
        self.r2 = randint(-100, 0)

        self.bg_rect = pygame.Surface((200, 20))
        self.bg_rect.set_alpha(150)
        self.bg_rect.fill((255, 255, 255))

        self.logo = game.assets['player_idle']

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in ENTER_KEYS:
                self.game.change_scene(MENU_ITEMS[self.option_index][1])
            if event.type == pygame.KEYUP:
                if event.key in UP_KEYS:
                    self.option_index = (self.option_index - 1) % len(MENU_ITEMS)
                elif event.key in DOWN_KEYS:
                    self.option_index = (self.option_index + 1) % len(MENU_ITEMS)

    def update(self):
        self.logo.update()

    def render(self, surf):
        surf.blit(self.game.assets['backgrounds'][0], (self.r1, 0))
        surf.blit(self.game.assets['backgrounds'][1], (self.r2, 0))
        surf.blit(self.bg_rect, (28, 49 + self.option_index * 20))

        draw_text(surf, 'Red Panda Run', (30, 20), TITLE)
        for n, (label, _) in enumerate(MENU_ITEMS):
            if n == self.option_index:
                draw_text(surf, label, (31, 49 + 20 * n), SELECTED)
            else:
                draw_text(surf, label, (30, 50 + 20 * n), MENU)
        draw_text(surf, '>', (10, 48 + 20 * self.option_index), MARKER)
        draw_text(surf, 'Use WASD or\nArrow Keys,\nPress [ENTER]\nto select', (80, 170), HINT)

        surf.blit(pygame.transform.scale(self.logo.img(flip=True), (132, 90)), (180, 150))
