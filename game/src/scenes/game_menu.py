import pygame

from src.gamestate import GameState
from src.keys import ENTER_KEYS
from src.scenes.scene import Scene
from src.text import ORANGE, WHITE_BIG, WHITE_SMALL, draw_text

# how wide a fact may get before it wraps onto the next line
FACT_WIDTH = 304


# the card with a red panda fact that shows before each level
class GameMenuScene(Scene):
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in ENTER_KEYS:
                    self.game.change_scene(GameState.GAME_RUNNING)
                if event.key == pygame.K_ESCAPE:
                    self.game.change_scene(GameState.LEVEL_SELECT)

    def render(self, surf):
        level, facts = self.game.level, self.game.facts
        surf.fill(ORANGE)
        if level < len(facts):
            draw_text(surf, facts[level], (8, 70), WHITE_BIG, width=FACT_WIDTH)
        draw_text(surf, 'Level ' + str(level + 1), (100, 30), WHITE_BIG)
        draw_text(surf, '[ESC]', (10, 10), WHITE_SMALL)
        draw_text(surf, 'Press [ENTER] to continue', (70, 200), WHITE_SMALL)
