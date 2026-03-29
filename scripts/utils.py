import pygame
import os
from random import randint

BASE_IMG_PATH = 'data/images/'

def load_image(path,alpha=False,scale=1):
    if alpha:
        img = pygame.image.load(BASE_IMG_PATH + path).convert_alpha()
        img = pygame.transform.scale_by(img,scale)
        return img
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey((0,0,0))
    img = pygame.transform.scale_by(img,scale)
    return img

def load_images(path,alpha=False,scale=1):
    images = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        if img_name == '.DS_Store':
            continue
        images.append(load_image(path + '/' + img_name, alpha, scale))
    return images

class Animation:
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

    def img(self,flip=False,direction=0):
        frame_index = int(self.frame // self.img_duration)
        if frame_index >= len(self.images):
            frame_index = len(self.images) - 1
        img = pygame.transform.flip(self.images[frame_index],flip,False)
        img = pygame.transform.rotate(img, direction)
        return img


class Text:
    def __init__(self,text,size,color,pos):
        self.texts = text.split('\n')
        self.color = color
        self.pos = pos
        self.size = size
        self.font = pygame.font.Font('data/fonts/PublicPixel.ttf',self.size)
        self.images = [self.font.render(text,True,color) for text in self.texts]

    def render(self,surf,offset=(0,0)):
        for i in range(len(self.images)):
            surf.blit(self.images[i],(self.pos[0]-offset[0],int(self.size*i*1.2) + (self.pos[1]-offset[1])))
class Music:
    def __init__(self,game):
        self.mlist = []
        for song_name in sorted(os.listdir('data/music')):
            if song_name == '.DS_Store':
                continue
            self.mlist.append('data/music/'+str(song_name))
        self.index = randint(0,len(self.mlist)-1)
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

class Background:
    def __init__(self,speed,pos):
        self.speed = speed
        self.pos = list(pos)

class Backgrounds:
    def __init__(self,speed,img,move_speed,pos=(0,0)):
        self.image = img
        self.speed = speed
        self.move_speed = move_speed
        self.left = list(pos)
        self.right = [self.left[0]+self.image.get_width(),pos[1]]

    def update(self,offset):
        self.left[0] += self.move_speed -((offset[0] * self.speed)%(self.image.get_width())) - self.left[0]
        self.right[0] = self.left[0] + self.image.get_width()

        self.left[1] = -offset[1]*self.speed
        self.right[1] = -offset[1] * self.speed

        if self.right[0] <= 0:
            self.right[0] += self.image.get_width()
            self.left = self.right

    def render(self,surf):
        surf.blit(self.image, self.left)
        surf.blit(self.image, self.right)
