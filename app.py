import math
import os
import random
import pyxel

WIDTH = 256
HEIGHT = 192
FLOOR_Y = 162
LAUNCH_X = 48
LAUNCH_Y = 132
MAX_PULL = 32
GRAVITY = 0.28


def get_asset_path(filename):
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    return os.path.join(assets_dir, filename)


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.0, 3.5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 1.0
        self.life = random.randint(12, 22)
        self.max_life = self.life
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15
        self.life -= 1

    def draw(self):
        if self.life > 0:
            pyxel.pset(int(self.x), int(self.y), self.color)


class Pig:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.alive = True
        self.size = 16

    def update(self):
        if not self.alive:
            return
        if abs(self.vx) > 0.05 or abs(self.vy) > 0.05:
            self.x += self.vx
            self.y += self.vy
            self.vy += GRAVITY
            self.vx *= 0.92

            # Floor collision
            if self.y + self.size > FLOOR_Y:
                self.y = FLOOR_Y - self.size
                self.vy = -self.vy * 0.4
                self.vx *= 0.85
                if abs(self.vy) < 0.3:
                    self.vy = 0.0


class Bird:
    def __init__(self, x, y, vx, vy):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.active = True
        self.radius = 7
        self.stopped_frames = 0

    def update(self):
        if not self.active:
            return

        self.x += self.vx
        self.y += self.vy
        self.vy += GRAVITY
        self.vx *= 0.99

        # Floor collision
        if self.y + self.radius > FLOOR_Y:
            self.y = FLOOR_Y - self.radius
            self.vy = -self.vy * 0.45
            self.vx *= 0.82
            if abs(self.vy) < 0.4 and abs(self.vx) < 0.2:
                self.stopped_frames += 1
                if self.stopped_frames > 45:
                    self.active = False

        # Out of bounds
        if self.x > WIDTH + 30 or self.x < -30 or self.y > HEIGHT + 20:
            self.active = False


