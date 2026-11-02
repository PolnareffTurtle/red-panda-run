"""Reinforcement learning suite. Run from repo root"""

import os
import sys
from pathlib import Path

import gymnasium as gym
import numpy as np
import pygame
from gymnasium.utils.env_checker import check_env

GAME_DIR = Path(__file__).resolve().parent.parent / "game"
os.chdir(GAME_DIR)
sys.path.append(str(Path.cwd()))
# no sound even when watching; the video driver is picked per env in __init__
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from main import Game  # noqa: E402
from src.scenes.gameplay import GameplayScene  # noqa: E402

# 1 tick = 1/60 seconds. 30 s is several times what level 1 takes; a longer limit only
# adds standing-still steps that teach nothing
MAX_TICKS = 1800
# game ticks each action is repeated for. Exploring with a fresh random action every tick just
# jitters in place, and fewer steps per level means rewards are discounted less on the way back
FRAME_SKIP = 4

# tile codes in the level grid; also the index of each tile's one-hot channel
EMPTY, SOLID, SPIKE, MUSHROOM, BAMBOO = range(5)
N_TILE_TYPES = 5
TILE_CODES = {None: EMPTY, "physics": SOLID, "lose": SPIKE, "jump": MUSHROOM, "win": BAMBOO}

# how many tiles around the player the agent sees (odd, so the player is in the middle)
VIEW_W, VIEW_H = 11, 9
# padding around the level grid, at least a full view so any slice stays inside the array
PAD = max(VIEW_W, VIEW_H)

# player state appended after the view window, see _player_state
N_STATE = 13
# rough maximum magnitudes, used to scale the state into [-1, 1]
MAX_SPEED_X = 3.5  # a wall jump's push
MAX_SPEED_Y = 10  # terminal fall speed; a mushroom bounce is -8
MAX_WIND = 5  # strongest wind push in any level is 4.5


class RedPandaRunEnv(gym.Env):
    # "human" opens the game window and draws every step at the game's real speed
    metadata = {"render_modes": ["human"], "render_fps": 60}

    def __init__(self, level=0, render_mode=None):
        assert render_mode is None or render_mode in self.metadata["render_modes"], render_mode
        self.render_mode = render_mode
        # SDL reads the driver when Game() calls pygame.init(), so this is early enough.
        # Without a window there's nothing to draw to, and training runs far faster.
        if render_mode != "human":
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        self.game = Game()
        self.level = level
        self.action_space = gym.spaces.Discrete(6)
        # 0 = nothing
        # 1 = left
        # 2 = right
        # 3 = jump
        # 4 = jump + left
        # 5 = jump + right
        self.observation_space = gym.spaces.Box(
            -1, 1, shape=(VIEW_H * VIEW_W * N_TILE_TYPES + N_STATE,), dtype=np.float32
        )
        # padded tile grid per level, built on first use since it never changes
        self.grids = {}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.game.level = self.level
        self.game.scene = GameplayScene(self.game)
        self.ticks = 0
        # whether the previous step held jump; like the up key, jump only fires on a new press
        self.jump_held = False
        if self.level not in self.grids:
            self.grids[self.level] = self._build_grid()
        self.grid = self.grids[self.level]
        # gymnasium's convention: in human mode the env draws itself, so callers never call render
        if self.render_mode == "human":
            self.render()
        return self._get_obs(), {}

    def _build_grid(self):
        # the main layer as a 2D array of tile codes, indexed [y, x] like any numpy image
        tilemaps = self.game.scene.tilemaps
        tiles = tilemaps.tilemaps[tilemaps.main_layer]
        # Tilemaps doesn't store the level width. Ending the grid at the rightmost tile is
        # fine: everything past it is empty, which is what the padding says anyway.
        width = max(x for x, _ in tiles) + 1
        grid = np.full((tilemaps.height, width), EMPTY, dtype=np.int64)
        for (x, y), tile in tiles.items():
            if 0 <= y < tilemaps.height:
                grid[y, x] = TILE_CODES[tile.type]
        # empty above and to the sides; below the bottom the player dies, so call it spikes
        grid = np.pad(grid, ((PAD, 0), (PAD, PAD)), constant_values=EMPTY)
        return np.pad(grid, ((0, PAD), (0, 0)), constant_values=SPIKE)

    def _get_obs(self):
        center = self.game.scene.player.rect().center
        # player's tile in padded-grid coordinates, clamped so the slice stays in the array.
        # Past the padding everything is the same constant tile, so clamping changes nothing.
        x = int(np.clip(center[0] // 16 + PAD, VIEW_W // 2, self.grid.shape[1] - VIEW_W // 2 - 1))
        y = int(np.clip(center[1] // 16 + PAD, VIEW_H // 2, self.grid.shape[0] - VIEW_H // 2 - 1))
        window = self.grid[
            y - VIEW_H // 2 : y + VIEW_H // 2 + 1, x - VIEW_W // 2 : x + VIEW_W // 2 + 1
        ]
        # one channel per tile type, so the network doesn't read "spike = 2" as "2x solid"
        view = np.eye(N_TILE_TYPES, dtype=np.float32)[window].flatten()
        return np.concatenate([view, self._player_state()])

    def _player_state(self):
        player = self.game.scene.player
        center = player.rect().center
        # collisions only exists once the player has updated, so not yet right after reset
        collisions = getattr(player, "collisions", {})
        wind_x = wind_y = 0
        for wind in self.game.scene.tilemaps.wind_zones:
            if player.rect().colliderect(wind.rect):
                wind_x += wind.x_push
                wind_y += wind.y_push
        state = np.array(
            [
                player.velocity[0] / MAX_SPEED_X,
                player.velocity[1] / MAX_SPEED_Y,
                # where in its tile the player is, which the view window can't show
                center[0] % 16 / 16,
                center[1] % 16 / 16,
                collisions.get("down", False),
                # touching a wall, which wall_slide alone doesn't say for the first 4 ticks
                collisions.get("left", False) or collisions.get("right", False),
                player.wall_slide,
                player.jumps,
                # a wall jump only fires if flip and last_movement point into the wall
                1 if player.flip else -1,
                player.last_movement[0],
                # still holding jump from the last step, so choosing jump now does nothing
                self.jump_held,
                wind_x / MAX_WIND,
                wind_y / MAX_WIND,
            ],
            dtype=np.float32,
        )
        return np.clip(state, -1, 1)

    def step(self, action):
        movement = [False, False]
        if action % 3 == 1:
            movement[0] = True
        if action % 3 == 2:
            movement[1] = True
        jump = action >= 3
        if jump and not self.jump_held:
            self.game.scene.player.jump()
        self.jump_held = jump
        self.game.scene.movement = movement
        for _ in range(FRAME_SKIP):
            self.game.scene.update()
            self.ticks += 1
            # draw every tick, not every step, so watching runs at the game's real speed
            if self.render_mode == "human":
                self.render()
            if self.game.scene.result:
                break
        reward = 0
        if self.game.scene.result:
            reward = 1 if self.game.scene.result == "win" else -1
        return (
            self._get_obs(),
            reward,
            self.game.scene.result is not None,
            self.ticks >= MAX_TICKS,
            {"is_success": self.game.scene.result == "win"},
        )

    def render(self):
        # the same three steps as one frame of Game.run(): draw the scene, show it, wait
        self.game.scene.render(self.game.display)
        self.game.present()
        self.game.clock.tick(self.metadata["render_fps"])
        # the window needs its events read, or macOS shows the spinning cursor
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                sys.exit()

    def close(self):
        pygame.quit()


if __name__ == "__main__":
    env = RedPandaRunEnv()
    check_env(env)
