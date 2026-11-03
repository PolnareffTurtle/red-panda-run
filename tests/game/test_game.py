"""Runs the real game headless: scenes, levels, the async frame loop and its timing."""

import asyncio
import json
from pathlib import Path

import pygame
import pytest

from main import MAX_TICKS_PER_FRAME, SCENES, Game
from src.gamestate import UNFINISHED_LEVELS, GameState
from src.scenes import level_select
from src.scenes.game_menu import GameMenuScene
from src.scenes.gameplay import GameplayScene
from src.scenes.level_select import LevelSelectScene
from src.scenes.main_menu import MainMenuScene
from src.text import BROWN, GREY, HINT, ORANGE, draw_text, surfaces, text_surface
from src.tilemap import Tile

LEVELS = range(1, 21)
PLAYABLE = [level for level in LEVELS if level not in UNFINISHED_LEVELS]
LAST_LEVEL = PLAYABLE[-1]
# the next level is locked, so these return to the main menu
END_OF_RUN = [level for level in PLAYABLE if level + 1 in UNFINISHED_LEVELS]


def key(event_type, code):
    return pygame.event.Event(event_type, key=code)


def press(scene, code):
    scene.handle_events([key(pygame.KEYDOWN, code), key(pygame.KEYUP, code)])


def gameplay(game, level=1):
    game.level = level
    return GameplayScene(game)


def test_every_game_state_has_a_scene():
    assert set(SCENES) == set(GameState)


@pytest.mark.parametrize("state", GameState, ids=lambda state: state.name)
def test_scene_runs(game, state):
    scene = SCENES[state](game)
    press(scene, pygame.K_DOWN)
    press(scene, pygame.K_UP)
    for _ in range(5):
        scene.update()
        scene.render(game.display)


@pytest.mark.parametrize("level", PLAYABLE)
def test_level_plays(game, level):
    scene = gameplay(game, level)
    scene.handle_events([key(pygame.KEYDOWN, pygame.K_RIGHT)])
    for tick in range(300):
        if tick % 20 == 0:
            scene.player.jump()
        scene.update()
        if tick % 10 == 0:
            scene.render(game.display)
        if scene.result:
            break


@pytest.mark.parametrize("level", PLAYABLE)
def test_rendering_does_not_advance_a_level(game, level):
    # Render runs once per frame and update once per tick, so anything advanced in render
    # slows down in Safari at 30fps
    scene = gameplay(game, level)
    for _ in range(10):
        scene.update()

    def state():
        return (
            list(scene.player.pos),
            list(scene.player.velocity),
            scene.player.animation.frame,
            list(scene.scroll),
            list(scene.tilemaps.group_alpha),
            [
                (particle.animation.frame, particle.pos)
                for wind in scene.tilemaps.wind_zones
                for particle in wind.particles
            ],
        )

    before = state()
    for _ in range(5):
        scene.render(game.display)
    assert state() == before


@pytest.mark.parametrize("scene_class", [MainMenuScene, LevelSelectScene])
def test_rendering_does_not_advance_menus(game, scene_class):
    scene = scene_class(game)
    before = scene.logo.frame
    for _ in range(5):
        scene.render(game.display)
    assert scene.logo.frame == before


def test_frame_loop_runs_and_changes_scene(game, monkeypatch):
    frames = 0
    tracks = []
    next_frame = game.next_frame

    async def counted_next_frame():
        # the script of the run: each frame of the real loop ends up in here
        nonlocal frames
        frames += 1
        if frames == 3:
            pygame.event.post(pygame.event.Event(game.NEXT))
        if frames == 5:
            game.change_scene(GameState.LEVEL_SELECT)
        if frames == 40:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        assert frames < 100, "the loop ignored QUIT"
        return await next_frame()

    monkeypatch.setattr(game, "next_frame", counted_next_frame)
    monkeypatch.setattr(game.musics, "mnext", lambda: tracks.append(1))
    # QUIT would shut pygame down for every test after this one
    monkeypatch.setattr(pygame, "quit", lambda: None)
    pygame.event.clear()

    with pytest.raises(SystemExit):
        asyncio.run(game.run())

    assert isinstance(game.scene, LevelSelectScene)
    assert game.next_scene is None
    assert tracks == [1]


class FakeClock:
    def tick(self, fps):
        pass


def ticks_per_frame(game, monkeypatch, frame_times):
    # plays frames lasting the given numbers of milliseconds, returns the ticks for each
    now = 0
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: now)
    monkeypatch.setattr(game, "clock", FakeClock())
    game.last_frame_time = 0
    game.tick_backlog = 0
    ticks = []
    for frame_time in frame_times:
        now += frame_time
        ticks.append(asyncio.run(game.next_frame()))
    return ticks


