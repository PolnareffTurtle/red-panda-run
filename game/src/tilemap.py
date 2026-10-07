import json
import math

import pygame

from src.text import Style, draw_text
from src.wind import WindZone

with open('assets/redpandarun.json') as f:
    rawjson = f.read()
    jsondata = json.loads(rawjson)
tile_types = {}
for i in jsondata['tiles']:
    tile_types[i['id']] = i['type']

# Tile layers behind main_layer are scenery: multiply them by this colour so anything drawn
# at full brightness is something the player can touch.
BACKGROUND_TINT = (188, 190, 212)
# Small props keep their colour even on a background layer; nobody mistakes them for ground.
UNTINTED_TILES = {
    *(13, 14, 15, 16, 17, 38, 39, 40, 41, 42, 63, 64, 65),  # grass, bushes, palm
    *(59, 60, 185, 186, 187),  # water
    *(84, 85, 86, 87, 109, 111, 112, 134, 135, 136, 137),  # gate / swing
    *(105, 106, 107, 108),  # fence
    *(68, 93, 261, 262),  # small mushrooms, coconuts
}

# Tiles on layers in front of the player turn see-through while the player is behind them.
# Touching tiles fade together as one object (a whole bush, not single tiles).
FADE_MIN_ALPHA = 80
FADE_SPEED = 0.15  # share of the remaining alpha difference covered per tick
FADE_MARGIN = 6  # pixels around the player that count as "behind"
FADE_STEP = 16  # alpha is rounded to this so only a few faded copies of a tile are cached

