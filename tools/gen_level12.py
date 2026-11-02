"""Generates game/assets/levels/12.json (level 13).

Run from the repo root: python tools/gen_level12.py [output path]
Rows passed to the helpers (rect, put, ground, ...) are shifted down by DY tiles.
"""

import json
import math
import random
import sys
from pathlib import Path

random.seed(13)
W, H = 132, 34
DY = 2
NL = 5  # far, trunks, decor, main, front
FAR, TRUNK, DECOR, MAIN, FRONT = range(NL)
layers = [dict() for _ in range(NL)]

SETS = {
    'dirt': dict(
        TL=2,
        T=3,
        TR=4,
        L=51,
        R=55,
        BL=102,
        B=103,
        BR=104,
        iNW=27,
        iNE=29,
        iSW=77,
        iSE=79,
        TLb=26,
        TRb=30,
        BLb=76,
        BRb=80,
        fill=[28, 28, 52, 54, 78, 78, 53],
    ),
    'stone': dict(
        TL=252,
        T=253,
        TR=254,
        L=301,
        R=305,
        BL=352,
        B=353,
        BR=354,
        iNW=277,
        iNE=279,
        iSW=327,
        iSE=329,
        TLb=276,
        TRb=280,
        BLb=326,
        BRb=330,
        fill=[278, 302, 304, 328, 303],
    ),
    'dleaf': dict(
        TL=480,
        T=481,
        TR=482,
        L=529,
        R=533,
        BL=580,
        B=581,
        BR=582,
        iNW=505,
        iNE=507,
        iSW=555,
        iSE=557,
        TLb=504,
        TRb=508,
        BLb=554,
        BRb=558,
        fill=[531],
    ),
    'gleaf': dict(
        TL=377,
        T=378,
        TR=379,
        L=426,
        R=430,
        BL=477,
        B=478,
        BR=479,
        iNW=402,
        iNE=404,
        iSW=452,
        iSE=454,
        TLb=401,
        TRb=405,
        BLb=451,
        BRb=455,
        fill=[428],
    ),
    'dwood': dict(
        TL=307,
        T=308,
        TR=309,
        L=356,
        R=360,
        BL=407,
        B=408,
        BR=409,
        iNW=332,
        iNE=334,
        iSW=382,
        iSE=384,
        TLb=331,
        TRb=335,
        BLb=381,
        BRb=385,
        fill=[358, 357, 359, 333, 383],
    ),
    'lwood': dict(
        TL=182,
        T=183,
        TR=184,
        L=231,
        R=235,
        BL=282,
        B=283,
        BR=284,
        iNW=207,
        iNE=209,
        iSW=257,
        iSE=259,
        TLb=206,
        TRb=210,
        BLb=256,
        BRb=260,
        fill=[233, 232, 234, 208, 258],
    ),
    'purple': dict(
        TL=121,
        T=122,
        TR=123,
        L=170,
        R=174,
        BL=221,
        B=222,
        BR=223,
        iNW=146,
        iNE=148,
        iSW=196,
        iSE=198,
        TLb=145,
        TRb=149,
        BLb=195,
        BRb=199,
        fill=[172, 147, 171, 173, 197],
    ),
}


def autotile(cells, name, edge_solid=False):
    S = SETS[name]

    def has(x, y):
        if edge_solid and not (0 <= x < W and 0 <= y < H):
            return True
        return (x, y) in cells

    out = {}
    for x, y in cells:
        u, d, lf, r = has(x, y - 1), has(x, y + 1), has(x - 1, y), has(x + 1, y)
        if u and d and lf and r:
            if not has(x - 1, y - 1):
                t = S['iNW']
            elif not has(x + 1, y - 1):
                t = S['iNE']
            elif not has(x - 1, y + 1):
                t = S['iSW']
            elif not has(x + 1, y + 1):
                t = S['iSE']
            else:
                t = random.choice(S['fill'])
        elif not u:
            if not lf:
                t = S['TLb'] if has(x + 1, y - 1) else S['TL']
            elif not r:
                t = S['TRb'] if has(x - 1, y - 1) else S['TR']
            else:
                t = S['T']
        elif not d:
            if not lf:
                t = S['BLb'] if has(x + 1, y + 1) else S['BL']
            elif not r:
                t = S['BRb'] if has(x - 1, y + 1) else S['BR']
            else:
                t = S['B']
        elif not lf:
            t = S['L']
        else:
            t = S['R']
        out[(x, y)] = t
    return out


