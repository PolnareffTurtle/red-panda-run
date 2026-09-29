from sys import exit

import pygame

pygame.init()
screen = pygame.display.set_mode((960, 720))
surf = pygame.image.load('data/images/coconut.png').convert_alpha()
medium_surf = pygame.Surface((400, 400), SRCALPHA=True)
testRect = pygame.Rect(50, 50, 1000, 1000)
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
    screen.fill('white')

    medium_surf.blit(surf, (0, 0))
    screen.blit(medium_surf, (300, 200))

    pygame.display.update()
    clock.tick(60)