@pytest.mark.parametrize("fps", [60, 30, 20])
def test_game_speed_does_not_depend_on_frame_rate(game, monkeypatch, fps):
    ticks = ticks_per_frame(game, monkeypatch, [1000 / fps] * fps)
    assert sum(ticks) == pytest.approx(60, abs=1)


def test_long_hitch_is_dropped(game, monkeypatch):
    assert ticks_per_frame(game, monkeypatch, [5000]) == [MAX_TICKS_PER_FRAME]
    assert game.tick_backlog == 0


@pytest.mark.parametrize("level", [level for level in PLAYABLE if level not in END_OF_RUN])
def test_winning_moves_to_the_next_level(game, level):
    scene = gameplay(game, level)
    scene.win()
    scene.finish()
    assert game.level == level + 1
    assert game.next_scene is GameState.GAME_MENU


@pytest.mark.parametrize("level", END_OF_RUN)
def test_winning_before_a_locked_level_goes_to_the_main_menu(game, level):
    scene = gameplay(game, level)
    scene.win()
    scene.finish()
    assert game.level == level
    assert game.next_scene is GameState.MAIN_MENU


def test_losing_reloads_the_level(game):
    scene = gameplay(game, 3)
    scene.lose()
    scene.finish()
    assert game.level == 3
    assert game.next_scene is GameState.GAME_RUNNING


def test_level_select_picks_the_level_on_screen(game):
    scene = LevelSelectScene(game)
    scene.option_index = LAST_LEVEL - 1
    press(scene, pygame.K_RETURN)
    assert game.level == LAST_LEVEL
    assert game.next_scene is GameState.GAME_MENU


@pytest.mark.parametrize("level", sorted(UNFINISHED_LEVELS))
def test_level_select_ignores_unfinished_levels(game, level):
    scene = LevelSelectScene(game)
    scene.option_index = level - 1
    press(scene, pygame.K_RETURN)
    assert game.next_scene is None


def drawn_text(monkeypatch, game, scene):
    texts = []
    monkeypatch.setattr(level_select, "draw_text", lambda surf, text, *args: texts.append(text))
    scene.render(game.display)
    return texts


def test_level_select_marks_locked_slots(game, monkeypatch):
    locked = min(UNFINISHED_LEVELS)
    scene = LevelSelectScene(game)
    scene.option_index = locked - 1
    texts = drawn_text(monkeypatch, game, scene)
    assert "Coming soon" in texts
    assert "Press [ENTER]" not in texts
    assert not {str(level) for level in UNFINISHED_LEVELS} & set(texts)


def test_level_select_shows_the_hint_on_playable_slots(game, monkeypatch):
    scene = LevelSelectScene(game)
    texts = drawn_text(monkeypatch, game, scene)
    assert "Press [ENTER]" in texts
    assert "Coming soon" not in texts


def test_selected_padlock_is_raised_and_faded(game):
    locked = min(UNFINISHED_LEVELS)
    scene = LevelSelectScene(game)
    scene.option_index = locked - 1
    scene.render(game.display)
    column, row = (locked - 1) % 5, (locked - 1) // 5
    x, y = 50 + column * 50, 60 + row * 30
    # orange and brown, but blended with the background behind them
    lock = game.display.get_at((x + 10, y + 12))[:3]
    shadow = game.display.get_at((x + 2, y + 12))[:3]
    assert lock != ORANGE
    assert lock[0] > lock[2]
    assert shadow != BROWN
    assert sum(shadow) < sum(lock)

    scene.option_index = 0
    scene.render(game.display)
    assert game.display.get_at((x + 10, y + 12))[:3] == GREY


@pytest.mark.parametrize(
    ("code", "start", "end"),
    [
        (pygame.K_RIGHT, 0, 1),
        (pygame.K_KP6, 0, 1),  # how Safari reports the arrows
        (pygame.K_DOWN, 0, 5),
        (pygame.K_KP2, 0, 5),
        (pygame.K_LEFT, 0, 0),  # doesn't wrap at the edges
        (pygame.K_UP, 0, 0),
        (pygame.K_RIGHT, 19, 19),
        (pygame.K_DOWN, 19, 19),
    ],
)
def test_level_select_marker(game, code, start, end):
    scene = LevelSelectScene(game)
    scene.option_index = start
    press(scene, code)
    assert scene.option_index == end


@pytest.mark.parametrize("level", [1, 6, 7, LAST_LEVEL])
def test_fact_card_draws_with_or_without_a_fact(game, level):
    game.level = level
    GameMenuScene(game).render(game.display)