def rect(x0, y0, x1, y1):
    return {
        (x, y + DY)
        for x in range(x0, x1 + 1)
        for y in range(y0, y1 + 1)
        if 0 <= y + DY < H and 0 <= x < W
    }


def blob(x0, y0, x1, y1, r=1):
    """rounded rectangle: corners cut by r steps"""
    # the full-width band must be at least 2 tiles thick both ways, or the autotiler has no
    # edge piece for it and the shape comes out with flat, chopped sides
    assert x1 - x0 + 1 >= 2 * r + 2 and y1 - y0 + 1 >= 2 * r + 2, (x0, y0, x1, y1)
    c = set()
    for i in range(r + 1):
        c |= rect(x0 + i, y0 + (r - i), x1 - i, y1 - (r - i))
    return c


def dome(x0, y0, x1, y1):
    """bush sitting on the ground: rounded top, flat full-width bottom"""
    assert x1 - x0 + 1 >= 4 and y1 - y0 + 1 >= 3, (x0, y0, x1, y1)
    return rect(x0 + 1, y0, x1 - 1, y0) | rect(x0, y0 + 1, x1, y1)


def put(layer, x, y, tile):
    layers[layer][(x, y + DY)] = tile


# ---------------------------------------------------------------- terrain
solid = {}


def ground(x0, y0, x1, y1, m='dirt'):
    for c in rect(x0, y0, x1, y1):
        solid[c] = m


ground(0, -2, 9, 31)  # left cliff
ground(10, 22, 41, 31)  # start meadow
for x in range(10, 14):  # pond
    del solid[(x, 22 + DY)]
    solid[(x, 23 + DY)] = 'stone'
ground(22, 21, 33, 21)  # hill
ground(25, 19, 30, 20)
ground(42, 24, 62, 31, 'stone')  # spike pit
ground(63, 22, 72, 31)
ground(68, 9, 69, 17, 'stone')  # floating pillar (chimney wall)
ground(73, 11, 87, 31)  # plateau
ground(88, 24, 101, 31, 'stone')  # wind chasm
ground(102, 20, 107, 31, 'stone')  # landing
ground(108, 22, 121, 31)
ground(122, -2, 131, 31)  # right cliff

# dark core deep inside the ground
INF = 99
dist = {}
frontier = []
for x in range(W):
    for y in range(H):
        if (x, y) not in solid:
            dist[(x, y)] = 0
            frontier.append((x, y))
while frontier:
    nxt = []
    for x, y in frontier:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (x + dx, y + dy)
                if n in solid and n not in dist:
                    dist[n] = dist[(x, y)] + 1
                    nxt.append(n)
    frontier = nxt


def thr(x, y):
    return max(4, 5 + round(1.3 * math.sin(x * 0.45 + 1) + 1.3 * math.sin(y * 0.7 + 2)))


dark = {c for c in solid if dist.get(c, INF) >= thr(*c)}
changed = True
while changed:
    changed = False
    for x, y in list(dark):
        h = ((x - 1, y) in dark or x == 0) + ((x + 1, y) in dark or x == W - 1)
        v = ((x, y - 1) in dark or y == 0) + ((x, y + 1) in dark or y == H - 1)
        if h == 0 or v == 0:
            dark.discard((x, y))
            changed = True


def is_dark(x, y):
    return (x, y) in dark or not (0 <= x < W and 0 <= y < H)


for m in ('dirt', 'stone'):
    cells = {c for c, mm in solid.items() if mm == m}
    tiles = autotile(set(solid), m, edge_solid=True)
    for c in cells:
        layers[MAIN][c] = tiles[c]
