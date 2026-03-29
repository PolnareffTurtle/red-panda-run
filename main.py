import pygame
from sys import exit
from random import randint
import math
from scripts.entities import PhysicsEntity, Player
from scripts.utils import load_image, load_images, Animation, Text, Music,Backgrounds
from scripts.tilemap import Tilemaps
import asyncio
from scripts.gamestate import GameState

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((960,720),flags=pygame.SCALED,vsync=1)
        pygame.display.set_caption('Red Panda Run')
        self.display = pygame.Surface((320,240))
        self.clock = pygame.time.Clock()
        self.movement = [False,False]

        self.scroll = [0,0]
        self.gamestate = GameState.MAIN_MENU
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
            'player_wall_slide': Animation(load_images('player/wall_slide'),img_dur=5),
            'wind_anim': Animation(load_images('wind_anim',alpha=True,scale=2),img_dur=1,loop=False)
        }

        self.player = Player(self,(0,0),(22,10))

    def fps_counter(self):
        fps = str(int(self.clock.get_fps()))
        fps_t = Text(fps,16,"white",(30,30))
        fps_t.render(self.display)

    def transition_in(self,i):
        pygame.draw.rect(self.display, (0, 0, 0), pygame.rect.Rect(i, 0, self.display.get_width(), self.display.get_height()))

    async def transition_out(self):
        i=0
        while True:
            if i>360:
                break
            i+=36
            pygame.draw.rect(self.display,(0,0,0),pygame.rect.Rect(0,0,i,self.display.get_height()))

            self.clock.tick(60)
            pygame.display.update()
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))

            await asyncio.sleep(0)

    async def win(self):
        Text(':)',24,(0, 0, 0),(self.player.pos[0]-self.render_scroll[0],self.player.pos[1]-20-self.render_scroll[1])).render(self.display)
        await self.transition_out()
        if self.level == 5:
            self.gamestate = GameState.MAIN_MENU
        else:
            self.level += 1
            self.gamestate = GameState.GAME_MENU

    async def lose(self):
        self.movement[0] = False
        self.movement[1] = False
        Text('😟', 24, (235, 84, 40), (self.player.pos[0]-self.render_scroll[0], self.player.pos[1] - 20 - self.render_scroll[1])).render(self.display)
        await self.transition_out()
        self.gamestate = GameState.GAME_RUNNING

    async def main_menu(self):
        #self.transition_in()
        texts = {
            Text('Red Panda Run', 16, (146, 52, 22), (29, 21)),
            Text('Continue', 16, (146, 52, 22), (30, 50)),
            Text('Level Select', 16, (146, 52, 22), (30, 70)),
            Text('Options', 16, (146, 52, 22), (30, 90)),
            Text('Use Arrow\nKeys and\nPress [ENTER]\nto select', 8, (235, 84, 40), (80, 170)),
        }
        texts2 = {
            Text('Red Panda Run', 16, (235, 84, 40), (30, 20))
        }
        option_index=0
        r1=randint(-100,-50)
        r2=randint(-100,0)

        bg_rect = pygame.Surface((200, 20))
        bg_rect.set_alpha(150)
        bg_rect.fill((255, 255, 255))

        i=0
        while self.gamestate == GameState.MAIN_MENU:


            self.display.blit(self.assets['backgrounds'][0],(r1,0))
            self.display.blit(self.assets['backgrounds'][1],(r2,0))
            self.display.blit(bg_rect,(28,49+option_index*20))

            for text in texts:
                text.render(self.display)
            for text in texts2:
                text.render(self.display)

            marker = Text('>',16,(235, 84, 40),(10,48+20*option_index))
            marker.render(self.display)
            option_marker = Text(['Continue','Level Select','Options'][option_index], 16, (235, 84, 40), (31, 49+20*option_index))
            option_marker.render(self.display)

            logo = self.assets['player_idle']
            self.display.blit(pygame.transform.scale(logo.img(flip=True),(132,90)),(180,150))
            logo.update()

            self.musics.update()

            if i <=360:
                self.transition_in(i)
            i+=36

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == self.NEXT:
                    self.musics.mnext()
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_RETURN,pygame.K_KP_ENTER]:
                        await self.transition_out()
                        self.gamestate = [GameState.GAME_MENU, GameState.LEVEL_SELECT, GameState.OPTIONS][option_index]
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP:
                        option_index = (option_index - 1) % 3
                    elif event.key == pygame.K_DOWN:
                        option_index = (option_index + 1) % 3

            self.clock.tick(60)
            pygame.display.update()
            self.screen.blit(pygame.transform.scale(self.display,self.screen.get_size()),(0,0))

            await asyncio.sleep(0)
    async def level_select(self):
        texts = [
            Text('Levels', 16, (146, 52, 22), (119, 21)),
            Text('Levels', 16, (235, 84, 40), (120, 20)),
            Text('Press [ENTER]', 8, (235, 84, 40), (140, 200)),
            Text('to select', 8, (235, 84, 40), (140, 210)),
            Text('[ESC]', 8, (235, 84, 40), (10,10))
        ]
        level_texts = [
            Text(str(i+1),
                 16,(146, 52, 22),
                 (50+(i%5)*50, 60+(i//5)*30))
            for i in range(20)
        ]

        option_index = 0
        r1 = randint(-100, -50)
        r2 = randint(-100, 0)
        i=0

        #bg rect
        bg_rect = pygame.Surface((265, 130))
        bg_rect.set_alpha(150)
        bg_rect.fill((255, 255, 255))
        while self.gamestate == GameState.LEVEL_SELECT:

            self.display.blit(self.assets['backgrounds'][0], (r1, 0))
            self.display.blit(self.assets['backgrounds'][1], (r2, 0))

            self.display.blit(bg_rect,(30,50))

            for text in texts:
                text.render(self.display)
            for text in level_texts:
                text.render(self.display)

            logo = self.assets['player_idle']
            self.display.blit(pygame.transform.scale(logo.img(), (132, 90)), (10, 150))
            logo.update()

            marker = Text('>', 16, (235, 84, 40), (37+50*(option_index%5), 58 + 30 * (option_index//5)))
            level_marker = Text(str(option_index+1),16,(235, 84, 40),(51+(option_index%5)*50, 59+(option_index//5)*30))
            marker.render(self.display)
            level_marker.render(self.display)

            self.musics.update()

            if i <=360:
                self.transition_in(i)
            i+=36

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == self.NEXT:
                    self.musics.mnext()
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_RETURN,pygame.K_KP_ENTER]:
                        self.level=option_index
                        self.gamestate = GameState.GAME_MENU
                        await self.transition_out()
                    if event.key == pygame.K_ESCAPE:
                        self.gamestate = GameState.MAIN_MENU
                        await self.transition_out()

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP:
                        option_index = min((option_index - 5) % 20,option_index)
                    elif event.key == pygame.K_DOWN:
                        option_index = max((option_index + 5) % 20,option_index)
                    elif event.key == pygame.K_LEFT:
                        option_index = min((option_index - 1) % 20,option_index)
                    elif event.key == pygame.K_RIGHT:
                        option_index = max((option_index + 1) % 20,option_index)

            self.clock.tick(60)
            pygame.display.update()
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))

            await asyncio.sleep(0)

    async def options_menu(self):
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



        while self.gamestate == GameState.OPTIONS:
            self.display.fill((235, 84, 40))

            for text in texts:
                text.render(self.display)
            options['sound']['images'][self.sound_index].render(self.display)
            options['resolution']['images'][self.res_index].render(self.display)

            marker = Text('>', 16, (255,255,255), (10, 50 + y * 20))
            marker.render(self.display)

            logo = self.assets['player_idle']
            self.display.blit(pygame.transform.scale(logo.img(), (132, 90)), (10, 150))
            logo.update()

            self.musics.update()

            if i <= 360:
                self.transition_in(i)
            i += 36

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == self.NEXT:
                    self.musics.mnext()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        await self.transition_out()
                        self.gamestate = GameState.MAIN_MENU
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

            await asyncio.sleep(0)

    async def game_menu(self):
        i = 0
        facts = [
            'Did you know that\nred pandas\naren\'t closely\nrelated to giant\npandas?',
            'Red pandas love\nbamboo!',
            'Unfortunately,\nred pandas are\nendangered in\nseveral asian\ncountries.',
            'They are endanger\n-ed due to habitat\nloss and degrada-\ntion, human inter-\nference, and\npoaching.',
            'You can help red\npandas by spread\n-ing awareness,\ndonating, and go\n-ing against the\nred panda trade.',
            'Red pandas are\nthe cutests ani-\nmals, so it\'s\nup to us to\nprotect them!',
            'among us in\nreal life',
            'among us in\nreal life',
            'among us in\nreal life',
            'among us in\nreal life',
            'among us in\nreal life',
            'among us in\nreal life',
            'among us in\nreal life',
            'among us in\nreal life',
            'among us in\nreal life',
            'among us in\nreal life',
            'among us in\nreal life',
        ]
        while self.gamestate == GameState.GAME_MENU:
            self.display.fill((235, 84, 40))
            for text in [
                Text(facts[self.level], 16, (255, 255, 255), (30, 70)),
                Text('Level ' + str(self.level + 1), 16, (255, 255, 255), (100, 30)),
                Text('[ESC]', 8, (255, 255, 255), (10, 10)),
                Text('Press [ENTER] to continue', 8, (255, 255, 255), (70, 200))
            ]:
                text.render(self.display)
            self.musics.update()

            if i <= 360:
                self.transition_in(i)
            i += 36

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == self.NEXT:
                    self.musics.mnext()
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_RETURN,pygame.K_KP_ENTER]:
                        self.gamestate = GameState.GAME_RUNNING
                        await self.transition_out()
                    if event.key == pygame.K_ESCAPE:
                        self.gamestate = GameState.LEVEL_SELECT
                        await self.transition_out()

            self.clock.tick(60)
            pygame.display.update()
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))

            await asyncio.sleep(0)

    async def game_running(self):

        i=0
        start_time = pygame.time.get_ticks()
        self.background0 = Backgrounds(0.1, self.assets['backgrounds'][0], 0,(0, 0))
        self.background1 = Backgrounds(0.2, self.assets['backgrounds'][1], 1, (0, 0))

        self.player.pos=[0,100]

        self.tilemaps = Tilemaps(self, self.level, tile_size=16)
        self.scroll = [self.player.rect().centerx - self.display.get_width() / 2, self.player.rect().centery - self.display.get_height() / 2]


        self.movement[0] = False
        self.movement[1] = False

        while self.gamestate == GameState.GAME_RUNNING:
            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0])/10
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1])/10
            #if self.scroll[1] > 150 and self.level != 2:
            #    self.scroll[1] = 150
            if self.scroll[1] > 16 * (self.tilemaps.height - 10):
                self.scroll[1] = 16 * (self.tilemaps.height - 10)
            self.render_scroll = (int(self.scroll[0]),int(self.scroll[1]))


            for background in [self.background0,self.background1]:
                background.update(self.render_scroll)
                background.render(self.display)

            self.tilemaps.update()
            self.tilemaps.render1(self.display,offset=self.render_scroll)

            self.player.update(self.tilemaps,(self.movement[1] - self.movement[0], 0))
            self.player.render(self.display,offset=self.render_scroll)
            self.tilemaps.render2(self.display,offset=self.render_scroll)

            Text('[ESC]', 8, (235, 84, 40), (10,10)).render(self.display)
            Text(str(((pygame.time.get_ticks()-start_time)//10)/100),8,(235, 84, 40), (270,10)).render(self.display)
            self.musics.update()

            if i <=360:
                self.transition_in(i)
            i+=36
            #self.fps_counter()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == self.NEXT:
                    self.musics.mnext()
                if event.type == pygame.KEYDOWN:
                    if event.key in {pygame.K_LEFT,pygame.K_a}:
                        self.movement[0] = True
                    if event.key in {pygame.K_RIGHT,pygame.K_d}:
                        self.movement[1] = True
                    if event.key in {pygame.K_UP,pygame.K_w}:
                        self.player.jump()
                    if event.key == pygame.K_ESCAPE:
                        self.gamestate = GameState.MAIN_MENU
                        await self.transition_out()
                elif event.type == pygame.KEYUP:
                    if event.key in {pygame.K_LEFT,pygame.K_a}:
                        self.movement[0] = False
                    if event.key in {pygame.K_RIGHT,pygame.K_d}:
                        self.movement[1] = False

            if self.gamestate == GameState.GAME_RUNNING:
                self.clock.tick(60)
                self.screen.blit(pygame.transform.scale(self.display,self.screen.get_size()),(0,0))
                pygame.display.update()


                await asyncio.sleep(0)

            elif self.gamestate == GameState.LOSE:
                await self.lose()
                break
            elif self.gamestate == GameState.WIN:
                await self.win()


    async def run(self):
        while True:
            if self.gamestate == GameState.GAME_RUNNING:
                await self.game_running()
            if self.gamestate == GameState.MAIN_MENU:
                await self.main_menu()
            if self.gamestate == GameState.LEVEL_SELECT:
                await self.level_select()
            if self.gamestate == GameState.GAME_MENU:
                await self.game_menu()
            if self.gamestate == GameState.OPTIONS:
                await self.options_menu()


if __name__ == '__main__':
    game = Game()
    asyncio.run(game.run())
