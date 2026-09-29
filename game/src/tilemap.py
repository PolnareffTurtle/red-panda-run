import json
import math

import pygame

from src.utils import Text
from src.wind import WindZone

with open('assets/redpandarun.json') as f:
    rawjson = f.read()
    jsondata = json.loads(rawjson)
tile_types = {}
for i in jsondata['tiles']:
    tile_types[i['id']] = i['type']

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
    def __init__(self, game, level, tile_size=16):

        self.game = game
        self.tile_size = tile_size
        self.tilemaps = []
        self.wind_zones = []
        self.texts = []
        self.rotated_tiles = {}
        self.open_json(level)

    def tile_image(self, index, rotation):
        # rotate once at load time; render1/render2 would otherwise allocate a new
        # surface for every visible tile on every frame
        if (index, rotation) not in self.rotated_tiles:
            self.rotated_tiles[(index, rotation)] = pygame.transform.rotate(
                self.game.assets['all_tiles'][index], rotation
            )
        return self.rotated_tiles[(index, rotation)]

    def open_json(self, level):
        with open('assets/levels/' + str(level) + '.json') as f:
            rawjson = f.read()
            jsondata = json.loads(rawjson)

        self.main_layer = jsondata['properties'][0]['value']
        self.game.player.pos = [
            16 * jsondata['properties'][1]['value'],  # player_x
            16 * jsondata['properties'][2]['value'],
        ]  # player_y
        self.height = jsondata['height']

        # there are 3 types of layers from tiled: tile layers, text layers, wind layers.
        for i in jsondata['layers']:
            if i['type'] == 'tilelayer':
                tilemap = {}
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

                        tilemap[(x, y)] = Tile(
                            val - 1,
                            (x, y),
                            tile_types.get(val - 1),
                            rotation,
                            self.tile_image(val - 1, rotation),
                        )
                self.tilemaps.append(tilemap)

            elif i['class'] == 'text':
                for object in i['objects']:
                    self.texts.append(
                        Text(
                            object['text']['text'],
                            object['text'].get('pixelsize', 16),
                            object['text']['color'],
                            (int(object['x']), object['y']),
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
                            animation=self.game.assets['wind_anim'],
                        )
                    )

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
        for text in self.texts:
            text.render(surf, offset)
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
                        surf.blit(
                            tile.image,
                            (
                                tile.pos[0] * self.tile_size - offset[0],
                                tile.pos[1] * self.tile_size - offset[1],
                            ),
                        )
