import asyncio
import json
import os
from sys import exit, platform

import pygame

from src.gamestate import GameState
from src.scenes.game_menu import GameMenuScene
from src.scenes.gameplay import GameplayScene
from src.scenes.level_select import LevelSelectScene
from src.scenes.main_menu import MainMenuScene
from src.scenes.option_menu import OptionsMenuScene
from src.utils import (
    Animation,
    Music,
    load_image,
    load_images,
    load_tileset,
)

SCENES = {
    GameState.MAIN_MENU: MainMenuScene,
    GameState.LEVEL_SELECT: LevelSelectScene,
    GameState.GAME_MENU: GameMenuScene,
    GameState.GAME_RUNNING: GameplayScene,
    GameState.OPTIONS: OptionsMenuScene,
}

# All game logic (physics, animations, transitions) is tuned as one tick per 1/60 s.
TICK_RATE = 60
# A hitch longer than this many ticks (level load, switching tabs) is dropped, not replayed.
MAX_TICKS_PER_FRAME = 4
# best ticks per level. Outside game/ so pygbag doesn't bundle it. The browser build has no disk
# that lasts, so there the scores only live until the page closes.
SCORES_FILE = None if platform == 'emscripten' else '../high_scores.json'


class Game:
    def __init__(self, scores_file=None):
        pygame.init()
        # SCALED lets SDL do the single upscale to the window/canvas. Rendering into a
        # 960x720 screen surface as well meant scaling the frame twice every frame.
        self.screen = pygame.display.set_mode((320, 240), flags=pygame.SCALED, vsync=1)
        pygame.display.set_caption('Red Panda Run')
        self.display = pygame.Surface((320, 240))
        self.clock = pygame.time.Clock()

        self.level = 1

        self.sound_index, self.res_index = 0, 0
        self.soundon = True
        self.resolution = self.screen.get_size()

        self.musics = Music(self)

        self.assets = {
            'all_tiles': load_tileset('assets/tileset/Assets2.png', 16),
            'backgrounds': load_images('background'),
            'player': load_image('player/idle/0.png'),
            'player_idle': Animation(load_images('player/idle'), img_dur=20),
            'player_jump': Animation(load_images('player/jump'), img_dur=5),
            'player_run': Animation(load_images('player/run'), img_dur=5),
            'player_wall_slide': Animation(load_images('player/wall_slide'), img_dur=5),
            'wind_anim': Animation(
                load_images('wind_anim', alpha=True, scale=2), img_dur=1, loop=False
            ),
        }

        # one fact per level, shown on the card before the level starts
        with open('assets/text/facts.json', encoding='utf-8') as f:
            self.facts = json.load(f)

        # None keeps scores in memory, so RL agents and tests can't overwrite the player's
        self.scores_file = scores_file
        self.best_ticks = {}
        if scores_file and os.path.exists(scores_file):
            with open(scores_file, encoding='utf-8') as f:
                self.best_ticks = {int(level): ticks for level, ticks in json.load(f).items()}

        self.last_frame_time = pygame.time.get_ticks()
        self.tick_backlog = 0

        self.scene = MainMenuScene(self)
        # the GameState to switch to at the end of this frame, or None to stay
        self.next_scene = None

    async def next_frame(self):
        # Show the frame, hand control back to the browser, and return how many logic ticks
        # to run before drawing the next one. Under pygbag the browser decides the frame rate
        # (requestAnimationFrame): Safari drops to 30fps in Low Power Mode or inside an
        # itch.io iframe, which ran the whole game at half speed when every frame was one tick.
        self.clock.tick(TICK_RATE)
        self.present()
        await asyncio.sleep(0)

        now = pygame.time.get_ticks()
        self.tick_backlog += (now - self.last_frame_time) * TICK_RATE / 1000
        self.last_frame_time = now
        ticks = int(self.tick_backlog)
        self.tick_backlog -= ticks
        if ticks > MAX_TICKS_PER_FRAME:
            ticks, self.tick_backlog = MAX_TICKS_PER_FRAME, 0
        return ticks

    def present(self):
        # blit before flipping, and only pay for a scale when the options menu has put
        # the screen at a size other than the 320x240 we render at
        if self.screen.get_size() == self.display.get_size():
            self.screen.blit(self.display, (0, 0))
        else:
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
        pygame.display.flip()

    def transition_in(self, i):
        pygame.draw.rect(
            self.display,
            (0, 0, 0),
            pygame.rect.Rect(i, 0, self.display.get_width(), self.display.get_height()),
        )

    async def transition_out(self):
        i = 0
        ticks = 1
        while i <= 360:
            i += 36 * ticks
            pygame.draw.rect(
                self.display, (0, 0, 0), pygame.rect.Rect(0, 0, i, self.display.get_height())
            )

            ticks = await self.next_frame()

    def record_win(self, level, ticks):
        if level in self.best_ticks and self.best_ticks[level] <= ticks:
            return
        self.best_ticks[level] = ticks
        if self.scores_file:
            with open(self.scores_file, 'w', encoding='utf-8') as f:
                json.dump(self.best_ticks, f, indent=2, sort_keys=True)

    def change_scene(self, state):
        # takes effect at the end of the frame, after the wipe out has played
        self.next_scene = state

    async def run(self):
        i = 0
        ticks = 1
        while True:
            events = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == self.NEXT:
                    self.musics.mnext()
                else:
                    events.append(event)

            self.scene.handle_events(events)
            for _ in range(ticks):
                if self.next_scene is not None:
                    break
                self.scene.update()
            self.scene.render(self.display)
            self.musics.update()

            if i <= 360:
                self.transition_in(i)
            i += 36 * ticks

            if self.next_scene is not None:
                await self.transition_out()
                self.scene = SCENES[self.next_scene](self)
                self.next_scene = None
                i = 0

            ticks = await self.next_frame()


if __name__ == '__main__':
    game = Game(SCORES_FILE)
    asyncio.run(game.run())
