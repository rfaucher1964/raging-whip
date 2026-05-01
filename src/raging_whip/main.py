import math
import sys
from collections import deque
from pathlib import Path

import pygame


# ------------------------------------------------------------
# Raging Whip - Taller City Walk Test v0.4
# ------------------------------------------------------------
# Goals of this revision:
#   - cleaner transparent sprite handling
#   - smaller building footprints
#   - taller-feeling buildings using per-building height multipliers
#   - repeated/tiled wall columns so high-rises look like stacked floors
#   - a more street-canyon city layout
#
# Controls:
#   W / S        forward / backward
#   A / D        strafe left / right
#   Mouse        turn left / right
#   TAB          toggle minimap
#   ESC          quit
# ------------------------------------------------------------

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
HALF_HEIGHT = SCREEN_HEIGHT // 2

FOV = math.radians(66)
NUM_RAYS = 160
MAX_DEPTH = 46
DELTA_ANGLE = FOV / NUM_RAYS
DIST_TO_PROJ_PLANE = (SCREEN_WIDTH / 2) / math.tan(FOV / 2)
SCALE = SCREEN_WIDTH // NUM_RAYS

MOVE_SPEED = 3.7
MOUSE_SENSITIVITY = 0.0025
PLAYER_RADIUS = 0.18

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS = PROJECT_ROOT / "assets"
GROUND_DIR = ASSETS / "textures" / "ground"
WALLS_DIR = ASSETS / "textures" / "walls"
BUILDINGS_DIR = ASSETS / "textures" / "buildings"
PROPS_DIR = ASSETS / "sprites" / "city_props"


# ------------------------------------------------------------
# Map legend
# ------------------------------------------------------------
# Ground / walkable:
#   . = road
#   s = sidewalk
#   c = curb
#   l = grass/lawn
#   p = plaza/light pavement
#   P = player start
#
# Walls/buildings:
#   O = high-rise office facade
#   B = old red brick facade
#   A = apartment/stucco facade
#   R = grim stone residential/commercial facade
#   T = storefront facade
#   E = urban doorway facade
#   G = industrial garage facade
#   H = city hall / institutional wall
#   W = generic brick wall fallback
#   F = construction fence fallback
#
# Props / walkable:
#   1 = fire hydrant
#   2 = mailbox
#   3 = newspaper dispenser
#   4 = park bench
#   5 = utility pole with streetlight
#   6 = construction barricade
#   7 = trash can
#   8 = streetlamp
#   9 = Speak & Spell dumpster
# ------------------------------------------------------------

CITY_MAP_RAW = [
    "OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO",
    "OssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssO",
    "Os1ssss2sssss3ssssssssssssssssss4sssssssssss8sssssssssssssssssO",
    "OssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssO",
    "OccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccO",
    "O..............................................................O",
    "O..............................................................O",
    "OccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccO",
    "OssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssO",
    "OBBTEBBssOOOEOOOssAATTAAssRRRERRRssOOOTOOOssBBTEBBssAAAETAAO",
    "OBBTEBBssOOOEOOOssAATTAAssRRRERRRssOOOTOOOssBBTEBBssAAAETAAO",
    "OssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssO",
    "OccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccO",
    "O....................cccccccccccccccccccc......................O",
    "O....................ssssssssssssssssssss......................O",
    "Occccccccccccccccc...ssssssssssssssssssss...ccccccccccccccccccO",
    "Osssssssssssssssss...s5sssssssssssssss7ss...sssssssssssssssssO",
    "OHHHEHHHssBBBBBBBss...llllllllllllllll...ssGGGGGGGGssFFFFFAAAO",
    "OHHHEHHHssBBBBBBBss...llllllllllllllll...ssGGGGGGGGssF.....AAO",
    "OHHHHHHHssBBBBBBBss...llllllllllllllll...ssGGGGGGGGssF..9..AAO",
    "OssssssssssssssssssssssssssssssssssssssssssssssssssssF.....AAO",
    "OccccccccccccccccccccccccccccccccccccccccccccccccccccFFFFFFAAO",
    "O..............................................................O",
    "O......................P.......................................O",
    "O..............................................................O",
    "OccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccO",
    "OssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssO",
    "ORRERRRssOOOTOOOssBBTEBBssAAAETAAssRRRERRRssOOOEOOOssBBBTBBBO",
    "ORRERRRssOOOTOOOssBBTEBBssAAAETAAssRRRERRRssOOOEOOOssBBBTBBBO",
    "OssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssO",
    "Osssssssssssssssssss6sssssssssssssssssssssssssssssssssssssssssO",
    "OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO",
]