for x, y in solid:
    if (x, y) in dark:
        u, d, lf, r = is_dark(x, y - 1), is_dark(x, y + 1), is_dark(x - 1, y), is_dark(x + 1, y)
        t = 178
        if not u and not lf:
            t = 152
        elif not u and not r:
            t = 154
        elif not d and not lf:
            t = 202
        elif not d and not r:
            t = 204
        layers[MAIN][(x, y)] = t
    elif dist.get((x, y), INF) >= 3:
        if (x, y + 1) in dark:
            t = 127 if not is_dark(x - 1, y + 1) else 129 if not is_dark(x + 1, y + 1) else 128
        elif (x, y - 1) in dark:
            t = 227 if not is_dark(x - 1, y - 1) else 229 if not is_dark(x + 1, y - 1) else 228
        elif (x + 1, y) in dark:
            t = 151 if not is_dark(x + 1, y - 1) else 201 if not is_dark(x + 1, y + 1) else 176
        elif (x - 1, y) in dark:
            t = 155 if not is_dark(x - 1, y - 1) else 205 if not is_dark(x - 1, y + 1) else 180
        else:
            continue
        layers[MAIN][(x, y)] = t

# a few vine patches on cliff faces
for x, y in [
    (8, 13),
    (7, 17),
    (8, 20),
    (74, 14),
    (75, 18),
    (86, 15),
    (85, 19),
    (123, 11),
    (123, 18),
    (27, 20),
    (66, 23),
    (110, 23),
    (36, 23),
]:
    if layers[MAIN].get((x, y + DY)) in SETS['dirt']['fill']:
        put(MAIN, x, y, 61)

# ---------------------------------------------------------------- hazards / interactives
for x in range(42, 63):
    put(MAIN, x, 23, 211)
for x in range(88, 102):
    put(MAIN, x, 23, 211)


def branch(y, x0, x1, tx, layer=MAIN):
    for x in range(x0, x1 + 1):
        if x == tx:
            t = 434
        elif x == tx + 1:
            t = 435
        elif x == x0:
            t = 431
        elif x == x1:
            t = 438
        elif x < tx:
            t = 432 if (tx - x) % 2 else 433
        elif x == tx + 2:
            t = 436
        else:
            t = 437
        put(layer, x, y, t)


def trunk(tx, y0, y1):
    # Always drawn, even behind main-layer tiles: spikes and corner tiles are partly
    # transparent, so a skipped cell would leave the trunk floating above them. One extra
    # row at the bottom roots the trunk in the ground for the same reason.
    for y in range(y0, y1 + 2):
        put(TRUNK, tx, y, 434)
        put(TRUNK, tx + 1, y, 435)


leaf = {'gleaf': set(), 'dleaf': set(), 'purple': set()}


def canopy(x0, y0, x1, y1, r=1, back=(-1, -1, 1, 1), kind='gleaf'):
    leaf[kind] |= blob(x0, y0, x1, y1, r)
    if back:
        leaf['dleaf'] |= blob(x0 + back[0], y0 + back[1], x1 + back[2], y1 + back[3], r)


# pit trees
branch(20, 44, 49, 46)
put(MAIN, 49, 19, 92)  # mushroom on the branch tip
trunk(46, 11, 23)
canopy(43, 7, 50, 11, back=(-1, -1, 1, 1))

branch(14, 51, 56, 53)
trunk(53, 8, 23)
canopy(50, 4, 58, 9, r=2, back=(-1, -1, 2, 1))

branch(18, 58, 63, 60)
trunk(60, 11, 23)
canopy(57, 9, 64, 12, back=(-1, -1, 1, 1))

# chimney mushroom
put(MAIN, 71, 21, 67)

# goal tree
branch(17, 114, 119, 114)
branch(14, 111, 118, 114)
trunk(114, 8, 21)
for c, t in autotile(blob(112, 10, 119, 13, 1), 'dwood').items():
    layers[FAR][c] = t
canopy(110, 4, 120, 9, r=2, back=(-1, -1, 1, 1))
put(DECOR, 116, 11, 84), put(DECOR, 117, 11, 85), put(DECOR, 118, 11, 87)
put(DECOR, 116, 12, 109), put(DECOR, 118, 12, 112)
put(DECOR, 116, 13, 134), put(DECOR, 118, 13, 137)
put(MAIN, 117, 13, 66)  # bamboo (win)
put(MAIN, 120, 21, 67)  # mushroom up to the lower branch

