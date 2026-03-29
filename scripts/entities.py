import pygame
from scripts.gamestate import GameState

class PhysicsEntity:
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

    # TODO: Rework the wind_y to be based on terminal velocity, not subtracting a fixed velocity

    def check_collisions(self,axis: int,rects,frame_movement):
        if not rects:
            return
        self.pos[axis] += frame_movement[axis]
        entity_rect = self.rect()
        for rect in rects['physics']:
            #self.rect_render(rect)    #<--- DEBUGGING
            if entity_rect.colliderect(rect):
                if frame_movement[axis] > 0:
                    if axis == 0:
                        entity_rect.right = rect.left
                        self.collisions['right'] = True
                    else:
                        entity_rect.bottom = rect.top
                        self.collisions['down'] = True
                if frame_movement[axis] < 0:
                    if axis == 0:
                        entity_rect.left = rect.right
                        self.collisions['left'] = True
                    else:
                        entity_rect.top = rect.bottom
                        self.collisions['up'] = True
                self.pos[axis] = entity_rect.x if axis == 0 else entity_rect.y

    def update(self, tilemap, movement = (0,0)):
        terminal_velocity = 10
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}

        # if player is in the wind regions, update velocity
        wind_x,wind_y=0,0
        for wind in tilemap.wind_zones: 
            if self.rect().colliderect(wind.rect):
                wind_x += wind.x_push
                terminal_velocity += 2*wind.y_push
        frame_movement = (movement[0]*2 + self.velocity[0] + wind_x, movement[1] + self.velocity[1])
        rects = tilemap.physics_rects_around(self.pos)

        self.check_collisions(1, rects, frame_movement) # check vertical collisions
        self.check_collisions(0, rects, frame_movement) # check horizontal collisions

        entity_rect = self.rect()
        for rect in rects['lose']:
            if entity_rect.collidepoint(rect.center):
                self.game.gamestate = GameState.LOSE
        for rect in rects['win']:
            if entity_rect.colliderect(rect):
                self.game.gamestate = GameState.WIN
        for rect in rects['jump']:
            if entity_rect.collidepoint(rect.center):
                self.velocity[1] = -8

        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True

        self.last_movement = movement

        # update y velocity based on terminal velocity
        self.velocity[1] = min(terminal_velocity, self.velocity[1] + terminal_velocity * 0.025)  # 10 is the terminal velocity

        if self.collisions['up'] or self.collisions['down']:
            self.velocity[1] = 0

        self.animation.update()

    def render(self, surf,offset=(0,0)):
        surf.blit(pygame.transform.flip(self.animation.img(),self.flip,False),(self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]-15+self.size[1]))
        #pygame.draw.rect(self.game.display,(0,0,255),pygame.rect.Rect(self.pos[0]-offset[0],self.pos[1]-offset[1],self.size[0],self.size[1]),width=1)


class Player(PhysicsEntity):
    def __init__(self,game,pos,size):
        super().__init__(game,'player',pos,size)
        self.air_time=0
        self.jumps = 1

    def update(self, tilemap, movement= (0,0)):
        super().update(tilemap,movement=movement)

        if self.pos[1] > 16 * self.game.tilemaps.height:
            self.game.gamestate = GameState.LOSE

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