MAP_WIDTH = max(len(row) for row in CITY_MAP_RAW)
CITY_MAP = [row.ljust(MAP_WIDTH, "O") for row in CITY_MAP_RAW]
MAP_HEIGHT = len(CITY_MAP)


WALL_TEXTURE_FILES = {
    "O": "office_facade.png",
    "B": "brick_facade.png",
    "A": "apartment_facade.png",
    "R": "grim_building_facade.png",
    "T": "storefront_facade_texture.png",
    "E": "urban_doorway_texture.png",
    "G": "industrial_garage.png",
    "H": "city_hall_paneling.png",
    "W": "brick_wall.png",
    "F": "construction_fence.png",
}

WALL_TEXTURE_DIRS = {
    "O": BUILDINGS_DIR,
    "B": BUILDINGS_DIR,
    "A": BUILDINGS_DIR,
    "R": BUILDINGS_DIR,
    "T": BUILDINGS_DIR,
    "E": BUILDINGS_DIR,
    "G": BUILDINGS_DIR,
    "H": WALLS_DIR,
    "W": WALLS_DIR,
    "F": WALLS_DIR,
}

# This is the main trick for taller-looking buildings.
# High-rise and apartment façades are rendered taller than storefronts.
BUILDING_HEIGHT_MULT = {
    "O": 2.35,   # high-rise office
    "B": 1.80,   # older brick mid-rise
    "A": 1.90,   # apartment/stucco
    "R": 2.05,   # grim stone commercial/residential
    "T": 1.20,   # storefronts stay lower
    "E": 1.15,   # doorways stay lower
    "G": 1.25,   # garages stay lower
    "H": 1.70,   # institutional
    "W": 1.50,
    "F": 1.10,
}

GROUND_TEXTURE_FILES = {
    ".": "road.png",
    "s": "sidewalk.png",
    "c": "curb.png",
    "l": "lawn.png",
    "p": "sidewalk.png",
    "P": "road.png",
    "1": "sidewalk.png",
    "2": "sidewalk.png",
    "3": "sidewalk.png",
    "4": "sidewalk.png",
    "5": "sidewalk.png",
    "6": "road.png",
    "7": "sidewalk.png",
    "8": "sidewalk.png",
    "9": "sidewalk.png",
}

PROP_DEFS = {
    "1": {"name": "fire_hydrant", "file": "fire_hydrant.png", "scale": 0.48},
    "2": {"name": "mailbox", "file": "mailbox.png", "scale": 0.62},
    "3": {"name": "newspaper_dispenser", "file": "newspaper_dispenser.png", "scale": 0.62},
    "4": {"name": "park_bench", "file": "park_bench.png", "scale": 0.92},
    "5": {"name": "utility_pole", "file": "utility_pole_with_streetlight.png", "scale": 1.60},
    "6": {"name": "construction_barricade", "file": "construction_barricade.png", "scale": 0.86},
    "7": {"name": "trash_can", "file": "trash_can.png", "scale": 0.50},
    "8": {"name": "streetlamp", "file": "streetlamp.png", "scale": 1.45},
    "9": {"name": "speak_spell_dumpster", "file": "speak_spell_dumpster.png", "scale": 0.98},
}

SPRITE_OBJECTS = []
PLAYER_START = (MAP_WIDTH / 2, MAP_HEIGHT / 2)

for my, row in enumerate(CITY_MAP):
    for mx, tile in enumerate(row):
        if tile == "P":
            PLAYER_START = (mx + 0.5, my + 0.5)
        elif tile in PROP_DEFS:
            prop = dict(PROP_DEFS[tile])
            prop["x"] = mx + 0.5
            prop["y"] = my + 0.5
            SPRITE_OBJECTS.append(prop)


def load_texture(path: Path, size=(256, 256)) -> pygame.Surface:
    if not path.exists():
        print(f"Missing asset: {path}")
        surf = pygame.Surface(size).convert()
        surf.fill((255, 0, 255))
        return surf

    surf = pygame.image.load(path).convert()
    return pygame.transform.scale(surf, size)