# ---------------------------------------------------------------- start area
# waterfall + pond
for y in range(-2, 22):
    put(TRUNK, 10, y, 185)
    put(TRUNK, 11, y, 185)
for x in range(10, 14):
    put(TRUNK, x, 22, 59 if x % 2 == 0 else 60)
# swing gate
gx = 16
(
    put(DECOR, gx, 19, 84),
    put(DECOR, gx + 1, 19, 85),
    put(DECOR, gx + 2, 19, 86),
    put(DECOR, gx + 3, 19, 87),
)
put(DECOR, gx, 20, 109), put(DECOR, gx + 2, 20, 111), put(DECOR, gx + 3, 20, 112)
put(DECOR, gx, 21, 134), put(DECOR, gx + 3, 21, 137)

# background trees (no branches -> not climbable)
trunk(27, 9, 18)
canopy(23, 4, 31, 9, r=2, back=(-1, -1, 2, 1))
trunk(37, 13, 21)
canopy(34, 9, 40, 13, back=(-1, -1, 1, 1))
trunk(84, 3, 10)
canopy(81, -1, 88, 4, r=2, back=None, kind='purple')
trunk(105, 12, 19)
canopy(102, 8, 108, 12, back=(-1, -1, 1, 1))

# hedges far behind the ground line
for x0, y0, x1, y1 in [(21, 18, 25, 23), (64, 19, 67, 23), (108, 19, 112, 23), (30, 19, 35, 23)]:
    leaf['dleaf'] |= blob(x0, y0, x1, y1, 1)
for kind, L in (('dleaf', FAR), ('gleaf', DECOR), ('purple', DECOR)):
    # Ground edge and corner tiles have transparent pixels along their open side. Run the
    # foliage two tiles into any ground it touches, so its opaque fill (not its own feathered
    # edge, and not the sky) is what shows through those pixels.
    cells = set(leaf[kind])
    for x, y in leaf[kind]:
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if (x + dx, y + dy) in solid:
                    cells.add((x + dx, y + dy))
    for c, t in autotile(cells, kind).items():
        if c not in layers[L]:
            layers[L][c] = t

# plateau: fence + crates
for i, t in enumerate([105, 106, 107, 108]):
    put(DECOR, 79 + i, 10, t)
put(MAIN, 75, 9, 57), put(MAIN, 76, 9, 58), put(MAIN, 75, 10, 82), put(MAIN, 76, 10, 83)
put(MAIN, 77, 10, 81)

# pillar top + vines
put(DECOR, 68, 8, 63)


# ---------------------------------------------------------------- plants
def surface(x):
    for y in range(H):
        if (x, y) in solid:
            return y
    return None


def free(x, y):
    return all((x, y) not in L for L in (layers[DECOR], layers[MAIN], layers[FRONT]))


blocked = set(range(15, 21)) | {70, 71, 72, 119, 120, 121} | set(range(75, 83)) | set(range(10, 14))
x = 10
while x < 122:
    y = surface(x)
    if y is None or solid[(x, y)] != 'dirt' or x in blocked or not free(x, y - 1):
        x += 1
        continue
    roll = random.random()
    front = random.random() < 0.3
    L = FRONT if front else DECOR
    same = (
        surface(x + 1) == y
        and (x + 1) not in blocked
        and free(x + 1, y - 1)
        and solid.get((x + 1, y)) == 'dirt'
    )
    if roll < 0.10 and same:
        layers[L][(x, y - 1)] = 64
        layers[L][(x + 1, y - 1)] = 65
        x += 2
    elif roll < 0.16 and same and free(x, y - 2) and free(x + 1, y - 2):
        layers[DECOR][(x, y - 2)] = 16
        layers[DECOR][(x + 1, y - 2)] = 17
        layers[DECOR][(x, y - 1)] = 41
        layers[DECOR][(x + 1, y - 1)] = 42
        x += 2
    elif roll < 0.30:
        layers[L][(x, y - 1)] = 13
        x += 1
    elif roll < 0.48:
        layers[L][(x, y - 1)] = 14
        x += 1
    elif roll < 0.56:
        layers[DECOR][(x, y - 1)] = 15
        x += 1
    elif roll < 0.66:
        layers[L][(x, y - 1)] = 39
        x += 1
    elif roll < 0.72:
        layers[L][(x, y - 1)] = 63
        x += 1
    elif roll < 0.76:
        layers[DECOR][(x, y - 1)] = random.choice([68, 93])
        x += 1
    else:
        x += 1
