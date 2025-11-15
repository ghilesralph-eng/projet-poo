import pygame
from pygame import Rect

# -------------------- FENÊTRE --------------------
W, H = 800, 600
FPS = 60
pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("UI – Grille + Draft")
clock = pygame.time.Clock()

# -------------------- COULEURS / FONTS --------------------
WHITE  = (250, 250, 250)
INK    = (28, 30, 36)
MID    = (120, 124, 130)
ACC    = (42, 126, 210)
BORDER = (205, 205, 205)
BLACK  = (0, 0, 0)
PANEL_BG = (244, 246, 250)

title = pygame.font.SysFont("arial", 34, bold=True)
h2    = pygame.font.SysFont("arial", 24, bold=True)
h3    = pygame.font.SysFont("arial", 20, bold=True)
body  = pygame.font.SysFont("arial", 16)

# -------------------- LAYOUT --------------------
LEFT_W = int(W * 0.58)                  # zone de jeu (gauche)
RIGHT  = Rect(LEFT_W, 0, W - LEFT_W, H) # panneau droit
PADDING = 24

# Cartes RACCOURCIES
CARD_W, CARD_H = 90, 90
cards_top  = int(H * 0.46)
content_w  = RIGHT.width - 2 * PADDING
GAP = (content_w - 3 * CARD_W) // 2
CARD_RECTS = [
    Rect(RIGHT.x + PADDING + i * (CARD_W + GAP), cards_top, CARD_W, CARD_H)
    for i in range(3)
]

# « Redraw with dice » compact
REDRAW_BOX = Rect(RIGHT.right - PADDING - 180, int(H * 0.22), 180, 96)
DICE_BTN   = Rect(REDRAW_BOX.centerx - 40, REDRAW_BOX.bottom - 40, 80, 32)

# -------------------- DONNÉES D’AFFICHAGE --------------------
inventory = {"Steps\u200b": 76, "Coins": 0, "Gems": 2, "Keys": 1, "Dice": 1}  # \u200b = éventuel caractère invisible
STEPS_KEY = next((k for k in inventory.keys() if k.lower().startswith("steps")), "Steps")

room_names  = ["Closet", "Aquarium", "Bedroom"]
room_colors = [(52, 140, 210), (70, 170, 120), (120, 100, 160)]
room_sub    = ["", "", "Gain 2 steps every time you visit this room."]

# -------------------- GRILLE GAUCHE (5x9) --------------------
GRID_COLS, GRID_ROWS = 5, 9
CELL_W = LEFT_W // GRID_COLS
CELL_H = H // GRID_ROWS
cells_rect = [
    [Rect(c * CELL_W, r * CELL_H, CELL_W, CELL_H) for c in range(GRID_COLS)]
    for r in range(GRID_ROWS)
]
placed = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]  # None ou index de carte

# Départ en BAS MILIEU
cur_c, cur_r = 2, 8  # (col=2, row=8)

# Position "lissée" du curseur (pour effet de glissement)
cursor_x, cursor_y = cells_rect[cur_r][cur_c].center

# Sélection carte côté droit
focused = 0

# Animations cartes (hover)
card_hover = [0.0, 0.0, 0.0]  # 0 = normal, 1 = max hover

# -------------------- FOND GRADIENT GAUCHE --------------------
LEFT_BG = pygame.Surface((LEFT_W, H)).convert()
for y in range(H):
    t = y / max(H - 1, 1)
    # gradient vertic. du gris foncé au presque noir
    r = int(20 + 10 * (1 - t))
    g = int(22 + 8 * (1 - t))
    b = int(28 + 6 * (1 - t))
    pygame.draw.line(LEFT_BG, (r, g, b), (0, y), (LEFT_W, y))