class App:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title="Pig Sling Pyxel", fps=30)

        # Load sprites into Image Bank 0
        bird_sprite = get_asset_path("bird_16.png")
        pig_sprite = get_asset_path("pig_16.png")

        if os.path.exists(bird_sprite):
            pyxel.images[0].load(0, 0, bird_sprite)
        if os.path.exists(pig_sprite):
            pyxel.images[0].load(16, 0, pig_sprite)

        # Sound effects
        # Sound 0: Launch
        pyxel.sounds[0].set("g2b2d3g3", "s", "6543", "s", 3)
        # Sound 1: Hit / Impact
        pyxel.sounds[1].set("c3c2g1c1", "n", "7642", "f", 4)
        # Sound 2: Pig defeated
        pyxel.sounds[2].set("e3g3c4", "t", "776", "v", 5)
        # Sound 3: Level clear fanfare
        pyxel.sounds[3].set("c3e3g3c4e4g4", "t", "666777", "n", 6)
        # Sound 4: Background music pattern
        pyxel.sounds[4].set(
            "c3e3g3e3 d3f3a3f3 e3g3b3g3 c3e3g3e3",
            "p",
            "2222 2222 2222 2222",
            "s",
            10,
        )
        pyxel.musics[0].set([4])
        pyxel.playm(0, loop=True)

        self.reset_game()
        pyxel.run(self.update, self.draw)

    def reset_game(self):
        self.birds = []
        self.particles = []
        self.pigs = []
        self.score = 0
        self.birds_used = 0
        self.is_dragging = False
        self.drag_x = LAUNCH_X
        self.drag_y = LAUNCH_Y
        self.cleared = False
        self.cleared_sound_played = False

        # Build 2-column x 4-row pig stack
        for row in range(4):
            for col in range(2):
                x = 180 + col * 26
                y = FLOOR_Y - (row + 1) * 20
                self.pigs.append(Pig(x, y))

    def update(self):
        # Restart key
        if pyxel.btnp(pyxel.KEY_R):
            self.reset_game()
            return

        # Toggle music with M
        if pyxel.btnp(pyxel.KEY_M):
            if pyxel.play_pos(0) is not None:
                pyxel.stop(0)
            else:
                pyxel.playm(0, loop=True)

        # Handle mouse / touch dragging
        mx = pyxel.mouse_x
        my = pyxel.mouse_y

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            dist = math.hypot(mx - LAUNCH_X, my - LAUNCH_Y)
            if dist < 25:
                self.is_dragging = True

        if self.is_dragging:
            if pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
                dx = mx - LAUNCH_X
                dy = my - LAUNCH_Y
                dist = math.hypot(dx, dy)
                if dist > MAX_PULL:
                    angle = math.atan2(dy, dx)
                    self.drag_x = LAUNCH_X + math.cos(angle) * MAX_PULL
                    self.drag_y = LAUNCH_Y + math.sin(angle) * MAX_PULL
                else:
                    self.drag_x = mx
                    self.drag_y = my
            else:
                # Release and launch
                dx = LAUNCH_X - self.drag_x
                dy = LAUNCH_Y - self.drag_y
                speed_mult = 0.32
                if math.hypot(dx, dy) > 5:
                    vx = dx * speed_mult
                    vy = dy * speed_mult
                    self.birds.append(Bird(self.drag_x, self.drag_y, vx, vy))
                    self.birds_used += 1
                    pyxel.play(1, 0)
                self.is_dragging = False
                self.drag_x = LAUNCH_X
                self.drag_y = LAUNCH_Y

        # Update birds
        for bird in self.birds:
            if bird.active:
                bird.update()
                # Check collision with pigs
                for pig in self.pigs:
                    if pig.alive:
                        # Circle vs AABB collision
                        cx = bird.x
                        cy = bird.y
                        r = bird.radius
                        closest_x = max(pig.x, min(cx, pig.x + pig.size))
                        closest_y = max(pig.y, min(cy, pig.y + pig.size))
                        dist = math.hypot(cx - closest_x, cy - closest_y)
                        if dist < r:
                            # Hit!
                            pig.alive = False
                            self.score += 100
                            pyxel.play(2, 1)

                            # Spawn explosion particles
                            for _ in range(16):
                                color = random.choice([8, 9, 10, 11, 7])
                                self.particles.append(
                                    Particle(pig.x + 8, pig.y + 8, color)
                                )

                            # Deflect bird slightly
                            bird.vx *= 0.6
                            bird.vy *= 0.6

        # Update pigs
        for pig in self.pigs:
            pig.update()

        # Update particles
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles:
            p.update()

        # Check win condition
        remaining_pigs = sum(1 for p in self.pigs if p.alive)
        if remaining_pigs == 0 and not self.cleared:
            self.cleared = True
            if not self.cleared_sound_played:
                pyxel.play(1, 3)
                self.cleared_sound_played = True

    def draw(self):
        # Sky background
        pyxel.cls(12)

        # Clouds
        pyxel.circ(40, 30, 14, 7)
        pyxel.circ(55, 26, 18, 7)
        pyxel.circ(70, 30, 14, 7)

        pyxel.circ(170, 45, 12, 7)
        pyxel.circ(185, 40, 16, 7)
        pyxel.circ(200, 45, 12, 7)

        # Mountains in background
        pyxel.tri(90, FLOOR_Y, 130, 95, 170, FLOOR_Y, 13)
        pyxel.tri(140, FLOOR_Y, 180, 105, 220, FLOOR_Y, 13)

        # Ground / Floor
        pyxel.rect(0, FLOOR_Y, WIDTH, HEIGHT - FLOOR_Y, 11)
        pyxel.rect(0, FLOOR_Y, WIDTH, 3, 3)

        # Slingshot base
        pyxel.rect(LAUNCH_X - 2, LAUNCH_Y, 4, FLOOR_Y - LAUNCH_Y, 4)
        pyxel.line(LAUNCH_X - 6, LAUNCH_Y - 8, LAUNCH_X, LAUNCH_Y, 9)
        pyxel.line(LAUNCH_X + 6, LAUNCH_Y - 8, LAUNCH_X, LAUNCH_Y, 9)

        # Trajectory dots when dragging
        if self.is_dragging:
            dx = LAUNCH_X - self.drag_x
            dy = LAUNCH_Y - self.drag_y
            sim_x = self.drag_x
            sim_y = self.drag_y
            sim_vx = dx * 0.32
            sim_vy = dy * 0.32
            for i in range(12):
                sim_x += sim_vx
                sim_y += sim_vy
                sim_vy += GRAVITY
                if sim_y >= FLOOR_Y:
                    break
                if i % 2 == 0:
                    pyxel.pset(int(sim_x), int(sim_y), 7)

            # Slingshot bands
            pyxel.line(LAUNCH_X - 5, LAUNCH_Y - 8, self.drag_x, self.drag_y, 8)
            pyxel.line(LAUNCH_X + 5, LAUNCH_Y - 8, self.drag_x, self.drag_y, 8)
            # Bird on slingshot
            pyxel.blt(
                int(self.drag_x - 8),
                int(self.drag_y - 8),
                0,
                0,
                0,
                16,
                16,
                pyxel.COLOR_BLACK,
            )
        else:
            # Bird waiting on slingshot
            pyxel.blt(
                LAUNCH_X - 8,
                LAUNCH_Y - 14,
                0,
                0,
                0,
                16,
                16,
                pyxel.COLOR_BLACK,
            )

        # Draw active projectiles
        for bird in self.birds:
            if bird.active:
                pyxel.blt(
                    int(bird.x - 8),
                    int(bird.y - 8),
                    0,
                    0,
                    0,
                    16,
                    16,
                    pyxel.COLOR_BLACK,
                )

        # Draw pigs
        for pig in self.pigs:
            if pig.alive:
                pyxel.blt(
                    int(pig.x),
                    int(pig.y),
                    0,
                    16,
                    0,
                    16,
                    16,
                    pyxel.COLOR_BLACK,
                )

        # Draw particles
        for p in self.particles:
            p.draw()

        # UI Overlay
        pyxel.rect(0, 0, WIDTH, 14, 0)
        remaining = sum(1 for p in self.pigs if p.alive)
        pyxel.text(6, 4, f"SCORE: {self.score}", 7)
        pyxel.text(90, 4, f"PIGS LEFT: {remaining}", 11)
        pyxel.text(175, 4, f"SHOTS: {self.birds_used}", 10)
        pyxel.text(225, 4, "[R]ESET", 9)

        if self.cleared:
            pyxel.rect(48, 70, 160, 40, 0)
            pyxel.rectb(48, 70, 160, 40, 10)
            pyxel.text(80, 80, "ALL PIGS CLEARED!", 10)
            pyxel.text(72, 94, "Press [R] to Play Again", 7)


def main():
    App()


if __name__ == "__main__":
    main()