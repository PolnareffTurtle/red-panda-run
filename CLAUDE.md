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

**One loop, one scene at a time.** `game/main.py` holds the `Game` class: the window, the shared assets and settings (`level`, `soundon`, `sound_index`, `res_index`, `facts`), and the only frame loop, `Game.run()`. Each screen is a `Scene` subclass in `src/scenes/` (`MainMenuScene`, `LevelSelectScene`, `OptionsMenuScene`, `GameMenuScene` for the pre-level fact card, `GameplayScene`). Every frame the loop calls `scene.handle_events(events)`, then `scene.update()` once per tick, then `scene.render(self.display)`.

A scene leaves by calling `self.game.change_scene(GameState.X)`. The loop finishes the frame, plays the wipe out, builds a new scene from the `SCENES` dict in `main.py`, and draws the wipe in. Scenes are rebuilt on every change, so anything that must outlive a scene lives on `Game`. Scenes refer to each other only through the `GameState` enum (`src/gamestate.py`), which keeps them from importing each other. `GameplayScene` owns the `Player` and `Tilemaps`, and both hold a reference to the scene: the player ends a level by calling `scene.win()` / `scene.lose()`, and a loss simply changes to `GAME_RUNNING` again, which reloads the level.

**pygbag constraints shape the code:**
- `Game.run()` and `transition_out` are the only frame loops, and each must end an iteration with `ticks = await self.next_frame()`. That call presents the frame and yields to the browser (`await asyncio.sleep(0)`); without that yield the browser build freezes. Scene methods are plain functions and must never loop waiting for something.
- The browser sets the frame rate, not `clock.tick`: Safari runs at 30fps in Low Power Mode or inside itch.io's iframe. Game logic is tuned for 60 ticks/s, so `next_frame()` returns how many ticks to run, based on real elapsed time. Anything that advances over time goes in a scene's `update()`, which the loop calls once per tick (possibly 0 or several times in a frame): physics, `Animation.update`, scroll smoothing. Drawing goes in `render()`, which runs once per frame. If you advance something in `render()` instead, the game slows down again in Safari.
- Every input check uses the `UP_KEYS`/`DOWN_KEYS`/`LEFT_KEYS`/`RIGHT_KEYS` sets from `src/keys.py` (arrows + WASD + keypad 8/2/4/6). Don't compare against `pygame.K_UP` etc. directly. In Safari, arrow keys reach the page correctly but likely show up in pygame as keypad keys (`K_KP8`...), because Safari marks them as keypad keys and SDL's web backend remaps them. That's why the keypad keys are in the sets.
- Music must be `.ogg` (`assets/music/`). `Music` plays every file in that folder and uses a `USEREVENT` (`game.NEXT`) to move to the next track, which `Game.run()` handles (along with `QUIT`) before passing the remaining events to the scene.
- Don't call mixer or display operations every frame without need. See the comments in `Music.update` and `Game.present`.

**Rendering.** Everything is drawn to a 320x240 `self.display` surface, and `present()` blits it to the `SCALED` window, scaling only if the options menu changed the window size. Text is drawn with `draw_text(surf, text, pos, style)` from `src/text.py`, called straight from the frame loop. It keeps every rendered string in a dict keyed by text, size, color and wrap width, so nothing is re-rendered unless the string changes; pass `cache=False` for text that changes nearly every frame (the level timer). Colors and the `Style(size, color, shadow)` presets (`TITLE`, `MENU`, `SELECTED`, `HINT`, ...) live there too, and `width=` word-wraps to a pixel width.

**Levels are Tiled exports** (`assets/levels/<n>.json`, loaded by `src/tilemap.py`):
- The tileset `assets/redpandarun.json` maps tile id → `type` (`physics`, `win`, `lose`, `jump`). Tile images are cut from the 16px tileset sheet `assets/tileset/Assets2.png` by `load_tileset`, row by row, so a tile's position in the sheet gives its Tiled tile id (GID − 1).
- The map's custom properties are read **by position**: `[0]` `main_layer`, `[1]` `player_x`, `[2]` `player_y` (in tiles). Wind objects read `[0]` `x_push`, `[1]` `y_push`. Tiled sorts properties alphabetically, so keep these names.
- The top 3 bits of a GID encode rotation. They are decoded in `open_json`, and rotated surfaces are cached in `tile_image`.
- Only `main_layer` is used for collision (`physics_rects_around` checks a 4x3 neighborhood). Tile layers up to and including `main_layer` draw behind the player (`render1`). Text/wind objects and later layers draw in front (`render2`).
- Object layers are told apart by their Tiled `class`: `text` (in-world text, stored as `(text, pos, Style)` rows and drawn with `draw_text`) or `wind` (`WindZone` in `src/wind.py`, which pushes the player and spawns particles; exactly one of `x_push`/`y_push` must be non-zero).

**Level progression** is hard-coded. The level select shows 20 slots, but only levels whose index isn't in `UNFINISHED_LEVELS` (`src/gamestate.py`) can be picked. `GameMenuScene` shows `assets/text/facts.json[level]` (one plain sentence per level, wrapped to `FACT_WIDTH`; a level past the end of the list shows no fact), and `GameplayScene.finish()` returns to the main menu after level index 5. Update these together when adding levels.

**Assets.** `load_image` converts non-alpha images with black `(0,0,0)` as the colorkey. `load_images` loads a whole directory in sorted order (skipping `.DS_Store`), so frame and tile order comes from the filenames.
