import pygame
import pymunk
import pymunk.pygame_util
import math

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
draw_options = pymunk.pygame_util.DrawOptions(screen)

# Initialize Pymunk Physics Space
space = pymunk.Space()
space.gravity = (0, 900)  # Gravity pulls downward

# Static Floor
floor = pymunk.Segment(space.static_body, (0, 550), (WIDTH, 550), 5)
floor.friction = 0.6
floor.elasticity = 0.3
space.add(floor)

# Target Setup (Stacked Blocks)
def create_targets():
    for row in range(4):
        for col in range(2):
            x = 600 + col * 45
            y = 520 - row * 50
            mass = 1
            moment = pymunk.moment_for_box(mass, (40, 40))
            body = pymunk.Body(mass, moment)
            body.position = (x, y)
            shape = pymunk.Poly.create_box(body, (40, 40))
            shape.friction = 0.5
            shape.elasticity = 0.2
            space.add(body, shape)

create_targets()

# Projectile Spawner
def launch_projectile(pos, impulse):
    mass = 3
    radius = 15
    moment = pymunk.moment_for_circle(mass, 0, radius)
    body = pymunk.Body(mass, moment)
    body.position = pos
    shape = pymunk.Circle(body, radius)
    shape.friction = 0.5
    shape.elasticity = 0.6
    space.add(body, shape)
    body.apply_impulse_at_local_point(impulse)

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
    space.debug_draw(draw_options)

    # Draw Aiming Line
    if dragging:
        pygame.draw.line(screen, (255, 80, 80), launch_origin, mouse_pos, 3)
        pygame.draw.circle(screen, (255, 200, 0), launch_origin, 8)
    else:
        pygame.draw.circle(screen, (100, 200, 255), launch_origin, 15)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()