# -------------------- DESSIN --------------------
def draw_left():
    # fond gradient
    screen.blit(LEFT_BG, (0, 0))

    # légère "bordure" autour de la grille
    grid_outer = Rect(0, 0, LEFT_W, H).inflate(-10, -10)
    pygame.draw.rect(screen, (40, 42, 50), grid_outer, 2, border_radius=14)

    # grille des salles
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            cell = cells_rect[r][c]
            pygame.draw.rect(screen, (60, 62, 70), cell, 1)
            k = placed[r][c]
            if k is not None:
                inner = cell.inflate(-28, -28)
                # fond salle
                pygame.draw.rect(screen, room_colors[k], inner, border_radius=12)
                # bord blanc
                pygame.draw.rect(screen, WHITE, inner, 5, border_radius=12)
                # nom
                name = h3.render(room_names[k], True, WHITE)
                screen.blit(
                    name,
                    (inner.centerx - name.get_width() // 2,
                     inner.bottom - name.get_height() - 6),
                )

    # curseur : halo + contour animé autour de la cellule courante
    cell = cells_rect[cur_r][cur_c]
    halo_surf = pygame.Surface((cell.width + 20, cell.height + 20), pygame.SRCALPHA)
    # pulsation avec le temps
    t = pygame.time.get_ticks() / 600.0
    alpha = 60 + int(40 * (0.5 + 0.5 * pygame.math.sin(t)))
    pygame.draw.rect(
        halo_surf,
        (ACC[0], ACC[1], ACC[2], alpha),
        halo_surf.get_rect(),
        border_radius=16,
    )
    screen.blit(halo_surf, halo_surf.get_rect(center=cell.center))

    pygame.draw.rect(screen, ACC, cell, 3, border_radius=10)

def draw_right_panel_bg():
    # ombre légère
    shadow = RIGHT.inflate(16, 16)
    shadow_surf = pygame.Surface(shadow.size, pygame.SRCALPHA)
    pygame.draw.rect(
        shadow_surf,
        (0, 0, 0, 40),
        shadow_surf.get_rect(),
        border_radius=24,
    )
    screen.blit(shadow_surf, shadow.topleft)

    # panneau principal
    panel = RIGHT.inflate(-16, -16)
    pygame.draw.rect(screen, PANEL_BG, panel, border_radius=22)
    pygame.draw.rect(screen, (230, 232, 238), panel, 1, border_radius=22)
    return panel

def draw_inventory(panel):
    # zone inventaire en haut
    inv_rect = Rect(panel.x + PADDING, panel.y + PADDING,
                    panel.width - 2 * PADDING, 130)
    pygame.draw.rect(screen, WHITE, inv_rect, border_radius=16)
    pygame.draw.rect(screen, BORDER, inv_rect, 1, border_radius=16)

    screen.blit(title.render("Inventory", True, INK),
                (inv_rect.x + 14, inv_rect.y + 10))

    x_val = inv_rect.right - 18
    y = inv_rect.y + 22
    for k, v in inventory.items():
        y += 28
        vs = h2.render(str(v), True, INK)
        ks = h3.render(k, True, MID)
        screen.blit(vs, (x_val - vs.get_width(), y))
        screen.blit(
            ks,
            (x_val - vs.get_width() - 12 - ks.get_width(), y + 4),
        )

