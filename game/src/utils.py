import os
from random import randint

import pygame

BASE_IMG_PATH = 'assets/images/'


def load_image(path, alpha=False, scale=1):
    if alpha:
        img = pygame.image.load(BASE_IMG_PATH + path).convert_alpha()
        img = pygame.transform.scale_by(img, scale)
        return img
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey((0, 0, 0))
    img = pygame.transform.scale_by(img, scale)
    return img


def load_images(path, alpha=False, scale=1):
    images = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        if img_name == '.DS_Store':
            continue
        images.append(load_image(path + '/' + img_name, alpha, scale))
    return images


def load_tileset(path, tile_size):
    # cuts a tileset image into tiles left-to-right, top-to-bottom, so list index == Tiled tile id
    sheet = pygame.image.load(path).convert_alpha()
    tiles = []
    for y in range(sheet.get_height() // tile_size):
        for x in range(sheet.get_width() // tile_size):
            rect = (x * tile_size, y * tile_size, tile_size, tile_size)
            tiles.append(sheet.subsurface(rect).copy())
    return tiles


class Animation:
    def __init__(self, images, img_dur, loop=True):
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0

    def copy(self):
        return Animation(self.images, self.img_duration, self.loop)

    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True

    def img(self, flip=False, direction=0):
        frame_index = int(self.frame // self.img_duration)
        if frame_index >= len(self.images):
            frame_index = len(self.images) - 1
        img = pygame.transform.flip(self.images[frame_index], flip, False)
        img = pygame.transform.rotate(img, direction)
        return img


class Music:
    def __init__(self, game):
        self.mlist = []
        for song_name in sorted(os.listdir('assets/music')):
            if song_name == '.DS_Store':
                continue
            self.mlist.append('assets/music/' + str(song_name))
        self.index = randint(0, len(self.mlist) - 1)
        self.game = game
        self.paused = False
        self.game.NEXT = pygame.USEREVENT + 1
        pygame.mixer.music.load(self.mlist[self.index])
        pygame.mixer.music.play()
        pygame.mixer.music.set_endevent(self.game.NEXT)
        pygame.mixer.music.set_volume(0.5)

    def mnext(self):
        self.index = (self.index + 1) % len(self.mlist)
        pygame.mixer.music.load(self.mlist[self.index])
        pygame.mixer.music.play()
        pygame.mixer.music.set_endevent(self.game.NEXT)
        pygame.mixer.music.set_volume(0.5)
        self.paused = False

    def update(self):
        # only touch the mixer when the setting actually changes: pausing every frame
        # goes through the browser audio path under pygbag
        if self.game.soundon and self.paused:
            pygame.mixer.music.unpause()
            self.paused = False
        elif not self.game.soundon and not self.paused:
            pygame.mixer.music.pause()
            self.paused = True


class Background:
    def __init__(self, speed, pos):
        self.speed = speed
        self.pos = list(pos)


class Backgrounds:
    def __init__(self, speed, img, move_speed, pos=(0, 0)):
        self.image = img
        self.speed = speed
        self.move_speed = move_speed
        self.left = list(pos)
        self.right = [self.left[0] + self.image.get_width(), pos[1]]

    def update(self, offset):
        self.left[0] += (
            self.move_speed - ((offset[0] * self.speed) % (self.image.get_width())) - self.left[0]
        )
        self.right[0] = self.left[0] + self.image.get_width()

        self.left[1] = -offset[1] * self.speed
        self.right[1] = -offset[1] * self.speed

        if self.right[0] <= 0:
            self.right[0] += self.image.get_width()
            self.left = self.right

    def render(self, surf):
        surf.blit(self.image, self.left)
        surf.blit(self.image, self.right)
