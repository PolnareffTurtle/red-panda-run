import pygame

from src.entities import Player
from src.gamestate import UNFINISHED_LEVELS, GameState
from src.keys import LEFT_KEYS, RIGHT_KEYS, UP_KEYS
from src.scenes.scene import Scene
from src.text import BLACK, HINT, ORANGE, WHITE_BIG, Style, draw_text
from src.tilemap import Tilemaps
from src.utils import Backgrounds


class GameplayScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.start_time = pygame.time.get_ticks()
        self.backgrounds = [
            Backgrounds(0.1, game.assets['backgrounds'][0], 0, (0, 0)),
            Backgrounds(0.2, game.assets['backgrounds'][1], 1, (0, 0)),
        ]

        # the tilemap moves the player to the level's start position, so the player comes first
        self.player = Player(self, (0, 0), (22, 10))
        self.tilemaps = Tilemaps(self, game.level, tile_size=16)

        self.movement = [False, False]
        self.scroll = [
            self.player.rect().centerx - game.display.get_width() / 2,
            self.player.rect().centery - game.display.get_height() / 2,
        ]
        self.render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

        # 'win' or 'lose' once the level is over. Set by the player through win() and lose()
        self.result = None

    def win(self):
        self.result = 'win'

    def lose(self):
        self.result = 'lose'

    def finish(self):
        game = self.game
        if self.result == 'lose':
            # a new GameplayScene reloads the level
            game.change_scene(GameState.GAME_RUNNING)
        elif game.level == 5 or game.level + 1 in UNFINISHED_LEVELS:
            game.change_scene(GameState.MAIN_MENU)
        else:
            game.level += 1
            game.change_scene(GameState.GAME_MENU)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in LEFT_KEYS:
                    self.movement[0] = True
                if event.key in RIGHT_KEYS:
                    self.movement[1] = True
                if event.key in UP_KEYS:
                    self.player.jump()
                if event.key == pygame.K_ESCAPE:
                    self.game.change_scene(GameState.MAIN_MENU)
            elif event.type == pygame.KEYUP:
                if event.key in LEFT_KEYS:
                    self.movement[0] = False
                if event.key in RIGHT_KEYS:
                    self.movement[1] = False

    def update(self):
        display = self.game.display
        self.scroll[0] += (
            self.player.rect().centerx - display.get_width() / 2 - self.scroll[0]
        ) / 10
        self.scroll[1] += (
            self.player.rect().centery - display.get_height() / 2 - self.scroll[1]
        ) / 10
        if self.scroll[1] > 16 * (self.tilemaps.height - 10):
            self.scroll[1] = 16 * (self.tilemaps.height - 10)

        self.tilemaps.update()
        self.player.update(self.tilemaps, (self.movement[1] - self.movement[0], 0))
        if self.result:
            self.finish()

    def render(self, surf):
        self.render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

        for background in self.backgrounds:
            background.update(self.render_scroll)
            background.render(surf)

        self.tilemaps.render1(surf, offset=self.render_scroll)
        self.player.render(surf, offset=self.render_scroll)
        self.tilemaps.render2(surf, offset=self.render_scroll)

        draw_text(surf, '[ESC]', (10, 10), HINT)
        # the timer shows a new value nearly every frame, so it is not worth caching
        seconds = ((pygame.time.get_ticks() - self.start_time) // 10) / 100
        draw_text(surf, str(seconds), (270, 10), HINT, cache=False)
        draw_text(surf, str(int(self.game.clock.get_fps())), (30, 30), WHITE_BIG)

        if self.result:
            # the face over the player's head while the level wipes out
            face, color = (':)', BLACK) if self.result == 'win' else ('😟', ORANGE)
            pos = (self.player.pos[0], self.player.pos[1] - 20)
            draw_text(surf, face, pos, Style(24, color), offset=self.render_scroll)
