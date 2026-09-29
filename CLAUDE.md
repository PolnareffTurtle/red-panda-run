# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Red Panda Run is a small pygame-ce 2D platformer that also ships to the browser with pygbag. All game code and assets live under `game/`. The repo root only holds `.venv/`, `.gitignore`, and `ruff.toml`.

## Commands

```bash
# Run locally. Asset paths are relative ('assets/...'), so the working directory must be game/
source .venv/bin/activate          # Python 3.14, pygame-ce 2.5.7
cd game && python main.py

# Build/serve for the web (pygbag is installed per-user, not in .venv). Run from the repo root.
pygbag game                        # serves on localhost:8000, output goes to game/build/web
pygbag --build game                # build only
```

Lint/format with ruff (installed in `.venv`, config in `ruff.toml`), from the repo root: `ruff check` and `ruff format`.

There are no tests or requirements file. `game/src/test.py` is a throwaway pygame scratch script, not a test suite.

## Architecture

**State machine in one class.** `game/main.py` holds a single `Game` class. `Game.run()` loops forever and dispatches on `self.gamestate` (the `GameState` enum in `src/gamestate.py`) to one async method per screen: `main_menu`, `level_select`, `options_menu`, `game_menu` (the pre-level fact card), and `game_running`. Each method runs its own `while self.gamestate == ...` loop, so a screen changes just by assigning `self.gamestate`. Entities do this too: `Player.update` sets `LOSE`/`WIN` straight on the game, and `game_running` then calls `lose()`/`win()`.

**pygbag constraints shape the code:**
- Every frame loop must end with `ticks = await self.next_frame()`, including `transition_out`. That call presents the frame and yields to the browser (`await asyncio.sleep(0)`); without that yield the browser build freezes.
- The browser sets the frame rate, not `clock.tick`: Safari runs at 30fps in Low Power Mode or inside itch.io's iframe. Game logic is tuned for 60 ticks/s, so `next_frame()` returns how many ticks to run, based on real elapsed time. Anything that advances per tick goes inside `for _ in range(ticks)` or gets multiplied by `ticks`: physics, `Animation.update`, scroll smoothing, the `i += 36` transition counters. Drawing stays outside that loop. If you advance something once per frame instead, the game slows down again in Safari.
- Every input check uses the `UP_KEYS`/`DOWN_KEYS`/`LEFT_KEYS`/`RIGHT_KEYS` sets (arrows + WASD + keypad 8/2/4/6). Don't compare against `pygame.K_UP` etc. directly. In Safari, arrow keys reach the page correctly but likely show up in pygame as keypad keys (`K_KP8`...), because Safari marks them as keypad keys and SDL's web backend remaps them. That's why the keypad keys are in the sets.
- Music must be `.ogg` (`assets/music/`). `Music` plays every file in that folder and uses a `USEREVENT` (`game.NEXT`) to move to the next track, so every screen's event loop has to handle `self.NEXT`.
- Don't call mixer or display operations every frame without need. See the comments in `Music.update` and `Game.present`.

**Rendering.** Everything is drawn to a 320x240 `self.display` surface, and `present()` blits it to the `SCALED` window, scaling only if the options menu changed the window size. `Text` objects pre-render at construction and share fonts per size via `get_font`, so build them once outside the loop when possible.

**Levels are Tiled exports** (`assets/levels/<n>.json`, loaded by `src/tilemap.py`):
- The tileset `assets/redpandarun.json` maps tile id → `type` (`physics`, `win`, `lose`, `jump`). Tile images are cut from the 16px tileset sheet `assets/tileset/Assets2.png` by `load_tileset`, row by row, so a tile's position in the sheet gives its Tiled tile id (GID − 1).
- The map's custom properties are read **by position**: `[0]` `main_layer`, `[1]` `player_x`, `[2]` `player_y` (in tiles). Wind objects read `[0]` `x_push`, `[1]` `y_push`. Tiled sorts properties alphabetically, so keep these names.
- The top 3 bits of a GID encode rotation. They are decoded in `open_json`, and rotated surfaces are cached in `tile_image`.
- Only `main_layer` is used for collision (`physics_rects_around` checks a 4x3 neighborhood). Tile layers up to and including `main_layer` draw behind the player (`render1`). Text/wind objects and later layers draw in front (`render2`).
- Object layers are told apart by their Tiled `class`: `text` (in-world `Text`) or `wind` (`WindZone` in `src/wind.py`, which pushes the player and spawns particles; exactly one of `x_push`/`y_push` must be non-zero).

**Level progression** is hard-coded in `main.py`. The level select shows 20 slots, but only levels whose index isn't in `UNFINISHED_LEVELS` can be picked. `game_menu` indexes a `facts` list by level, and `win()` returns to the main menu after level index 5. Update these together when adding levels.

**Assets.** `load_image` converts non-alpha images with black `(0,0,0)` as the colorkey. `load_images` loads a whole directory in sorted order (skipping `.DS_Store`), so frame and tile order comes from the filenames.

**`src/scenes/` is an unfinished refactor** toward per-scene classes (`Scene` base with `handle_events`/`update`/`render`). Nothing imports it, it uses a broken import (`from scene import Scene`), and `option_menu.py` is truncated. The live logic is the methods in `main.py`.
