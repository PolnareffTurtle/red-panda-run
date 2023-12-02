import pygame

class PhysicsEntity():
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)

        self.size = size
        self.velocity = [0,0]
        self.action = ''
        self.anim_offset = (0,0)
        self.flip = False
        self.set_action('idle')

        self.last_movement = [0,0]

    def rect(self):
        return pygame.rect.Rect(self.pos[0],self.pos[1],self.size[0],self.size[1])

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '_' + self.action].copy()




    def update(self, tilemap, movement = (0,0)):
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        frame_movement = (movement[0]*2 + self.velocity[0], movement[1] + self.velocity[1])

        rects = tilemap.physics_rects_around(self.pos)

        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect in rects['0']:
            #self.rect_render(rect)
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x

        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()

        rects = tilemap.physics_rects_around(self.pos)

        for rect in rects['0']:
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y

        for rect in rects['2']:
            if entity_rect.colliderect(rect):
                self.game.gamestate = self.game.LOSE
        for rect in rects['1']:
            if entity_rect.colliderect(rect):
                self.game.gamestate = self.game.WIN

        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True

        self.last_movement = movement

        self.velocity[1] = min(10, self.velocity[1] + 0.25)  # 10 is the terminal velocity

        if self.collisions['up'] or self.collisions['down']:
            self.velocity[1] = 0

        self.animation.update()

    def render(self, surf,offset=(0,0)):
        surf.blit(pygame.transform.flip(self.animation.img(),self.flip,False),(self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))
        #pygame.draw.rect(self.game.display,(0,0,255),pygame.rect.Rect(self.pos[0]-offset[0],self.pos[1]-offset[1],self.size[0],self.size[1]),width=1)
class Background():
    def __init__(self,speed,pos):
        self.speed = speed
        self.pos = list(pos)

class Backgrounds():
    def __init__(self,speed,img,pos=(0,0)):
        self.image = img
        self.speed = speed
        self.left = Background(speed,pos)
        self.right = Background(speed,(self.left.pos[0]+self.image.get_width(),0))

    def update(self,offset):
        self.left.pos[0] += -((offset[0] * self.speed)%(self.image.get_width())) - self.left.pos[0]
        self.right.pos[0] = self.left.pos[0] + self.image.get_width()

        self.left.pos[1] = -offset[1]*self.speed
        self.right.pos[1] = -offset[1] * self.speed

        if self.right.pos[0] <= 0:
            self.right.pos[0] += self.image.get_width()
            self.left = self.right


    def render(self,surf):
        surf.blit(self.image, (self.left.pos[0], self.left.pos[1]))
        surf.blit(self.image, (self.right.pos[0], self.right.pos[1]))

class Player(PhysicsEntity):
    def __init__(self,game,pos,size):
        super().__init__(game,'player',pos,size)
        self.air_time=0
        self.jumps = 1

    def update(self, tilemap, movement= (0,0)):
        super().update(tilemap,movement=movement)

        if self.pos[1] > 300:
            self.game.gamestate = self.game.LOSE

        self.air_time += 1
        if self.collisions['down']:
            self.air_time = 0
            self.jumps = 1

        self.wall_slide = False
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1],0.5)
            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True
            self.set_action('wall_slide')

        if not self.wall_slide:
            if self.air_time > 4:
                self.set_action('jump')
                self.jumps=0
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')

        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0]-0.1,0)
        if self.velocity[0] < 0:
            self.velocity[0] = min(self.velocity[0]+0.1,0)

    def jump(self):
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 3.5
                self.velocity[1] = -3.5
                self.air_time = 5
                self.jumps = max(0,self.jumps-1)
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -3.5
                self.velocity[1] = -3.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
        elif self.jumps:
            self.velocity[1] = -6
            self.jumps -= 1
            self.air_time = 5