@pytest.fixture
def scene(game):
    # level 1 with an empty main layer, so each test places only the tiles it's about
    scene = gameplay(game, 1)
    scene.tilemaps.tilemaps[scene.tilemaps.main_layer].clear()
    scene.tilemaps.wind_zones.clear()
    scene.player.pos = [160, 160]
    return scene


def place(scene, x, y, tile_type):
    tilemap = scene.tilemaps.tilemaps[scene.tilemaps.main_layer]
    tilemap[(x, y)] = Tile(0, (x, y), tile_type)


def step(scene):
    scene.player.update(scene.tilemaps, (0, 0))


def test_falling_out_of_the_level_loses(scene):
    scene.player.pos = [160, 16 * scene.tilemaps.height + 1]
    step(scene)
    assert scene.result == "lose"


def test_spikes_lose(scene):
    place(scene, 10, 10, "lose")
    step(scene)
    assert scene.result == "lose"


def test_bamboo_wins(scene):
    place(scene, 10, 10, "win")
    step(scene)
    assert scene.result == "win"


def test_mushroom_bounces(scene):
    place(scene, 10, 10, "jump")
    step(scene)
    assert scene.player.velocity[1] < -7


def test_player_lands_and_jumps_once(scene):
    for x in range(9, 13):
        place(scene, x, 11, "physics")
    for _ in range(60):
        step(scene)
        if scene.player.collisions["down"]:
            break
    assert scene.player.collisions["down"]
    assert scene.player.rect().bottom == 11 * 16

    scene.player.jump()
    assert scene.player.velocity[1] == -6
    step(scene)
    velocity = scene.player.velocity[1]
    scene.player.jump()
    assert scene.player.velocity[1] == velocity


def test_every_track_loads(game):
    for path in game.musics.mlist:
        pygame.mixer.music.load(path)
    assert {Path(path).suffix for path in game.musics.mlist} == {".ogg"}


def test_music_wraps_to_the_first_track(game):
    music = game.musics
    music.index = len(music.mlist) - 1
    music.mnext()
    assert music.index == 0


def test_music_only_touches_the_mixer_when_the_setting_changes(game, monkeypatch):
    # pausing goes through the browser audio path, so it can't happen every frame
    pauses = []
    monkeypatch.setattr(pygame.mixer.music, "pause", lambda: pauses.append("pause"))
    monkeypatch.setattr(pygame.mixer.music, "unpause", lambda: pauses.append("unpause"))
    game.soundon = False
    game.musics.update()
    game.musics.update()
    game.soundon = True
    game.musics.update()
    game.musics.update()
    assert pauses == ["pause", "unpause"]


def test_text_is_cached_unless_told_not_to(game):
    surfaces.clear()
    assert text_surface("hi", 8, (0, 0, 0)) is text_surface("hi", 8, (0, 0, 0))
    draw_text(game.display, "12.34", (0, 0), HINT, cache=False)
    assert len(surfaces) == 1


def test_text_wraps_to_width(game):
    one_line = text_surface("a few words here", 8, (0, 0, 0))
    wrapped = text_surface("a few words here", 8, (0, 0, 0), width=50)
    assert wrapped.get_width() <= 50
    assert wrapped.get_height() > one_line.get_height()


@pytest.fixture
def scores(game, monkeypatch, tmp_path):
    path = tmp_path / "high_scores.json"
    monkeypatch.setattr(game, "scores_file", path)
    monkeypatch.setattr(game, "best_ticks", {})
    return path


def test_winning_saves_the_ticks_it_took(game, scores):
    scene = gameplay(game, 2)
    for _ in range(7):
        scene.update()
    scene.win()
    scene.finish()
    assert json.loads(scores.read_text()) == {"2": 7}


def test_only_a_faster_win_replaces_the_best(game, scores):
    game.record_win(1, 300)
    game.record_win(1, 400)
    assert game.best_ticks == {1: 300}
    game.record_win(1, 288)
    assert game.best_ticks == {1: 288}


def test_losing_saves_nothing(game, scores):
    scene = gameplay(game)
    scene.lose()
    scene.finish()
    assert game.best_ticks == {}
    assert not scores.exists()


def test_scores_load_back_with_number_keys(game, scores):
    game.record_win(2, 288)
    assert Game(scores).best_ticks == {2: 288}


def test_no_scores_file_only_keeps_them_in_memory(game, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(game, "scores_file", None)
    monkeypatch.setattr(game, "best_ticks", {})
    game.record_win(1, 100)
    assert game.best_ticks == {1: 100}
    assert list(tmp_path.iterdir()) == []