def is_checker_or_near_white(pixel: pygame.Color) -> bool:
    # Handles generated checkerboard backgrounds or near-white non-alpha areas.
    # We use this only from edge flood-fill, so it should not erase isolated white highlights.
    r, g, b, a = pixel.r, pixel.g, pixel.b, pixel.a
    if a < 20:
        return True
    return r > 215 and g > 215 and b > 215 and (max(r, g, b) - min(r, g, b) < 45)


def remove_edge_background_alpha(surf: pygame.Surface) -> pygame.Surface:
    """Remove transparent/checkerboard-like background connected to the image edges.

    This is safer than just removing all white/gray pixels, because white highlights
    inside a sprite are not connected to the outer background and should stay visible.
    """
    surf = surf.convert_alpha()
    w, h = surf.get_size()
    visited = set()
    q = deque()

    for x in range(w):
        q.append((x, 0))
        q.append((x, h - 1))
    for y in range(h):
        q.append((0, y))
        q.append((w - 1, y))

    while q:
        x, y = q.popleft()
        if (x, y) in visited:
            continue
        if x < 0 or y < 0 or x >= w or y >= h:
            continue
        visited.add((x, y))

        pixel = surf.get_at((x, y))
        if not is_checker_or_near_white(pixel):
            continue

        surf.set_at((x, y), (pixel.r, pixel.g, pixel.b, 0))
        q.append((x + 1, y))
        q.append((x - 1, y))
        q.append((x, y + 1))
        q.append((x, y - 1))

    return surf


def load_sprite(path: Path, size=(256, 256)) -> pygame.Surface:
    if not path.exists():
        print(f"Missing sprite: {path}")
        surf = pygame.Surface(size).convert_alpha()
        surf.fill((255, 0, 255, 255))
        return surf

    surf = pygame.image.load(path).convert_alpha()
    surf = pygame.transform.scale(surf, size)
    surf = remove_edge_background_alpha(surf)
    return surf


def is_wall(x: float, y: float) -> bool:
    mx, my = int(x), int(y)
    if mx < 0 or my < 0 or mx >= MAP_WIDTH or my >= MAP_HEIGHT:
        return True
    tile = CITY_MAP[my][mx]
    return tile in WALL_TEXTURE_FILES


def get_tile(x: float, y: float) -> str:
    mx, my = int(x), int(y)
    if mx < 0 or my < 0 or mx >= MAP_WIDTH or my >= MAP_HEIGHT:
        return "."
    return CITY_MAP[my][mx]


def cast_single_ray(px, py, angle):
    sin_a = math.sin(angle)
    cos_a = math.cos(angle)
    step = 0.02
    depth = 0.01

    while depth < MAX_DEPTH:
        x = px + cos_a * depth
        y = py + sin_a * depth
        if is_wall(x, y):
            tile = get_tile(x, y)
            hit_x = x - int(x)
            hit_y = y - int(y)
            tex_x = hit_y if hit_x < 0.03 or hit_x > 0.97 else hit_x
            return depth, tile, tex_x
        depth += step

    return MAX_DEPTH, "O", 0.0


def draw_sky(screen):
    for y in range(HALF_HEIGHT):
        t = y / HALF_HEIGHT
        r = int(95 + 75 * t)
        g = int(175 + 45 * t)
        b = int(235 + 10 * t)
        pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    pygame.draw.circle(screen, (255, 240, 160), (SCREEN_WIDTH - 140, 90), 38)


def draw_floor(screen, player_x, player_y, player_angle, ground_textures):
    """Fast floor renderer.

    This is intentionally simple. The previous textured floor sampled thousands
    of pixels every frame and made the prototype crawl. This version draws a
    road-colored lower half and simple bands for a retro city-street feel.
    """
    road_color = (58, 58, 58)
    near_road_color = (42, 42, 42)

    pygame.draw.rect(screen, road_color, (0, HALF_HEIGHT, SCREEN_WIDTH, HALF_HEIGHT))

    # Darker near-ground band for depth.
    pygame.draw.rect(screen, near_road_color, (0, int(SCREEN_HEIGHT * 0.78), SCREEN_WIDTH, int(SCREEN_HEIGHT * 0.22)))

    # Simple sidewalk/curb illusion near the horizon.
    pygame.draw.rect(screen, (125, 125, 115), (0, HALF_HEIGHT, SCREEN_WIDTH, 28))
    pygame.draw.rect(screen, (90, 90, 84), (0, HALF_HEIGHT + 28, SCREEN_WIDTH, 8))

