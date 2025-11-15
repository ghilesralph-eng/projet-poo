# graphics.py
import math
import pygame
from pygame import Rect

# --- CONSTANTES PARTAGÉES (doivent matcher game.py) ---
GRID_COLS, GRID_ROWS = 5, 9

class Graphics:
    def __init__(self, width=800, height=600, fps=60):
        self.W, self.H, self.FPS = width, height, fps
        pygame.init()
        self.screen = pygame.display.set_mode((self.W, self.H))
        pygame.display.set_caption("UI – Grille + Draft")
        self.clock = pygame.time.Clock()

        # COULEURS / FONTS
        self.WHITE  = (250, 250, 250)
        self.INK    = (28, 30, 36)
        self.MID    = (120, 124, 130)
        self.ACC    = (42, 126, 210)
        self.BORDER = (205, 205, 205)
        self.BLACK  = (0, 0, 0)
        self.PANEL_BG = (244, 246, 250)

        self.title = pygame.font.SysFont("arial", 28, bold=True)
        self.h2    = pygame.font.SysFont("arial", 22, bold=True)
        self.h3    = pygame.font.SysFont("arial", 18, bold=True)
        self.body  = pygame.font.SysFont("arial", 14)

        # LAYOUT
        self.LEFT_W = int(self.W * 0.58)
        self.RIGHT  = Rect(self.LEFT_W, 0, self.W - self.LEFT_W, self.H)
        self.PADDING = 24

        self.CARD_W, self.CARD_H = 90, 90

        # Ces rectangles sont recalculés à chaque frame
        self.REDRAW_BOX = None
        self.DICE_BTN   = None
        self.CARD_RECTS = []
        self.CHOOSE_TITLE_Y = 0

        # GRILLE
        self.CELL_W = self.LEFT_W // GRID_COLS
        self.CELL_H = self.H // GRID_ROWS
        self.cells_rect = [
            [Rect(c * self.CELL_W, r * self.CELL_H, self.CELL_W, self.CELL_H)
             for c in range(GRID_COLS)]
            for r in range(GRID_ROWS)
        ]

        # Fond gradient
        self.LEFT_BG = pygame.Surface((self.LEFT_W, self.H)).convert()
        for y in range(self.H):
            t = y / max(self.H - 1, 1)
            r = int(20 + 10 * (1 - t))
            g = int(22 + 8 * (1 - t))
            b = int(28 + 6 * (1 - t))
            pygame.draw.line(self.LEFT_BG, (r, g, b), (0, y), (self.LEFT_W, y))

    # --------- LAYOUT PANNEAU DROIT ----------
    def layout_right(self):
        """
        Met en page proprement tout le panneau droit.
        """
        # INVENTAIRE (mais tu l'affiches compact ailleurs)
        inv_rect = Rect(self.RIGHT.x + self.PADDING,
                        self.RIGHT.y + self.PADDING,
                        self.RIGHT.width - 2 * self.PADDING,
                        125)

        # REDRAW
        redraw_top = inv_rect.bottom + 30
        self.REDRAW_BOX = Rect(inv_rect.x,
                               redraw_top,
                               inv_rect.width,
                               110)
        self.DICE_BTN = Rect(
            self.REDRAW_BOX.centerx - 45,
            self.REDRAW_BOX.centery + 10,
            90, 36
        )

        # TITRE + CARTES
        self.CHOOSE_TITLE_Y = self.REDRAW_BOX.bottom + 35
        cards_top = self.CHOOSE_TITLE_Y + 50
        content_w = inv_rect.width
        gap = (content_w - 3 * self.CARD_W) // 2

        self.CARD_RECTS = [
            Rect(inv_rect.x + i * (self.CARD_W + gap), cards_top,
                 self.CARD_W, self.CARD_H)
            for i in range(3)
        ]

        return inv_rect

    # --------- DESSIN GAUCHE ----------
    def draw_left(self, game):
        screen = self.screen
        screen.blit(self.LEFT_BG, (0, 0))

        grid_outer = Rect(0, 0, self.LEFT_W, self.H).inflate(-10, -10)
        pygame.draw.rect(screen, (40, 42, 50), grid_outer, 2, border_radius=14)

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                cell = self.cells_rect[r][c]
                pygame.draw.rect(screen, (60, 62, 70), cell, 1)
                k = game.placed[r][c]
                if k is not None:
                    inner = cell.inflate(-28, -28)
                    pygame.draw.rect(screen, game.room_colors[k],
                                     inner, border_radius=12)
                    pygame.draw.rect(screen, self.WHITE, inner, 5,
                                     border_radius=12)
                    name = self.h3.render(game.room_names[k], True, self.WHITE)
                    screen.blit(
                        name,
                        (inner.centerx - name.get_width() // 2,
                         inner.bottom - name.get_height() - 6),
                    )

        # curseur
        cell = self.cells_rect[game.cur_r][game.cur_c]
        halo_surf = pygame.Surface((cell.width + 20, cell.height + 20),
                                   pygame.SRCALPHA)
        t = pygame.time.get_ticks() / 600.0
        alpha = 60 + int(40 * (0.5 + 0.5 * math.sin(t)))
        pygame.draw.rect(
            halo_surf,
            (self.ACC[0], self.ACC[1], self.ACC[2], alpha),
            halo_surf.get_rect(),
            border_radius=16,
        )
        screen.blit(halo_surf, halo_surf.get_rect(center=cell.center))
        pygame.draw.rect(screen, self.ACC, cell, 3, border_radius=10)

    # --------- INVENTAIRE COMPACT ----------
    def draw_inventory(self, inv_rect, game):
        screen = self.screen
        x = self.RIGHT.right - 140
        y = inv_rect.y - 10

        screen.blit(
            self.h3.render("Inventory", True, self.INK),
            (x, y)
        )
        y += 22
        for k, v in game.inventory.items():
            label = self.body.render(f"{k}:", True, self.MID)
            val   = self.body.render(str(v), True, self.INK)
            screen.blit(label, (x, y))
            screen.blit(val,   (x + 80, y))
            y += 18

    # --------- REDRAW ----------
    def draw_redraw(self, game):
        screen = self.screen
        pygame.draw.rect(screen, self.WHITE, self.REDRAW_BOX, border_radius=16)
        pygame.draw.rect(screen, self.BORDER, self.REDRAW_BOX, 1, border_radius=16)

        lab = self.h2.render("Redraw", True, self.INK)
        sub = self.h3.render("with dice", True, self.MID)
        screen.blit(lab, (self.REDRAW_BOX.centerx - lab.get_width() // 2,
                          self.REDRAW_BOX.y + 10))
        screen.blit(sub, (self.REDRAW_BOX.centerx - sub.get_width() // 2,
                          self.REDRAW_BOX.y + 40))

        mouse = pygame.mouse.get_pos()
        hovered = self.DICE_BTN.collidepoint(mouse)
        btn_color = self.ACC if hovered else self.INK

        pygame.draw.rect(screen, self.WHITE, self.DICE_BTN, border_radius=8)
        pygame.draw.rect(screen, btn_color, self.DICE_BTN, 2, border_radius=8)

        txt = self.h3.render("Roll", True, btn_color)
        screen.blit(txt, (self.DICE_BTN.centerx - txt.get_width() // 2,
                          self.DICE_BTN.centery - txt.get_height() // 2))

        cx, cy = self.DICE_BTN.center
        for dx, dy in [(-10, -8), (10, 8)]:
            pygame.draw.circle(screen, btn_color, (cx + dx, cy + dy), 3)

    # --------- CARTES ----------
    def draw_cards(self, game):
        screen = self.screen
        mouse = pygame.mouse.get_pos()

        title_s = self.h2.render("Choose a room", True, self.INK)
        screen.blit(
            title_s,
            (self.RIGHT.x + (self.RIGHT.width - title_s.get_width()) // 2,
             self.CHOOSE_TITLE_Y),
        )

        for i, base_rect in enumerate(self.CARD_RECTS):
            hovered = base_rect.collidepoint(mouse)
            target = 1.0 if hovered else 0.0
            game.card_hover[i] += (target - game.card_hover[i]) * 0.18
            scale = 1.0 + 0.06 * game.card_hover[i]

            w = int(base_rect.width * scale)
            h = int(base_rect.height * scale)
            rect = Rect(0, 0, w, h)
            rect.center = base_rect.center

            if i == game.focused:
                focus_rect = rect.inflate(10, 10)
                pygame.draw.rect(screen, self.ACC, focus_rect, 3, border_radius=18)

            pygame.draw.rect(screen, game.room_colors[i], rect, border_radius=14)
            pygame.draw.rect(screen, self.WHITE, rect, 5, border_radius=14)

            inner = rect.inflate(-18, -18)
            pygame.draw.rect(screen, self.WHITE, inner, border_radius=10)
            pygame.draw.rect(screen, self.BORDER, inner, 1, border_radius=10)

            name = self.h3.render(game.room_names[i], True, self.INK)
            screen.blit(name, (rect.centerx - name.get_width() // 2,
                               rect.bottom + 6))

            if game.room_sub[i]:
                s = self.body.render(game.room_sub[i], True, self.MID)
                screen.blit(s, (rect.centerx - s.get_width() // 2,
                                rect.bottom + 26))

    # --------- PANEL COMPLET ----------
    def draw_right_panel_bg(self):
        screen = self.screen
        shadow = self.RIGHT.inflate(16, 16)
        shadow_surf = pygame.Surface(shadow.size, pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 40),
                         shadow_surf.get_rect(), border_radius=24)
        screen.blit(shadow_surf, shadow.topleft)

        panel = self.RIGHT.inflate(-16, -16)
        pygame.draw.rect(screen, self.PANEL_BG, panel, border_radius=22)
        pygame.draw.rect(screen, (230, 232, 238), panel, 1, border_radius=22)
        return panel

    # --------- DRAW ALL ----------
    def draw_all(self, game):
        self.screen.fill(self.WHITE)
        self.draw_left(game)
        panel = self.draw_right_panel_bg()
        inv_rect = self.layout_right()
        self.draw_inventory(inv_rect, game)
        self.draw_redraw(game)
        self.draw_cards(game)
        pygame.display.flip()