NEIGHBOR_OFFSETS = [
    (-1, -1),
    (0, -1),
    (1, -1),
    (2, -1),
    (-1, 0),
    (0, 0),
    (1, 0),
    (2, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
    (2, 1),
]


class Tile:
    def __init__(self, tile_index, pos, type=None, rotation=0, image=None):
        self.index = tile_index
        self.pos = pos
        self.type = type
        self.rotation = rotation
        self.image = image


class Tilemaps:
    def __init__(self, scene, level, tile_size=16):

        self.scene = scene
        self.tile_size = tile_size
        self.tilemaps = []
        self.wind_zones = []
        self.texts = []
        self.rotated_tiles = {}
        self.faded_tiles = {}
        self.open_json(level)

    def tile_image(self, index, rotation, background=False):
        # rotate (and tint) once at load time; render1/render2 would otherwise allocate a
        # new surface for every visible tile on every frame
        key = (index, rotation, background)
        if key not in self.rotated_tiles:
            image = pygame.transform.rotate(self.scene.game.assets['all_tiles'][index], rotation)
            if background:
                # BLEND_RGB_MULT leaves alpha alone, so transparent pixels stay transparent
                image.fill(BACKGROUND_TINT, special_flags=pygame.BLEND_RGB_MULT)
            self.rotated_tiles[key] = image
        return self.rotated_tiles[key]

    def faded_image(self, tile, alpha):
        # one cached copy per alpha step, so fading costs no per-frame surface work
        alpha = int(alpha) // FADE_STEP * FADE_STEP
        if alpha + FADE_STEP > 255:
            return tile.image
        key = (tile.index, tile.rotation, alpha)
        if key not in self.faded_tiles:
            image = tile.image.copy()
            image.set_alpha(alpha)
            self.faded_tiles[key] = image
        return self.faded_tiles[key]

    def group_foreground(self):
        # flood fill the foreground tiles into groups of touching tiles (diagonals count)
        self.foreground_group = {}
        self.group_alpha = []
        positions = set()
        for tilemap in self.tilemaps[self.main_layer + 1 :]:
            positions.update(tilemap)
        for start in positions:
            if start in self.foreground_group:
                continue
            group = len(self.group_alpha)
            self.group_alpha.append(255)
            self.foreground_group[start] = group
            stack = [start]
            while stack:
                x, y = stack.pop()
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        pos = (x + dx, y + dy)
                        if pos in positions and pos not in self.foreground_group:
                            self.foreground_group[pos] = group
                            stack.append(pos)

    def update_fade(self):
        rect = self.scene.player.rect().inflate(FADE_MARGIN * 2, FADE_MARGIN * 2)
        covering = set()
        for x in range(rect.left // self.tile_size, (rect.right - 1) // self.tile_size + 1):
            for y in range(rect.top // self.tile_size, (rect.bottom - 1) // self.tile_size + 1):
                if (x, y) in self.foreground_group:
                    covering.add(self.foreground_group[(x, y)])
        for group, alpha in enumerate(self.group_alpha):
            target = FADE_MIN_ALPHA if group in covering else 255
            if alpha != target:
                alpha += (target - alpha) * FADE_SPEED
                self.group_alpha[group] = target if abs(target - alpha) < 1 else alpha

    def open_json(self, level):
        with open('assets/levels/' + str(level) + '.json') as f:
            rawjson = f.read()
            jsondata = json.loads(rawjson)

        self.main_layer = jsondata['properties'][0]['value']
        self.scene.player.pos = [
            16 * jsondata['properties'][1]['value'],  # player_x
            16 * jsondata['properties'][2]['value'],
        ]  # player_y
        self.height = jsondata['height']

        # there are 3 types of layers from tiled: tile layers, text layers, wind layers.
        for i in jsondata['layers']:
            if i['type'] == 'tilelayer':
                tilemap = {}
                behind = len(self.tilemaps) < self.main_layer
                for j, val in enumerate(i['data']):
                    x = j % jsondata['width']
                    y = j // jsondata['width']
                    if val != 0:
                        rotation = 0
                        rotate_val = val // (2**29)
                        if rotate_val != 0:
                            if rotate_val == 3:
                                rotation = 90
                            elif rotate_val == 6:
                                rotation = 180
                            elif rotate_val == 5:
                                rotation = 270
                        val = val % 2**29  # this is for rotations in tiled for some reason
                        background = behind and val - 1 not in UNTINTED_TILES

                        tilemap[(x, y)] = Tile(
                            val - 1,
                            (x, y),
                            tile_types.get(val - 1),
                            rotation,
                            self.tile_image(val - 1, rotation, background),
                        )
                self.tilemaps.append(tilemap)

            elif i['class'] == 'text':
                for object in i['objects']:
                    self.texts.append(
                        (
                            object['text']['text'],
                            (int(object['x']), object['y']),
                            Style(object['text'].get('pixelsize', 16), object['text']['color']),
                        )
                    )
            elif i['class'] == 'wind':
                for wind in i['objects']:
                    self.wind_zones.append(
                        WindZone(
                            pos=(int(wind['x']), int(wind['y'])),
                            size=(int(wind['width']), int(wind['height'])),
                            x_push=wind['properties'][0][
                                'value'
                            ],  # x_push comes first in json file
                            y_push=wind['properties'][1]['value'],  # y_push
                            animation=self.scene.game.assets['wind_anim'],
                        )
                    )
        self.group_foreground()

    def tiles_around(self, pos):
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSETS:
            check_loc = (tile_loc[0] + offset[0], tile_loc[1] + offset[1])
            if check_loc in self.tilemaps[self.main_layer]:
                tiles.append(self.tilemaps[self.main_layer][check_loc])
        return tiles

    def physics_rects_around(self, pos):
        rects = {'physics': [], 'win': [], 'lose': [], 'jump': []}
        for tile in self.tiles_around(pos):
            if tile.type is None:
                continue
            rects[tile.type].append(
                pygame.rect.Rect(
                    tile.pos[0] * self.tile_size,
                    tile.pos[1] * self.tile_size,
                    self.tile_size,
                    self.tile_size,
                )
            )
        return rects

    def update(self):
        for wind_zone in self.wind_zones:
            wind_zone.update_particles()
        self.update_fade()

    def render1(self, surf, offset=(0, 0)):
        for tilemap in self.tilemaps[: self.main_layer + 1]:
            for x in range(
                math.floor(offset[0] / self.tile_size),
                math.ceil((offset[0] + surf.get_width()) / self.tile_size),
            ):
                for y in range(
                    math.floor(offset[1] / self.tile_size),
                    math.ceil((offset[1] + surf.get_height()) / self.tile_size),
                ):
                    if (x, y) in tilemap:
                        tile = tilemap[(x, y)]
                        surf.blit(
                            tile.image,
                            (
                                tile.pos[0] * self.tile_size - offset[0],
                                tile.pos[1] * self.tile_size - offset[1],
                            ),
                        )

    def render2(self, surf, offset=(0, 0)):
        for text, pos, style in self.texts:
            draw_text(surf, text, pos, style, offset)
        for wind_zone in self.wind_zones:
            wind_zone.render_particles(surf, offset)
        if not len(self.tilemaps) > self.main_layer + 1:
            return
        for tilemap in self.tilemaps[self.main_layer + 1 :]:
            for x in range(
                math.floor(offset[0] / self.tile_size),
                math.ceil((offset[0] + surf.get_width()) / self.tile_size),
            ):
                for y in range(
                    math.floor(offset[1] / self.tile_size),
                    math.ceil((offset[1] + surf.get_height()) / self.tile_size),
                ):
                    if (x, y) in tilemap:
                        tile = tilemap[(x, y)]
                        alpha = self.group_alpha[self.foreground_group[(x, y)]]
                        surf.blit(
                            self.faded_image(tile, alpha),
                            (
                                tile.pos[0] * self.tile_size - offset[0],
                                tile.pos[1] * self.tile_size - offset[1],
                            ),
                        )
