# Base class for every screen. Game.run owns the frame loop and calls these three methods
# on the current scene. To leave a scene, call self.game.change_scene(GameState.X): the loop
# plays the wipe and builds the next scene, so a scene never has to await anything.
class Scene:
    def __init__(self, game):
        self.game = game

    def handle_events(self, events):
        # this frame's events, minus QUIT and the music event, which Game handles itself
        pass

    def update(self):
        # one 1/60 s logic tick. Called 0 or more times per frame depending on how long the
        # frame took, so anything that advances over time belongs here, not in render
        pass

    def render(self, surf):
        pass
