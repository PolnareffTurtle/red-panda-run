from random import randint

import pygame


class WindParticle:
    def __init__(self, animation, direction, pos, speed):
        self.animation = animation.copy()
        self.animation.frame = randint(0, len(self.animation.images) - 1)
        self.animation.img_duration = 2 / speed
        self.pos = pos
        self.direction = direction

        # TODO: Create subsurface right after getting random coords from WindZone: cut off anywhere that
        # the surface would end up leaving the rectangle.
        # You will probably have to implement this during the img() part since it's an animation.

    def update(self):
        self.animation.update()
        if self.animation.done:
            return True

    def render(self, surf, offset):
        surf.blit(
            self.animation.img(direction=self.direction),
            (self.pos[0] - offset[0], self.pos[1] - offset[1]),
        )


class WindZone:
    def __init__(self, pos: tuple[int, int], size: tuple[int, int], x_push, y_push, animation):
        self.rect = pygame.rect.Rect(pos[0], pos[1], size[0], size[1])
        self.x_push = x_push
        self.y_push = y_push
        self.speed = max(abs(self.x_push), abs(self.y_push))
        self.animation = animation

        # 0 moves to the left, 90 moves down, 180 moves right, 270 (-90) moves up
        # exactly ONE of x_push, y_push MUST BE 0
        if self.x_push > 0:
            self.direction = 180
        elif self.x_push < 0:
            self.direction = 0
        elif self.y_push > 0:
            self.direction = 90
        elif self.y_push < 0:
            self.direction = -90
        self.particles = []

        # initial amount of particles is proportional to WindZone area
        area = self.rect.width * self.rect.height
        total = area / 1000
        for _ in range(int(total)):
            self.spawn_particle()

    def spawn_particle(self):
        width, height = self.animation.img(direction=self.direction).get_size()
        pos = (
            randint(self.rect.left, self.rect.right - width),
            randint(self.rect.top, self.rect.bottom - height),
        )
        self.particles.append(WindParticle(self.animation, self.direction, pos, self.speed))

    def update_particles(self):
        # add new particles as soon as old ones die
        new_particles_count = 0
        for particle in self.particles.copy():
            if particle.update():
                self.particles.remove(particle)
                new_particles_count += 1
        for _ in range(new_particles_count):
            self.spawn_particle()

    def render_particles(self, surf, offset):
        for particle in self.particles:
            particle.render(surf, offset)
