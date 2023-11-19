import pygame
import os
from random import randint

BASE_IMG_PATH = 'data/images/'

def load_image(path,alpha=False):
    if alpha:
        img = pygame.image.load(BASE_IMG_PATH + path).convert_alpha()
        return img
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey((0,0,0))
    return img

def load_images(path,alpha=False):
    images = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        if img_name == '.DS_Store':
            continue
        images.append(load_image(path + '/' + img_name, alpha))
    return images

class Animation():
    def __init__(self,images,img_dur,loop=True):
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0

    def copy(self):
        return Animation(self.images, self.img_duration,self.loop)

    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True

    def img(self,flip=False):
        return pygame.transform.flip(self.images[int(self.frame/self.img_duration)],flip,False)


class Text():
    def __init__(self,text,size,color,pos):
        self.text = text
        self.color = color
        self.pos = pos
        self.font = pygame.font.Font('data/fonts/PublicPixel.ttf',size)
        self.image = self.font.render(text,True,color)

    def render(self,surf):
        surf.blit(self.image,self.pos)

class Music():
    def __init__(self,game):
        self.mlist = []
        for song_name in sorted(os.listdir('data/music')):
            if song_name == '.DS_Store':
                continue
            self.mlist.append('data/music/'+str(song_name))
        self.index = randint(0,4)
        self.game = game
        self.game.NEXT = pygame.USEREVENT + 1
        pygame.mixer.music.load(self.mlist[self.index])
        pygame.mixer.music.play()
        pygame.mixer.music.set_endevent(self.game.NEXT)
        pygame.mixer.music.set_volume(0.5)

    def mnext(self):
        self.index=(self.index+1)%len(self.mlist)
        pygame.mixer.music.load(self.mlist[self.index])
        pygame.mixer.music.play()
        pygame.mixer.music.set_endevent(self.game.NEXT)
        pygame.mixer.music.set_volume(0.5)
    def update(self):
        if not self.game.soundon:
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()