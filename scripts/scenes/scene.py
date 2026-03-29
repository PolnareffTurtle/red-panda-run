import pygame

# Abstract class for all scenes
class Scene:

    def __init__(self, game):
        self.game = game

    def handle_events(self, events):
        # for event in events...
        pass

    def update(self, dt):
        pass

    def render(self, screen):
        pass
