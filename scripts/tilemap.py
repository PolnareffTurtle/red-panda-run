import pygame
import math
import json



NEIGHBOR_OFFSETS = [
    (-1,-1), (0,-1), (1,-1), (2,-1),
    (-1,0),  (0,0),  (1,0),  (2,0),
    (-1,1),  (0,1),  (1,1),  (2,1)
]
PHYSICS_TILES = {2,3,4,26,27,28,29,30,51,52,53,54,55,76,77,78,79,80,102,103,104,402,403,404,426,427,428,429,430,452,453,454,431,432,433,434,435,436,437,438,459,460,251,252,253,254,255,276,277,278,279,280,301,302,303,304,305,326,327,328,329,330,352,353,354,127,128,129,151,152,154,155,176,180,201,202,204,205,227,228,229}

WIN_TILE = 66
LOSE_TILE = 211
class Tile():
    def __init__(self, tile_index, pos):
        self.index = tile_index
        self.pos = pos

class Tilemaps():
    def __init__(self, game, level, tile_size = 16):

        self.game = game
        self.tile_size = tile_size
        self.tilemaps = []
        self.offgrid_tiles = []
        self.open_json(level)

    def open_json(self,level):
        with open('data/levels/'+str(level)+'.json') as f:
            rawjson = f.read()
            jsondata = json.loads(rawjson)

        self.main_layer = jsondata['properties'][0]['value']

        for i in range(len(jsondata['layers'])):
            tilemap = {}
            for i, val in enumerate(jsondata['layers'][i]['data']):
                if val != 0:
                    tilemap[str(i%jsondata['width']) + ';' + str(i//jsondata['width'])] = Tile(val-1,(i%jsondata['width'],i//jsondata['width']))
            self.tilemaps.append(tilemap)

    def tiles_around(self,pos):
        tiles=[]
        tile_loc = (int(pos[0] // self.tile_size),int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSETS:
            check_loc = str(tile_loc[0]+offset[0]) + ';' + str(tile_loc[1]+offset[1])
            if check_loc in self.tilemaps[self.main_layer]:
                tiles.append(self.tilemaps[self.main_layer][check_loc])
        return tiles

    def physics_rects_around(self,pos):
        rectangles,win,lose = [],[],[]
        for tile in self.tiles_around(pos):
            if tile.index != 0:
                if tile.index in PHYSICS_TILES:
                    rectangles.append(pygame.rect.Rect(tile.pos[0]*self.tile_size,tile.pos[1]*self.tile_size,self.tile_size,self.tile_size))
                elif tile.index == WIN_TILE:
                    win.append(pygame.rect.Rect(tile.pos[0]*self.tile_size,tile.pos[1]*self.tile_size,self.tile_size,self.tile_size))
                elif tile.index == LOSE_TILE:
                    lose.append(pygame.rect.Rect(tile.pos[0]*self.tile_size,tile.pos[1]*self.tile_size,self.tile_size,self.tile_size))
        return {'0': rectangles,'1': win,'2': lose}

    def render1(self, surf, offset=(0,0)):
        for tile in self.offgrid_tiles:
            surf.blit(self.game.assets[tile.type][tile.index], (tile.pos[0]-offset[0],tile.pos[1]-offset[1]))
        for tilemap in self.tilemaps[:self.main_layer+1]:
            for x in range(math.floor(offset[0] / self.tile_size), math.ceil((offset[0] + surf.get_width()) / self.tile_size)):
                for y in range(math.floor(offset[1] / self.tile_size), math.ceil((offset[1] + surf.get_height()) / self.tile_size)):
                    loc = str(x) + ';' + str(y)
                    if loc in tilemap:
                        tile = tilemap[loc]
                        surf.blit(self.game.assets['all_tiles'][tile.index],(tile.pos[0]*self.tile_size - offset[0], tile.pos[1]*self.tile_size - offset[1]))
    def render2(self, surf, offset=(0,0)):
        if len(self.tilemaps) > self.main_layer + 1:
            for tilemap in self.tilemaps[self.main_layer+1:]:
                for x in range(math.floor(offset[0] / self.tile_size), math.ceil((offset[0] + surf.get_width()) / self.tile_size)):
                    for y in range(math.floor(offset[1] / self.tile_size), math.ceil((offset[1] + surf.get_height()) / self.tile_size)):
                        loc = str(x) + ';' + str(y)
                        if loc in tilemap:
                            tile = tilemap[loc]
                            surf.blit(self.game.assets['all_tiles'][tile.index],(tile.pos[0]*self.tile_size - offset[0], tile.pos[1]*self.tile_size - offset[1]))