# leafy bushes in front of the player (they fade when the player walks behind them)
front_leaf = (
    dome(36, 19, 39, 21) | dome(64, 19, 67, 21) | dome(109, 19, 112, 21) | dome(83, 8, 86, 10)
)
for c, t in autotile(front_leaf, 'gleaf').items():
    layers[FRONT][c] = t
# small purple mushrooms next to the bouncy ones
put(DECOR, 70, 21, 93)
put(DECOR, 121, 21, 68)


# ---------------------------------------------------------------- export
def layer_json(i, name, cells):
    data = [0] * (W * H)
    for (x, y), t in cells.items():
        if 0 <= x < W and 0 <= y < H:
            data[y * W + x] = t + 1
    return {
        'data': data,
        'height': H,
        'id': i + 1,
        'name': name,
        'opacity': 1,
        'type': 'tilelayer',
        'visible': True,
        'width': W,
        'x': 0,
        'y': 0,
    }


def text(i, s, x, y, size=8):
    return {
        'height': 30,
        'id': i,
        'name': '',
        'rotation': 0,
        'text': {
            'color': '#eb5428',
            'fontfamily': 'Public Pixel',
            'pixelsize': size,
            'text': s,
            'wrap': True,
        },
        'type': '',
        'visible': True,
        'width': 160,
        'x': x,
        'y': y + DY * 16,
    }


names = ['Far Background', 'Trunks and Water', 'Decor', 'Main', 'Foreground']
out_layers = [layer_json(i, names[i], layers[i]) for i in range(NL)]
out_layers.append(
    {
        'class': 'text',
        'draworder': 'topdown',
        'id': 6,
        'name': 'Text',
        'objects': [
            text(1, 'trust the\nwind', 78 * 16, 6 * 16),
        ],
        'opacity': 1,
        'type': 'objectgroup',
        'visible': True,
        'x': 0,
        'y': 0,
    }
)
out_layers.append(
    {
        'class': 'wind',
        'draworder': 'topdown',
        'id': 7,
        'name': 'Wind',
        'objects': [
            {
                'height': 11 * 16,
                'id': 2,
                'name': 'updraft',
                'properties': [
                    {'name': 'x_push', 'type': 'float', 'value': 0},
                    {'name': 'y_push', 'type': 'float', 'value': -4.5},
                ],
                'rotation': 0,
                'type': '',
                'visible': True,
                'width': 176,
                'x': 88 * 16 + 24,
                'y': (12 + DY) * 16,
            }
        ],
        'opacity': 1,
        'type': 'objectgroup',
        'visible': True,
        'x': 0,
        'y': 0,
    }
)

level = {
    'compressionlevel': -1,
    'height': H,
    'infinite': False,
    'layers': out_layers,
    'nextlayerid': 8,
    'nextobjectid': 3,
    'orientation': 'orthogonal',
    'properties': [
        {'name': 'main_layer', 'type': 'int', 'value': MAIN},
        {'name': 'player_x', 'type': 'int', 'value': 17},
        {'name': 'player_y', 'type': 'int', 'value': 21 + DY},
    ],
    'renderorder': 'right-down',
    'tiledversion': '1.11.0',
    'tileheight': 16,
    'tilesets': [{'firstgid': 1, 'source': '../redpandarun.json'}],
    'tilewidth': 16,
    'type': 'map',
    'version': '1.10',
    'width': W,
}

default_path = Path(__file__).resolve().parent.parent / 'game/assets/levels/12.json'
out_path = sys.argv[1] if len(sys.argv) > 1 else default_path
with open(out_path, 'w') as f:
    json.dump(level, f)
print('wrote', out_path)
