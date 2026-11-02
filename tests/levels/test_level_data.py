"""Checks every Tiled export against what src/tilemap.py assumes about it."""

import json
import re
import struct
from pathlib import Path

import pytest

from src.gamestate import UNFINISHED_LEVELS

GAME_DIR = Path(__file__).resolve().parents[2] / "game"
LEVELS = GAME_DIR / "assets" / "levels"
TILESET = json.loads((GAME_DIR / "assets" / "redpandarun.json").read_text())
TILE_TYPES = {tile["id"]: tile["type"] for tile in TILESET["tiles"]}

LEVEL_SLOTS = 20  # the size of the level select grid
PLAYER_SIZE = (22, 10)  # GameplayScene
TILE_SIZE = 16
GID_MASK = 2**29 - 1  # the bits above this hold a tile's rotation

PATHS = sorted(LEVELS.glob("*.json"))
FINISHED_PATHS = [path for n, path in enumerate(PATHS, 1) if n not in UNFINISHED_LEVELS]


def load(path):
    return json.loads(path.read_text())


@pytest.fixture(params=PATHS, ids=lambda path: path.stem)
def level(request):
    return load(request.param)


def tile_layers(level):
    return [layer for layer in level["layers"] if layer["type"] == "tilelayer"]


def main_layer(level):
    return tile_layers(level)[level["properties"][0]["value"]]


def tile_at(level, x, y):
    if not 0 <= x < level["width"] or not 0 <= y < level["height"]:
        return 0
    return main_layer(level)["data"][y * level["width"] + x] & GID_MASK


def test_file_names_are_numbered_from_one_with_no_gaps():
    names = [path.name for path in PATHS]
    assert all(re.fullmatch(r"level_\d\d\.json", name) for name in names)
    assert names == [f"level_{n:02}.json" for n in range(1, len(names) + 1)]


def test_every_level_slot_is_a_level_or_unfinished():
    # an unfinished level may already have a file, it just can't be picked yet
    levels = set(range(1, len(PATHS) + 1))
    assert levels | UNFINISHED_LEVELS == set(range(1, LEVEL_SLOTS + 1))


def test_tileset_matches_its_sheet():
    # a PNG's width and height are always at these offsets in the IHDR chunk
    sheet = (GAME_DIR / "assets" / "tileset" / "Assets2.png").read_bytes()
    width, height = struct.unpack(">II", sheet[16:24])
    assert (width // TILE_SIZE) * (height // TILE_SIZE) == TILESET["tilecount"]


def test_tileset_types_are_known():
    # physics_rects_around has a list for each of these and crashes on anything else
    assert set(TILE_TYPES.values()) <= {"physics", "win", "lose", "jump"}
    assert max(TILE_TYPES) < TILESET["tilecount"]


def test_properties_are_in_the_order_tilemap_reads_them(level):
    names = [prop["name"] for prop in level["properties"]][:3]
    assert names == ["main_layer", "player_x", "player_y"]


def test_main_layer_is_a_tile_layer(level):
    assert 0 <= level["properties"][0]["value"] < len(tile_layers(level))


def test_uses_the_shared_tileset(level):
    # tile ids are worked out as GID - 1, which only holds for one tileset starting at 1
    assert level["tilesets"] == [{"firstgid": 1, "source": "../redpandarun.json"}]


def test_tile_ids_are_in_the_tileset(level):
    for layer in tile_layers(level):
        assert len(layer["data"]) == level["width"] * level["height"]
        assert max(gid & GID_MASK for gid in layer["data"]) <= TILESET["tilecount"]


def test_object_layers_have_a_known_class(level):
    for layer in level["layers"]:
        if layer["type"] != "tilelayer":
            assert layer.get("class") in ("text", "wind"), layer["name"]


def test_wind_pushes_exactly_one_way(level):
    for layer in level["layers"]:
        if layer.get("class") != "wind":
            continue
        for wind in layer["objects"]:
            properties = wind["properties"]
            assert [prop["name"] for prop in properties] == ["x_push", "y_push"]
            x_push, y_push = (prop["value"] for prop in properties)
            assert (x_push == 0) != (y_push == 0)


@pytest.mark.parametrize("path", FINISHED_PATHS, ids=lambda path: path.stem)
def test_unlocked_level_can_be_won(path):
    level = load(path)
    tiles = [gid & GID_MASK for gid in main_layer(level)["data"]]
    assert any(TILE_TYPES.get(tile - 1) == "win" for tile in tiles)


def test_player_starts_in_the_level_and_not_inside_a_wall(level):
    _, player_x, player_y = (prop["value"] for prop in level["properties"][:3])
    assert 0 <= player_x < level["width"]
    assert 0 <= player_y < level["height"]
    left, top = player_x * TILE_SIZE, player_y * TILE_SIZE
    for x in range(left // TILE_SIZE, (left + PLAYER_SIZE[0] - 1) // TILE_SIZE + 1):
        for y in range(top // TILE_SIZE, (top + PLAYER_SIZE[1] - 1) // TILE_SIZE + 1):
            assert TILE_TYPES.get(tile_at(level, x, y) - 1) != "physics", (x, y)
