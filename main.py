import pygame
import pymunk
import pymunk.pygame_util
import math
import os

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
draw_options = pymunk.pygame_util.DrawOptions(screen)

# Load Assets
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
bird_raw = pygame.image.load(os.path.join(ASSETS_DIR, "bird.png")).convert_alpha()
pig_raw = pygame.image.load(os.path.join(ASSETS_DIR, "pig.png")).convert_alpha()

# Target and Projectile lists to track bodies for rendering
blocks = []
projectiles = []

# Initialize Pymunk Physics Space
space = pymunk.Space()
space.gravity = (0, 900)  # Gravity pulls downward

# Static Floor
floor = pymunk.Segment(space.static_body, (0, 550), (WIDTH, 550), 5)
floor.friction = 0.6
floor.elasticity = 0.3
space.add(floor)

# Target Setup (Stacked Blocks)
BLOCK_SIZE = (40, 40)
pig_image = pygame.transform.smoothscale(pig_raw, BLOCK_SIZE)

def create_targets():
    for row in range(4):
        for col in range(2):
            x = 600 + col * 45
            y = 520 - row * 50
            mass = 1
            moment = pymunk.moment_for_box(mass, BLOCK_SIZE)
            body = pymunk.Body(mass, moment)
            body.position = (x, y)
            shape = pymunk.Poly.create_box(body, BLOCK_SIZE)
            shape.friction = 0.5
            shape.elasticity = 0.2
            space.add(body, shape)
            blocks.append(body)

create_targets()

# Projectile Spawner
PROJECTILE_RADIUS = 15
bird_image = pygame.transform.smoothscale(bird_raw, (PROJECTILE_RADIUS * 2, PROJECTILE_RADIUS * 2))

def launch_projectile(pos, impulse):
    mass = 3
    radius = PROJECTILE_RADIUS
    moment = pymunk.moment_for_circle(mass, 0, radius)
    body = pymunk.Body(mass, moment)
    body.position = pos
    shape = pymunk.Circle(body, radius)
    shape.friction = 0.5
    shape.elasticity = 0.6
    space.add(body, shape)
    body.apply_impulse_at_local_point(impulse)
    projectiles.append(body)

# Game Loop Variables
launch_origin = (150, 450)
dragging = False
running = True

while running:
    mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Start drag if clicked near launch origin
            dist = math.hypot(mouse_pos[0] - launch_origin[0], mouse_pos[1] - launch_origin[1])
            if dist < 40:
                dragging = True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if dragging:
                # Impulse vector points opposite to drag direction
                dx = launch_origin[0] - mouse_pos[0]
                dy = launch_origin[1] - mouse_pos[1]
                power = 15
                launch_projectile(launch_origin, (dx * power, dy * power))
                dragging = False

    # Physics Step
    dt = 1.0 / 60.0
    space.step(dt)

    # Render
    screen.fill((30, 30, 35))

    # Draw Floor
    pygame.draw.line(screen, (100, 100, 100), (0, 550), (WIDTH, 550), 5)

    # Draw Blocks (Pigs)
    for body in blocks:
        angle_deg = -math.degrees(body.angle)
        rotated_pig = pygame.transform.rotate(pig_image, angle_deg)
        rect = rotated_pig.get_rect(center=(round(body.position.x), round(body.position.y)))
        screen.blit(rotated_pig, rect)

    # Draw Projectiles (Birds)
    for body in projectiles:
        angle_deg = -math.degrees(body.angle)
        rotated_bird = pygame.transform.rotate(bird_image, angle_deg)
        rect = rotated_bird.get_rect(center=(round(body.position.x), round(body.position.y)))
        screen.blit(rotated_bird, rect)

    # Draw Aiming Line / Slingshot
    if dragging:
        pygame.draw.line(screen, (255, 80, 80), launch_origin, mouse_pos, 3)
        pygame.draw.circle(screen, (255, 200, 0), launch_origin, 8)
        bird_rect = bird_image.get_rect(center=mouse_pos)
        screen.blit(bird_image, bird_rect)
    else:
        bird_rect = bird_image.get_rect(center=launch_origin)
        screen.blit(bird_image, bird_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()