from scene import Scene
import pygame
from scripts.utils import Text
from random import randint
from scripts.gamestate import GameState

class MainMenuScene(Scene):
    def __init__(self,game):
        super().__init__(game)
        self.texts = {
            Text('Red Panda Run', 16, (146, 52, 22), (29, 21)),
            Text('Continue', 16, (146, 52, 22), (30, 50)),
            Text('Level Select', 16, (146, 52, 22), (30, 70)),
            Text('Options', 16, (146, 52, 22), (30, 90)),
            Text('Use Arrow\nKeys and\nPress [ENTER]\nto select', 8, (235, 84, 40), (80, 170)),
        }
        self.texts2 = {
            Text('Red Panda Run', 16, (235, 84, 40), (30, 20))
        }
        self.option_index=0
        self.r1=randint(-100,-50)
        self.r2=randint(-100,0)

        self.bg_rect = pygame.Surface((200, 20))
        self.bg_rect.set_alpha(150)
        self.bg_rect.fill((255, 255, 255))

        self.logo = self.game.assets['player_idle']

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_RETURN,pygame.K_KP_ENTER]:
                    self.gamestate = [GameState.GAME_MENU, GameState.LEVEL_SELECT, GameState.OPTIONS][self.option_index]
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_UP:
                    self.option_index = (self.option_index - 1) % 3
                elif event.key == pygame.K_DOWN:
                    self.option_index = (self.option_index + 1) % 3
                
    def render(self, screen):
        screen.blit(self.game.assets['backgrounds'][0],(self.r1,0))
        screen.blit(self.game.assets['backgrounds'][1],(self.r2,0))
        screen.blit(self.bg_rect,(28,49+self.option_index*20))

        for text in self.texts:
            text.render(screen)
        for text in self.texts2:
            text.render(screen)

        marker = Text('>',16,(235, 84, 40),(10,48+20*self.option_index))
        marker.render(screen)
        option_marker = Text(['Continue','Level Select','Options'][self.option_index], 16, (235, 84, 40), (31, 49+20*self.option_index))
        option_marker.render(screen)

        screen.blit(pygame.transform.scale(self.logo.img(flip=True),(132,90)),(180,150))
        

    def update(self,dt):
        self.logo.update()
