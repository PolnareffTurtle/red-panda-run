import pygame
from sys import exit
from random import randint
import math
from scripts.entities import PhysicsEntity, Backgrounds, Player
from scripts.utils import load_image, load_images, Animation, Text, Music
from scripts.tilemap import Tilemap

class Game():
    MAIN_MENU = 0
    LEVEL_SELECT = 1
    GAME_MENU = 2
    GAME_RUNNING = 3
    OPTIONS = 4
    TRANSITION_OUT = 5
    TRANSITION_IN = 6

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((960,720))
        pygame.display.set_caption('Red Panda Run')
        self.display = pygame.Surface((320,240))
        self.clock = pygame.time.Clock()
        self.movement = [False,False]

        self.scroll = [0,0]
        self.gamestate = Game.MAIN_MENU
        self.level = 0

        self.sound_index, self.res_index = 0, 2
        self.soundon = True
        self.resolution = self.screen.get_size()

        self.musics = Music(self)

        self.assets = {
            'all_tiles': load_images('tiles',True),
            'backgrounds': load_images('background'),
            'player': load_image('player/idle/0.png'),
            'player_idle': Animation(load_images('player/idle'),img_dur=20),
            'player_jump': Animation(load_images('player/jump'),img_dur=5),
            'player_run': Animation(load_images('player/run'),img_dur=5),
            'player_wall_slide': Animation(load_images('player/wall_slide'),img_dur=5)
        }

        self.player = Player(self,(0,0),(22,15))

        self.background0 = Backgrounds(0.1,self.assets['backgrounds'][0],(0,0))
        self.background1 = Backgrounds(0.2, self.assets['backgrounds'][1], (0, 0))

    def transition_out(self):
        i=0
        while True:
            if i>360:
                break
            i+=7
            pygame.draw.rect(self.display,(0,0,0),pygame.rect.Rect(0,0,i,self.display.get_height()))

            self.clock.tick(60)
            pygame.display.update()
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
    def transition_in(self,i):
        pygame.draw.rect(self.display, (0, 0, 0), pygame.rect.Rect(i, 0, self.display.get_width(), self.display.get_height()))

    def win(self):
        Text(':)',24,(0, 0, 0),(self.player.pos[0]-self.render_scroll[0],self.player.pos[1]-20-self.render_scroll[1])).render(self.display)
        self.transition_out()
        if self.level == 5:
            self.gamestate = Game.MAIN_MENU
        else:
            self.level += 1
            self.gamestate = Game.GAME_MENU

    def lose(self):
        if self.player.pos[1] > 300:
            self.player.pos[1] = 300
        Text('😟', 24, (235, 84, 40), (self.player.pos[0]-self.render_scroll[0], self.player.pos[1] - 20 - self.render_scroll[1])).render(self.display)
        self.transition_out()
        self.gamestate = Game.GAME_MENU
    def main_menu(self):
        #self.transition_in()
        texts = {
            Text('Red Panda Run', 16, (146, 52, 22), (29, 21)),
            Text('Continue', 16, (146, 52, 22), (30, 50)),
            Text('Level Select', 16, (146, 52, 22), (30, 70)),
            Text('Options', 16, (146, 52, 22), (30, 90)),
            Text('Press [ENTER]', 8, (235, 84, 40), (80, 170)),
            Text('to select', 8, (235, 84, 40), (110, 180))
        }
        texts2 = {
            Text('Red Panda Run', 16, (235, 84, 40), (30, 20))
        }
        option_index=0
        r1=randint(-100,-50)
        r2=randint(-100,0)
        i=0
        while self.gamestate == Game.MAIN_MENU:


            self.display.blit(self.assets['backgrounds'][0],(r1,0))
            self.display.blit(self.assets['backgrounds'][1],(r2,0))

            for text in texts:
                text.render(self.display)
            for text in texts2:
                text.render(self.display)

            marker = Text('>',16,(235, 84, 40),(10,48+20*option_index))
            marker.render(self.display)

            logo = self.assets['player_idle']
            self.display.blit(pygame.transform.scale(logo.img(flip=True),(132,90)),(180,130))
            logo.update()

            self.musics.update()

            if i <360:
                self.transition_in(i)
            i+=7

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == self.NEXT:
                    self.musics.mnext()
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_RETURN,pygame.K_KP_ENTER]:
                        self.transition_out()
                        self.gamestate = [Game.GAME_MENU,Game.LEVEL_SELECT,Game.OPTIONS][option_index]
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP:
                        option_index = (option_index - 1) % 3
                    elif event.key == pygame.K_DOWN:
                        option_index = (option_index + 1) % 3

            self.clock.tick(60)
            pygame.display.update()
            self.screen.blit(pygame.transform.scale(self.display,self.screen.get_size()),(0,0))

    def level_select(self):
        texts = {
            Text('Levels', 16, (146, 52, 22), (119, 21)),
            Text('[1]', 16, (146, 52, 22), (70, 60)),
            Text('[2]', 16, (146, 52, 22), (140, 60)),
            Text('[3]', 16, (146, 52, 22), (210, 60)),
            Text('[4]', 16, (146, 52, 22), (70, 100)),
            Text('[5]', 16, (146, 52, 22), (140, 100)),
            Text('[6]', 16, (146, 52, 22), (210, 100)),
            Text('Press [ENTER]', 8, (235, 84, 40), (140, 170)),
            Text('to select', 8, (235, 84, 40), (140, 180)),
            Text('[ESC]', 8, (235, 84, 40), (10,10))
        }

        texts2 = {
            Text('Levels', 16, (235, 84, 40), (120, 20)),
        }

        option_index = 0
        r1 = randint(-100, -50)
        r2 = randint(-100, 0)
        i=0
        while self.gamestate == Game.LEVEL_SELECT:


            self.display.blit(self.assets['backgrounds'][0], (r1, 0))
            self.display.blit(self.assets['backgrounds'][1], (r2, 0))

            for text in texts:
                text.render(self.display)
            for text in texts2:
                text.render(self.display)

            logo = self.assets['player_idle']
            self.display.blit(pygame.transform.scale(logo.img(), (132, 90)), (10, 130))
            logo.update()

            marker = Text('>', 16, (235, 84, 40), (50+70*(option_index%3), 58 + 40 * (option_index//3)))
            marker.render(self.display)

            self.musics.update()

            if i <360:
                self.transition_in(i)
            i+=7

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == self.NEXT:
                    self.musics.mnext()
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_RETURN,pygame.K_KP_ENTER]:
                        self.level=option_index
                        self.gamestate = Game.GAME_MENU
                        self.transition_out()
                    if event.key == pygame.K_ESCAPE:
                        self.gamestate = Game.MAIN_MENU
                        self.transition_out()

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP:
                        option_index = (option_index - 3) % 6
                    elif event.key == pygame.K_DOWN:
                        option_index = (option_index + 3) % 6
                    elif event.key == pygame.K_LEFT:
                        option_index = (option_index - 1) % 6
                    elif event.key == pygame.K_RIGHT:
                        option_index = (option_index + 1) % 6

            self.clock.tick(60)
            pygame.display.update()
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))

    def options_menu(self):
        y=0
        texts = {
            Text('Options', 16, (255,255,255), (120, 20)),
            Text('Sound:', 16, (255, 255, 255), (30, 50)),
            Text('Resolution:', 16, (255, 255, 255), (30, 70)),
            Text('[ESC]', 8, (255,255,255), (10, 10)),
            Text('Use arrow keys', 8, (255,255,255), (140, 170)),
            Text('to change', 8, (255,255,255), (140, 180)),
        }
        options={
            'sound': {
                'images': [
                    Text('On', 16, (255, 255, 255), (220, 50)),
                    Text('Off', 16, (255, 255, 255), (220, 50)),
                ],
                'vals': [
                    True,
                    False
                ]

            },
            'resolution': {
                'images': [
                    Text('320x240', 8, (255, 255, 255), (220, 76)),
                    Text('640x480', 8, (255, 255, 255), (220, 76)),
                    Text('960x720', 8, (255, 255, 255), (220, 76)),
                    Text('1280x960', 8, (255, 255, 255), (220, 76)),
                ],
                'vals': [
                    (320,240),
                    (640,480),
                    (960,720),
                    (1280,960)
                ]
            }
        }
        i=0



        while self.gamestate == Game.OPTIONS:
            self.display.fill((235, 84, 40))

            for text in texts:
                text.render(self.display)
            options['sound']['images'][self.sound_index].render(self.display)
            options['resolution']['images'][self.res_index].render(self.display)

            marker = Text('>', 16, (255,255,255), (10, 50 + y * 20))
            marker.render(self.display)

            logo = self.assets['player_idle']
            self.display.blit(pygame.transform.scale(logo.img(), (132, 90)), (10, 130))
            logo.update()

            self.musics.update()

            if i < 360:
                self.transition_in(i)
            i += 7

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == self.NEXT:
                    self.musics.mnext()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.transition_out()
                        self.gamestate = Game.MAIN_MENU
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP:
                        y = (y - 1)%2
                        x=0
                    elif event.key == pygame.K_DOWN:
                        y = (y + 1)%2
                        x=0
                    elif event.key == pygame.K_LEFT:
                        if y == 0:
                            self.sound_index = (self.sound_index - 1)%2
                            self.soundon = options['sound']['vals'][self.sound_index]

                        elif y == 1:
                            self.res_index = (self.res_index - 1)%4
                            self.screen = pygame.display.set_mode((options['resolution']['vals'][self.res_index]))

                    elif event.key == pygame.K_RIGHT:
                        if y == 0:
                            self.sound_index = (self.sound_index + 1) % 2
                            self.soundon = options['sound']['vals'][self.sound_index]

                        elif y == 1:
                            self.res_index = (self.res_index + 1) % 4
                            self.screen = pygame.display.set_mode((options['resolution']['vals'][self.res_index]))


            self.clock.tick(60)
            pygame.display.update()
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))


    def game_menu(self):
        i = 0
        if self.level == 0:
            facts = {
                Text('Level '+str(self.level+1), 16, (255, 255, 255), (100, 30)),
                Text('[ESC]', 8, (255, 255, 255), (10, 10)),
                Text('Did you know that', 16, (255, 255, 255), (30, 70)),
                Text('red pandas are', 16, (255, 255, 255), (30,90)),
                Text('not closely', 16, (255, 255, 255), (30, 110)),
                Text('related to giant', 16, (255, 255, 255), (30, 130)),
                Text('pandas?', 16, (255, 255, 255), (30, 150)),
                Text('Press [ENTER] to continue', 8, (255, 255, 255), (70, 200))
            }
        elif self.level == 1:
            facts = {
                Text('Level '+str(self.level+1), 16, (255, 255, 255), (100, 30)),
                Text('[ESC]', 8, (255, 255, 255), (10, 10)),
                Text('Red pandas eat', 16, (255, 255, 255), (30, 70)),
                Text('mushrooms, but', 16, (255, 255, 255), (30,90)),
                Text('they like bamboo', 16, (255, 255, 255), (30, 110)),
                Text('way more.', 16, (255, 255, 255), (30, 130)),
                #Text('pandas?', 16, (255, 255, 255), (30, 150)),
                Text('Press [ENTER] to continue', 8, (255, 255, 255), (70, 200))
            }
        elif self.level == 2:
            facts = {
                Text('Level '+str(self.level+1), 16, (255, 255, 255), (100, 30)),
                Text('[ESC]', 8, (255, 255, 255), (10, 10)),
                Text('Unfortunately,', 16, (255, 255, 255), (30, 70)),
                Text('red pandas are', 16, (255, 255, 255), (30,90)),
                Text('endangered in', 16, (255, 255, 255), (30, 110)),
                Text('India, Bhutan,', 16, (255, 255, 255), (30, 130)),
                Text('China, Nepal,', 16, (255, 255, 255), (30, 150)),
                Text('and Myanmar.', 16, (255, 255, 255), (30, 170)),
                Text('Press [ENTER] to continue', 8, (255, 255, 255), (70, 200))
            }
        elif self.level == 3:
            facts = {
                Text('Level ' + str(self.level + 1), 16, (255, 255, 255), (100, 30)),
                Text('[ESC]', 8, (255, 255, 255), (10, 10)),
                Text('They are endanger', 16, (255, 255, 255), (30, 70)),
                Text('-ed due to habitat', 16, (255, 255, 255), (30, 90)),
                Text('loss and degrada-', 16, (255, 255, 255), (30, 110)),
                Text('tion, human inter-,', 16, (255, 255, 255), (30, 130)),
                Text('ference, and', 16, (255, 255, 255), (30, 150)),
                Text('poaching.', 16, (255, 255, 255), (30, 170)),
                Text('Press [ENTER] to continue', 8, (255, 255, 255), (70, 200))
            }
        elif self.level == 4:
            facts = {
                Text('Level ' + str(self.level + 1), 16, (255, 255, 255), (100, 30)),
                Text('[ESC]', 8, (255, 255, 255), (10, 10)),
                Text('You can help red', 16, (255, 255, 255), (30, 70)),
                Text('pandas by spread', 16, (255, 255, 255), (30, 90)),
                Text('-ing awareness,', 16, (255, 255, 255), (30, 110)),
                Text('donating, and go', 16, (255, 255, 255), (30, 130)),
                Text('-ing against the', 16, (255, 255, 255), (30, 150)),
                Text('red panda trade.', 16, (255, 255, 255), (30, 170)),
                Text('Press [ENTER] to continue', 8, (255, 255, 255), (70, 200))
            }
        elif self.level == 5:
            facts = {
                Text('Level ' + str(self.level + 1), 16, (255, 255, 255), (100, 30)),
                Text('[ESC]', 8, (255, 255, 255), (10, 10)),
                Text('Red pandas are', 16, (255, 255, 255), (30, 70)),
                Text('the cutest ani-', 16, (255, 255, 255), (30, 90)),
                Text('mals, so it\'s', 16, (255, 255, 255), (30, 110)),
                Text('up to us to', 16, (255, 255, 255), (30, 130)),
                Text('protect them!', 16, (255, 255, 255), (30, 150)),
                Text('Press [ENTER] to continue', 8, (255, 255, 255), (70, 200))
            }

        while self.gamestate == Game.GAME_MENU:
            self.display.fill((235, 84, 40))
            for fact in facts:
                fact.render(self.display)

            self.musics.update()

            if i < 360:
                self.transition_in(i)
            i += 7

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == self.NEXT:
                    self.musics.mnext()
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_RETURN,pygame.K_KP_ENTER]:
                        self.gamestate = Game.GAME_RUNNING
                        self.transition_out()
                    if event.key == pygame.K_ESCAPE:
                        self.gamestate = Game.MAIN_MENU
                        self.transition_out()

            self.clock.tick(60)
            pygame.display.update()
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))

    def game_running(self):
        i=0
        self.player.pos=[0,150]
        if self.level in [1,5]:
            self.player.pos = [930,230]
        self.tilemap = Tilemap(self, self.level, tile_size=16)
        while self.gamestate == Game.GAME_RUNNING:

            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0])/10
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1])/10
            if self.scroll[1] > 150:
                self.scroll[1] = 150
            self.render_scroll = (int(self.scroll[0]),int(self.scroll[1]))


            self.background0.update(self.render_scroll)
            self.background0.render(self.display)
            self.background1.update(self.render_scroll)
            self.background1.render(self.display)

            self.tilemap.render(self.display,offset=self.render_scroll)

            self.player.update(self.tilemap,(self.movement[1] - self.movement[0], 0))
            self.player.render(self.display,offset=self.render_scroll)

            if self.level == 0:
                Text('Use arrow keys to move', 8, (235, 84, 40), (-100-self.scroll[0], 100-self.scroll[1])).render(self.display)
                Text('Eat the purple', 8, (235, 84, 40), (200 - self.scroll[0],  - self.scroll[1])).render(
                    self.display)
                Text('mushroom to win', 8, (235, 84, 40),(200 - self.scroll[0], 10- self.scroll[1])).render(self.display)
            elif self.level == 1:
                Text('wall jump practice!', 8, (235, 84, 40), (600 - self.scroll[0], 250 - self.scroll[1])).render(self.display)
                Text('This is the longest', 8, (235, 84, 40), (270 - self.scroll[0], 250 - self.scroll[1])).render(self.display)
                Text('possible wall jump!', 8, (235, 84, 40), (270 - self.scroll[0], 260 - self.scroll[1])).render(self.display)
                Text('Challenge!', 8, (235, 84, 40), (270 - self.scroll[0], 20 - self.scroll[1])).render(self.display)
            elif self.level == 2:
                Text('You can step', 8, (235, 84, 40), (-50 - self.scroll[0], 150 - self.scroll[1])).render(self.display)
                Text('on these leaves', 8, (235, 84, 40), (-50 - self.scroll[0], 160 - self.scroll[1])).render(self.display)
                Text('Wall jump!', 8, (235, 84, 40),(200 - self.scroll[0], 40- self.scroll[1])).render(self.display)
                Text('Challenge!', 8, (235, 84, 40), (270 - self.scroll[0], 200 - self.scroll[1])).render(self.display)
            elif self.level == 3:
                Text('Wall jumps go farther', 8, (235, 84, 40), (200 - self.scroll[0], 40 - self.scroll[1])).render(self.display)
                Text('than regular ones!', 8, (235, 84, 40),(200 - self.scroll[0], 50 - self.scroll[1])).render(self.display)
                Text('no one said it would be easy ;)', 8, (235, 84, 40), (200 - self.scroll[0], 300 - self.scroll[1])).render(self.display)
            Text('[ESC]', 8, (235, 84, 40), (10,10)).render(self.display)

            self.musics.update()

            if i <360:
                self.transition_in(i)
            i+=7

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == self.NEXT:
                    self.musics.mnext()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = True
                    if event.key == pygame.K_UP:
                        self.player.jump()
                    if event.key == pygame.K_ESCAPE:
                        self.gamestate = Game.MAIN_MENU
                        self.transition_out()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = False


            self.screen.blit(pygame.transform.scale(self.display,self.screen.get_size()),(0,0))
            pygame.display.update()
            self.clock.tick(60)

    def run(self):
        while True:
            if self.gamestate == Game.GAME_RUNNING:
                self.game_running()
            if self.gamestate == Game.MAIN_MENU:
                self.main_menu()
            if self.gamestate == Game.LEVEL_SELECT:
                self.level_select()
            if self.gamestate == Game.GAME_MENU:
                self.game_menu()
            if self.gamestate == Game.OPTIONS:
                self.options_menu()


if __name__ == '__main__':
    game = Game()
    game.run()