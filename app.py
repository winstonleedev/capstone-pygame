import asyncio
import math
import os

import pygame
import pymunk

WIDTH, HEIGHT = 800, 600
FLOOR_Y = 550
BLOCK_SIZE = (40, 40)
BLOCK_COLLISION_TYPE = 1
PROJECTILE_COLLISION_TYPE = 2
LAUNCH_ORIGIN = (150, 450)


def get_asset_path(filename):
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    path = os.path.join(assets_dir, filename)
    if not os.path.exists(path):
        name, ext = os.path.splitext(filename)
        for alt_name in (f"{name}-pygbag.ogg", f"{name}.ogg"):
            alt_path = os.path.join(assets_dir, alt_name)
            if os.path.exists(alt_path):
                return alt_path
    return path


def load_assets():
    bird_raw = pygame.image.load(get_asset_path("bird.png")).convert_alpha()
    pig_raw = pygame.image.load(get_asset_path("pig.png")).convert_alpha()
    pig_image = pygame.transform.smoothscale(pig_raw, BLOCK_SIZE)
    bird_image = pygame.transform.smoothscale(bird_raw, (30, 30))

    flying_sound = None
    hit_sound = None
    try:
        flying_path = get_asset_path("flying.mp3")
        if os.path.exists(flying_path):
            flying_sound = pygame.mixer.Sound(flying_path)
    except Exception as e:
        print(f"Warning: could not load flying sound: {e}")

    try:
        hit_path = get_asset_path("hit.mp3")
        if os.path.exists(hit_path):
            hit_sound = pygame.mixer.Sound(hit_path)
    except Exception as e:
        print(f"Warning: could not load hit sound: {e}")

    return {
        "bird_image": bird_image,
        "pig_image": pig_image,
        "flying_sound": flying_sound,
        "hit_sound": hit_sound,
        "music_path": get_asset_path("music.mp3"),
    }


def get_pointer_position(event):
    if hasattr(event, "pos"):
        return event.pos
    if hasattr(event, "x") and hasattr(event, "y"):
        return (event.x, event.y)
    return None


def remove_body_and_shape(space, body):
    for shape in list(space.shapes):
        if getattr(shape, "body", None) is body:
            space.remove(shape)
    space.remove(body)


def launch_projectile(space, projectiles, pos, impulse, projectile_collision_type, flying_sound):
    body = pymunk.Body(3, pymunk.moment_for_circle(3, 0, 15))
    body.position = pos
    shape = pymunk.Circle(body, 15)
    shape.friction, shape.elasticity = 0.5, 0.6
    shape.collision_type = projectile_collision_type
    space.add(body, shape)
    body.apply_impulse_at_local_point(impulse)
    projectiles.append(body)
    if flying_sound is not None:
        flying_sound.play()


def handle_projectile_hit(arbiter, space, data):
    projectile_shape, block_shape = arbiter.shapes
    if projectile_shape.collision_type == PROJECTILE_COLLISION_TYPE:
        projectile_body = projectile_shape.body
        block_body = block_shape.body
    else:
        projectile_body = block_shape.body
        block_body = projectile_shape.body

    if projectile_body in data["projectiles"]:
        data["projectiles"].remove(projectile_body)
    if block_body in data["blocks"]:
        data["blocks"].remove(block_body)

    remove_body_and_shape(space, projectile_body)
    remove_body_and_shape(space, block_body)
    if data["hit_sound"] is not None:
        data["hit_sound"].play()
    return False


def build_world(space):
    floor = pymunk.Segment(space.static_body, (0, FLOOR_Y), (WIDTH, FLOOR_Y), 5)
    floor.friction, floor.elasticity = 0.6, 0.3
    space.add(floor)

    blocks = []
    for row in range(4):
        for col in range(2):
            body = pymunk.Body(1, pymunk.moment_for_box(1, BLOCK_SIZE))
            body.position = (600 + col * 45, 520 - row * 50)
            shape = pymunk.Poly.create_box(body, BLOCK_SIZE)
            shape.friction, shape.elasticity = 0.5, 0.2
            shape.collision_type = BLOCK_COLLISION_TYPE
            space.add(body, shape)
            blocks.append(body)
    return blocks


async def main():
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Pig Sling Mobile")
    clock = pygame.time.Clock()

    assets = load_assets()
    bird_image = assets["bird_image"]
    pig_image = assets["pig_image"]
    flying_sound = assets["flying_sound"]
    hit_sound = assets["hit_sound"]
    music_path = assets["music_path"]

    space = pymunk.Space()
    space.gravity = (0, 900)

    blocks = build_world(space)
    projectiles = []
    collision_data = {"blocks": blocks, "projectiles": projectiles, "hit_sound": hit_sound}
    collision_handler = space.add_collision_handler(PROJECTILE_COLLISION_TYPE, BLOCK_COLLISION_TYPE)
    collision_handler.begin = lambda arbiter, space, data: handle_projectile_hit(arbiter, space, collision_data)

    dragging = False
    drag_pos = LAUNCH_ORIGIN
    running = True
    music_started = False

    while running:
        pointer_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                pointer = get_pointer_position(event)
                if pointer is not None:
                    if not music_started and os.path.exists(music_path):
                        try:
                            pygame.mixer.music.load(music_path)
                            pygame.mixer.music.set_volume(0.35)
                            pygame.mixer.music.play(-1)
                            music_started = True
                        except pygame.error:
                            music_started = True
                    if math.hypot(pointer[0] - LAUNCH_ORIGIN[0], pointer[1] - LAUNCH_ORIGIN[1]) < 45:
                        dragging = True
                        drag_pos = pointer
            elif event.type in (pygame.MOUSEMOTION, pygame.FINGERMOTION):
                if dragging:
                    next_pos = get_pointer_position(event)
                    if next_pos is not None:
                        drag_pos = next_pos
            elif event.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP):
                if dragging:
                    release_pos = get_pointer_position(event) or pointer_pos
                    dx = LAUNCH_ORIGIN[0] - release_pos[0]
                    dy = LAUNCH_ORIGIN[1] - release_pos[1]
                    launch_projectile(space, projectiles, LAUNCH_ORIGIN, (dx * 15, dy * 15), PROJECTILE_COLLISION_TYPE, flying_sound)
                    dragging = False
                    drag_pos = LAUNCH_ORIGIN

        space.step(1.0 / 60.0)
        screen.fill((30, 30, 35))
        pygame.draw.line(screen, (100, 100, 100), (0, FLOOR_Y), (WIDTH, FLOOR_Y), 5)

        for body in blocks:
            rot = pygame.transform.rotate(pig_image, -math.degrees(body.angle))
            screen.blit(rot, rot.get_rect(center=(round(body.position.x), round(body.position.y))))

        for body in projectiles:
            rot = pygame.transform.rotate(bird_image, -math.degrees(body.angle))
            screen.blit(rot, rot.get_rect(center=(round(body.position.x), round(body.position.y))))

        if dragging:
            pygame.draw.line(screen, (255, 80, 80), LAUNCH_ORIGIN, drag_pos, 3)
            pygame.draw.circle(screen, (255, 200, 0), LAUNCH_ORIGIN, 8)
            screen.blit(bird_image, bird_image.get_rect(center=drag_pos))
        else:
            screen.blit(bird_image, bird_image.get_rect(center=LAUNCH_ORIGIN))

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())