def draw_redraw():
    # fond
    pygame.draw.rect(screen, WHITE, REDRAW_BOX, border_radius=16)
    pygame.draw.rect(screen, BORDER, REDRAW_BOX, 1, border_radius=16)

    lab = h2.render("Redraw", True, INK)
    sub = h3.render("with dice", True, MID)
    screen.blit(lab, (REDRAW_BOX.centerx - lab.get_width() // 2, REDRAW_BOX.y + 10))
    screen.blit(sub, (REDRAW_BOX.centerx - sub.get_width() // 2, REDRAW_BOX.y + 40))

    # bouton
    mouse_pos = pygame.mouse.get_pos()
    hovered = DICE_BTN.collidepoint(mouse_pos)
    btn_color = ACC if hovered else INK

    pygame.draw.rect(screen, WHITE, DICE_BTN, border_radius=8)
    pygame.draw.rect(screen, btn_color, DICE_BTN, 2, border_radius=8)

    txt = h3.render("Roll", True, btn_color)
    screen.blit(txt, (DICE_BTN.centerx - txt.get_width() // 2,
                      DICE_BTN.centery - txt.get_height() // 2))

    # points sur le dé
    cx, cy = DICE_BTN.center
    for dx, dy in [(-10, -8), (10, 8)]:
        pygame.draw.circle(screen, btn_color, (cx + dx, cy + dy), 3)

def draw_cards():
    mouse_pos = pygame.mouse.get_pos()

    title_s = h2.render("Choose a room", True, INK)
    screen.blit(
        title_s,
        (RIGHT.x + (RIGHT.width - title_s.get_width()) // 2, int(H * 0.34)),
    )

    for i, base_rect in enumerate(CARD_RECTS):
        # animation hover
        hovered = base_rect.collidepoint(mouse_pos)
        target = 1.0 if hovered else 0.0
        card_hover[i] += (target - card_hover[i]) * 0.18
        scale = 1.0 + 0.06 * card_hover[i]

        # rect agrandi
        w = int(base_rect.width * scale)
        h = int(base_rect.height * scale)
        rect = Rect(0, 0, w, h)
        rect.center = base_rect.center

        # contour de focus
        if i == focused:
            focus_rect = rect.inflate(10, 10)
            pygame.draw.rect(screen, ACC, focus_rect, 3, border_radius=18)

        # carte
        pygame.draw.rect(screen, room_colors[i], rect, border_radius=14)
        pygame.draw.rect(screen, WHITE, rect, 5, border_radius=14)

        inner = rect.inflate(-18, -18)
        pygame.draw.rect(screen, WHITE, inner, border_radius=10)
        pygame.draw.rect(screen, BORDER, inner, 1, border_radius=10)

        # nom de la salle
        name = h3.render(room_names[i], True, INK)
        screen.blit(name, (rect.centerx - name.get_width() // 2, rect.bottom + 6))

        # sous-texte éventuel
        if room_sub[i]:
            s = body.render(room_sub[i], True, MID)
            screen.blit(s, (rect.centerx - s.get_width() // 2, rect.bottom + 26))

def blit_all(panel):
    screen.fill(WHITE)
    draw_left()
    draw_inventory(panel)
    draw_redraw()
    draw_cards()
    pygame.display.flip()

# -------------------- LOGIQUE UI --------------------
def place_current_cell(card_index):
    placed[cur_r][cur_c] = card_index

# -------------------- BOUCLE --------------------
def main():
    global focused, cur_c, cur_r, cursor_x, cursor_y

    running   = True
    sel_cool  = 0
    move_cool = 0

    panel = draw_right_panel_bg()  # juste pour calculer le rect dès le départ

    while running:
        dt = clock.tick(FPS)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    place_current_cell(focused)
                elif e.key in (pygame.K_1, pygame.K_KP1):
                    focused = 0
                elif e.key in (pygame.K_2, pygame.K_KP2):
                    focused = 1
                elif e.key in (pygame.K_3, pygame.K_KP3):
                    focused = 2
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                m = pygame.mouse.get_pos()
                # clic cartes
                for i, r in enumerate(CARD_RECTS):
                    if r.collidepoint(m):
                        focused = i
                # clic bouton reroll
                if DICE_BTN.collidepoint(m) and inventory["Dice"] > 0:
                    inventory["Dice"] -= 1  # placeholder pour l'instant

        keys = pygame.key.get_pressed()

        # Déplacement sur la GRILLE (ZQSD) — incrémente Steps à chaque déplacement effectif
        if move_cool <= 0:
            moved = False
            old_c, old_r = cur_c, cur_r

            if keys[pygame.K_q] and cur_c > 0:
                cur_c -= 1
                moved = True
            elif keys[pygame.K_d] and cur_c < GRID_COLS - 1:
                cur_c += 1
                moved = True
            elif keys[pygame.K_z] and cur_r > 0:
                cur_r -= 1
                moved = True
            elif keys[pygame.K_s] and cur_r < GRID_ROWS - 1:
                cur_r += 1
                moved = True

            if moved and (cur_c != old_c or cur_r != old_r):
                move_cool = 120
                inventory[STEPS_KEY] = inventory.get(STEPS_KEY, 0) + 1  # toujours ton placeholder
        else:
            move_cool -= dt

        # Navigation cartes (flèches gauche/droite)
        if sel_cool <= 0:
            if keys[pygame.K_LEFT]:
                if focused > 0:
                    focused -= 1
                sel_cool = 140
            elif keys[pygame.K_RIGHT]:
                if focused < 2:
                    focused += 1
                sel_cool = 140
        else:
            sel_cool -= dt

        # interpolation douce de la position du curseur
        target_x, target_y = cells_rect[cur_r][cur_c].center
        cursor_x += (target_x - cursor_x) * 0.25
        cursor_y += (target_y - cursor_y) * 0.25

        # redessiner panneau droit (pour l'ombre) + tout le reste
        panel = draw_right_panel_bg()
        blit_all(panel)

    pygame.quit()

if __name__ == "__main__":
    main()
