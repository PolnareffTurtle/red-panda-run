from scene import Scene
from src.utils import Text
from random import randint
import pygame
from src.gamestate import GameState

class LevelSelectScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.texts = [
            Text('Levels', 16, (146, 52, 22), (119, 21)),
            Text('Levels', 16, (235, 84, 40), (120, 20)),
            Text('Press [ENTER]', 8, (235, 84, 40), (140, 200)),
            Text('to select', 8, (235, 84, 40), (140, 210)),
            Text('[ESC]', 8, (235, 84, 40), (10,10))
        ]
        self.level_texts = [
            Text(str(i+1),
                 16,(146, 52, 22),
                 (50+(i%5)*50, 60+(i//5)*30))
            for i in range(20)
        ]

        self.option_index = 0
        self.r1 = randint(-100, -50)
        self.r2 = randint(-100, 0)

        bg_rect = pygame.Surface((265, 130))
        bg_rect.set_alpha(150)
        bg_rect.fill((255, 255, 255))

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_RETURN,pygame.K_KP_ENTER]:
                    self.game.level=self.option_index
                    self.game.gamestate = GameState.GAME_MENU
                if event.key == pygame.K_ESCAPE:
                    self.game.gamestate = GameState.MAIN_MENU

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_UP:
                    self.option_index = min((self.option_index - 5) % 20,self.option_index)
                elif event.key == pygame.K_DOWN:
                    self.option_index = max((self.option_index + 5) % 20,self.option_index)
                elif event.key == pygame.K_LEFT:
                    self.option_index = min((self.option_index - 1) % 20,self.option_index)
                elif event.key == pygame.K_RIGHT:
                    self.option_index = max((self.option_index + 1) % 20,self.option_index)
    
    def render(self, screen):
        screen.blit(self.game.assets['backgrounds'][0], (self.r1, 0))
        screen.blit(self.game.assets['backgrounds'][1], (self.r2, 0))

        screen.blit(self.bg_rect,(30,50))

        for text in self.texts:
            text.render(screen)
        for text in self.level_texts:
            text.render(screen)

        logo = self.game.assets['player_idle']
        screen.blit(pygame.transform.scale(logo.img(), (132, 90)), (10, 150))
        logo.update()

        marker = Text('>', 16, (235, 84, 40), (37+50*(self.option_index%5), 58 + 30 * (self.option_index//5)))
        level_marker = Text(str(self.option_index+1),16,(235, 84, 40),(51+(self.option_index%5)*50, 59+(self.option_index//5)*30))
        marker.render(screen)
        level_marker.render(screen)

    def update(self, dt):
        self.logo.update()