def make_tiled_wall_column(texture: pygame.Surface, tex_column: int, width: int, height: int, repeat_factor: float) -> pygame.Surface:
    """Fast wall column rendering.

    v0.4 originally tiled every wall column pixel-by-pixel, which looked decent
    but was far too slow in Python. This faster version scales one texture column.
    Taller buildings still come from BUILDING_HEIGHT_MULT.
    """
    tex_w, tex_h = texture.get_size()
    tex_column = max(0, min(tex_w - 1, tex_column))
    column = texture.subsurface((tex_column, 0, 1, tex_h))
    return pygame.transform.scale(column, (width, height))


def draw_walls(screen, player_x, player_y, player_angle, wall_textures):
    start_angle = player_angle - FOV / 2
    zbuffer = [MAX_DEPTH] * NUM_RAYS

    for ray in range(NUM_RAYS):
        angle = start_angle + ray * DELTA_ANGLE
        depth, tile, tex_x = cast_single_ray(player_x, player_y, angle)
        depth *= math.cos(player_angle - angle)
        depth = max(depth, 0.0001)
        zbuffer[ray] = depth

        height_mult = BUILDING_HEIGHT_MULT.get(tile, 1.0)
        wall_height = int((DIST_TO_PROJ_PLANE / depth) * height_mult)
        wall_height = min(wall_height, SCREEN_HEIGHT * 3)

        texture = wall_textures.get(tile)
        if texture is None:
            pygame.draw.rect(screen, (255, 0, 255), (ray * SCALE, HALF_HEIGHT - wall_height // 2, SCALE, wall_height))
            continue

        tex_w, _tex_h = texture.get_size()
        tex_column = int(tex_x * tex_w) % tex_w

        # Tall buildings get vertical texture repetitions. Low storefronts/doors do not.
        repeat_factor = max(1.0, height_mult * 1.25)
        column = make_tiled_wall_column(texture, tex_column, SCALE, wall_height, repeat_factor)

        shade = max(0.38, min(1.0, 6.2 / (depth + 0.8)))
        if shade < 1.0:
            dark = pygame.Surface(column.get_size()).convert_alpha()
            dark.fill((0, 0, 0, int(255 * (1 - shade))))
            column.blit(dark, (0, 0))

        screen.blit(column, (ray * SCALE, HALF_HEIGHT - wall_height // 2))

    return zbuffer


def draw_sprites(screen, player_x, player_y, player_angle, object_textures, zbuffer):
    visible = []
    for obj in SPRITE_OBJECTS:
        dx = obj["x"] - player_x
        dy = obj["y"] - player_y
        dist = math.hypot(dx, dy)
        theta = math.atan2(dy, dx)
        gamma = theta - player_angle

        while gamma > math.pi:
            gamma -= 2 * math.pi
        while gamma < -math.pi:
            gamma += 2 * math.pi

        if -FOV * 0.85 < gamma < FOV * 0.85 and dist > 0.25:
            visible.append((dist, gamma, obj))

    visible.sort(reverse=True, key=lambda item: item[0])

    for dist, gamma, obj in visible:
        texture = object_textures.get(obj["file"])
        if texture is None:
            continue

        corrected_dist = dist * math.cos(gamma)
        if corrected_dist <= 0:
            continue

        proj_height = int((DIST_TO_PROJ_PLANE / corrected_dist) * obj.get("scale", 1.0))
        proj_width = proj_height
        if proj_height <= 3:
            continue

        screen_x = int((SCREEN_WIDTH / 2) + math.tan(gamma) * DIST_TO_PROJ_PLANE - proj_width / 2)
        screen_y = int(HALF_HEIGHT + proj_height * 0.92 - proj_height)

        first_ray = max(0, screen_x // SCALE)
        last_ray = min(NUM_RAYS - 1, (screen_x + proj_width) // SCALE)
        if first_ray <= last_ray and corrected_dist > min(zbuffer[first_ray:last_ray + 1]):
            continue

        sprite = pygame.transform.scale(texture, (proj_width, proj_height))
        shade = max(0.50, min(1.0, 5.2 / (corrected_dist + 0.8)))
        if shade < 1.0:
            dark = pygame.Surface(sprite.get_size()).convert_alpha()
            dark.fill((0, 0, 0, int(255 * (1 - shade))))
            sprite.blit(dark, (0, 0))

        screen.blit(sprite, (screen_x, screen_y))


def move_player(px, py, angle, dt, keys):
    speed = MOVE_SPEED * dt
    dx = dy = 0.0

    forward_x = math.cos(angle)
    forward_y = math.sin(angle)
    right_x = math.cos(angle + math.pi / 2)
    right_y = math.sin(angle + math.pi / 2)

    if keys[pygame.K_w]:
        dx += forward_x * speed
        dy += forward_y * speed
    if keys[pygame.K_s]:
        dx -= forward_x * speed
        dy -= forward_y * speed
    if keys[pygame.K_d]:
        dx += right_x * speed
        dy += right_y * speed
    if keys[pygame.K_a]:
        dx -= right_x * speed
        dy -= right_y * speed

    new_x = px + dx
    new_y = py + dy

    if not is_wall(new_x + PLAYER_RADIUS, py) and not is_wall(new_x - PLAYER_RADIUS, py):
        px = new_x
    if not is_wall(px, new_y + PLAYER_RADIUS) and not is_wall(px, new_y - PLAYER_RADIUS):
        py = new_y

    return px, py


def draw_minimap(screen, px, py, angle):
    tile_size = 4
    offset_x = 14
    offset_y = 14

    for y, row in enumerate(CITY_MAP):
        for x, tile in enumerate(row):
            rect = pygame.Rect(offset_x + x * tile_size, offset_y + y * tile_size, tile_size, tile_size)
            if tile in WALL_TEXTURE_FILES:
                color = (75, 75, 75)
            elif tile == ".":
                color = (35, 35, 35)
            elif tile == "s":
                color = (145, 145, 132)
            elif tile == "c":
                color = (100, 100, 90)
            elif tile == "l":
                color = (50, 120, 40)
            elif tile in PROP_DEFS:
                color = (30, 200, 60)
            else:
                color = (120, 120, 110)
            pygame.draw.rect(screen, color, rect)

    player_screen_x = offset_x + int(px * tile_size)
    player_screen_y = offset_y + int(py * tile_size)
    pygame.draw.circle(screen, (255, 0, 0), (player_screen_x, player_screen_y), 4)
    pygame.draw.line(
        screen,
        (255, 255, 0),
        (player_screen_x, player_screen_y),
        (player_screen_x + int(math.cos(angle) * 12), player_screen_y + int(math.sin(angle) * 12)),
        2,
    )


def main():
    pygame.init()
    pygame.display.set_caption("Raging Whip - Taller City Walk Test v0.4")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 18)

    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    wall_textures = {}
    for tile, filename in WALL_TEXTURE_FILES.items():
        wall_textures[tile] = load_texture(WALL_TEXTURE_DIRS[tile] / filename)

    ground_textures = {
        filename: load_texture(GROUND_DIR / filename)
        for filename in set(GROUND_TEXTURE_FILES.values())
    }

    object_textures = {}
    for obj in SPRITE_OBJECTS:
        object_textures[obj["file"]] = load_sprite(PROPS_DIR / obj["file"], size=(256, 256))

    player_x, player_y = PLAYER_START
    player_angle = -math.pi / 2
    show_minimap = True

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_TAB:
                    show_minimap = not show_minimap
            elif event.type == pygame.MOUSEMOTION:
                mouse_dx, _mouse_dy = event.rel
                player_angle += mouse_dx * MOUSE_SENSITIVITY

        keys = pygame.key.get_pressed()
        player_x, player_y = move_player(player_x, player_y, player_angle, dt, keys)

        draw_sky(screen)
        draw_floor(screen, player_x, player_y, player_angle, ground_textures)
        zbuffer = draw_walls(screen, player_x, player_y, player_angle, wall_textures)
        draw_sprites(screen, player_x, player_y, player_angle, object_textures, zbuffer)

        if show_minimap:
            draw_minimap(screen, player_x, player_y, player_angle)

        tile = get_tile(player_x, player_y)
        hud = font.render(
            f"City Walk v0.4 | FPS {clock.get_fps():.0f} | tile {tile} | WASD | mouse | TAB map | ESC",
            True,
            (20, 20, 20),
        )
        screen.blit(hud, (16, SCREEN_HEIGHT - 32))
        pygame.display.flip()

    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

