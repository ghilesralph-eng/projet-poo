"""
Blue Prince — Prototype Pygame (Option D)

Fonctionnalités incluses (version D):
- Grille 5x9 avec pièces posées progressivement
- Déplacement ZQSD pour choisir une direction, Espace pour valider (spec. 2.5) 
- Ouverture de portes avec niveaux de verrouillage 0/1/2 + clés / kit de crochetage (spec. 2.6)
- Tirage de 3 pièces pondéré par rareté, au moins une pièce coût 0 gemme (spec. 2.7)
- Reroll avec dés (si disponible)
- HUD d'inventaire (pas, gemmes, clés, dés, pièces) et décrémentation des pas (spec. 2.1)
- Quelques pièces réelles avec effets simples (gains de ressources)
- Condition de placement pour une pièce (Veranda = bordure)
- Victoire en atteignant l'Antechamber (haut de la grille), défaite si plus de pas

Contrôles:
- Z / Q / S / D : choisir la direction (haut / gauche / bas / droite)
- ESPACE : valider l'action (se déplacer ou ouvrir)
- ÉCHAP : quitter
- Pendant le tirage: ←/→ ou A/D pour sélectionner, ENTRÉE pour poser, R pour relancer (si dés>0)
"""

import sys
import random
import pygame
from typing import Dict, List, Optional, Tuple

from inventory.inventory import Inventory
from rooms.room_data import RoomDef
from player import Player
from manor import Manor, GRID_ROWS, GRID_COLS  # ton manor propre

# ==========================
# Constantes & couleurs
# ==========================
WIDTH, HEIGHT = 1200, 800
FPS = 60

GRID_ROWS, GRID_COLS = 9, 5    # 9 lignes, 5 colonnes

HEADER_H = 96                  # bandeau du haut
MARGIN   = 10                  # marge entre les cases
TILE     = 64                  # TAILLE FIXE d’une case

# Taille de la grille
GRID_W = GRID_COLS * TILE + (GRID_COLS + 1) * MARGIN
GRID_H = GRID_ROWS * TILE + (GRID_ROWS + 1) * MARGIN

# Position de la grille (gauche)
GRID_X = 40
GRID_Y = HEADER_H + 24         # un peu sous le header

BG = (18, 20, 26)
PANEL = (30, 34, 44)
TEXT = (235, 240, 255)
SUBTLE = (160, 170, 190)
ACCENT = (120, 180, 255)
DANGER = (230, 80, 80)
SUCCESS = (90, 200, 140)
OUTLINE = (240, 245, 255)


ROOM_COLORS = {
    "blue": (70, 110, 170),
    "yellow": (220, 190, 60),
    "green": (80, 160, 110),
    "purple": (150, 100, 170),
    "orange": (220, 140, 80),
    "red": (200, 80, 80),
}

# Directions (r, c)
DIRS: Dict[str, Tuple[int, int]] = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
}
KEY_TO_DIR = {
    pygame.K_z: "up",
    pygame.K_w: "up",
    pygame.K_s: "down",
    pygame.K_q: "left",
    pygame.K_a: "left",
    pygame.K_d: "right",
}

# ==========================
# Utilitaires
# ==========================

def inside(r: int, c: int) -> bool:
    return 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS


def grid_to_px(r: int, c: int) -> pygame.Rect:
    x = GRID_X + MARGIN + c * (TILE + MARGIN)
    y = GRID_Y + MARGIN + r * (TILE + MARGIN)
    return pygame.Rect(x, y, TILE, TILE)


def draw_rounded(surface, color, rect, radius=16, width=0):
    pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)


def text(surface, s, font, color, center=None, topleft=None):
    surf = font.render(s, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = center
    if topleft:
        rect.topleft = topleft
    surface.blit(surf, rect)
    return rect

# ==========================
# Effets de pièces
# ==========================

def apply_room_effect(inv: Inventory, rd: RoomDef):
    # Certains RoomDef n’ont pas d’effet → None par défaut
    effect = getattr(rd, "effect_on_enter", None)

    if effect == "+steps_10":
        inv.add_steps(10)

    elif effect == "+coins_40":
        inv.add_coins(40)

    elif effect == "+gem_chance":
        p = 0.5 + (0.2 if inv.rabbit_foot else 0)
        if random.random() < p:
            inv.add_gems(1)

    elif effect == "shop_sample":
        if inv.coins >= 10:
            inv.use_coins(10)
            inv.add_keys(1)


# ==========================
# UI de tirage
# ==========================

class DrawUI:
    def __init__(self, font, font_small):
        self.font = font
        self.font_small = font_small
        self.active = False
        self.candidates: List[RoomDef] = []
        self.selected = 0
        self.pos: Tuple[int, int] = (0, 0)
        self.from_dir: str = "up"

    def open(self, candidates: List[RoomDef], pos: Tuple[int, int], from_dir: str):
        self.active = True
        self.candidates = candidates
        self.selected = 0
        self.pos = pos
        self.from_dir = from_dir

    def close(self):
        self.active = False

    def handle_event(self, e, inventory: Inventory, manor: Manor):
        if not self.active:
            return None
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_LEFT, pygame.K_a):
                self.selected = (self.selected - 1) % len(self.candidates)
            elif e.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = (self.selected + 1) % len(self.candidates)
            elif e.key == pygame.K_r:
                if inventory.dice > 0:
                    inventory.use_dice(1)
                    r, c = self.pos          # r = ligne, c = colonne
                    self.candidates = manor.draw_candidates(r, c, self.from_dir)
                    self.selected = 0
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                choice = self.candidates[self.selected]
                cost = choice.gem_cost if not isinstance(choice.gem_cost, tuple) else choice.gem_cost[0]
                if not inventory.use_gems(cost):
                    return None
                r, c = self.pos              # r = ligne, c = colonne
                manor.place_room(choice, r, c, self.from_dir)
                self.close()
                return (r, c, choice)
        return None

    def draw(self, screen):
        if not self.active:
            return
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        panel = pygame.Rect(120, 140, WIDTH - 240, HEIGHT - 280)
        draw_rounded(screen, PANEL, panel, 20)
        text(
            screen,
            "Choisis une pièce (Entrée pour poser, R = relancer si dés)",
            self.font,
            TEXT,
            center=(panel.centerx, panel.top + 40),
        )

        if not self.candidates:
            text(screen, "Aucune pièce admissible ici…", self.font, DANGER, center=panel.center)
            return

        card_w = 260
        gap = 40
        total_w = len(self.candidates) * card_w + (len(self.candidates) - 1) * gap
        start_x = panel.centerx - total_w // 2
        y = panel.top + 90

        for i, rd in enumerate(self.candidates):
            rect = pygame.Rect(start_x + i * (card_w + gap), y, card_w, 360)
            sel = (i == self.selected)
            draw_rounded(screen, (60, 65, 80) if not sel else (80, 90, 110), rect, 18)

            color = ROOM_COLORS.get(rd.color, (120, 120, 120))
            head = rect.copy()
            head.height = 56
            draw_rounded(screen, color, head, 18)
            text(screen, rd.name, self.font, (20, 20, 20), center=head.center)

            y2 = rect.top + 80
            text(screen, f"Couleur: {rd.color}", self.font_small, TEXT, topleft=(rect.left + 16, y2)); y2 += 28
            text(screen, f"Rareté: {rd.rarity}", self.font_small, TEXT, topleft=(rect.left + 16, y2)); y2 += 28
            text(screen, f"Coût gemmes: {rd.gem_cost}", self.font_small, TEXT, topleft=(rect.left + 16, y2)); y2 += 28

            y2 += 8
            text(screen, "Portes:", self.font_small, SUBTLE, topleft=(rect.left + 16, y2)); y2 += 24
            pr = ["↑", "→", "↓", "←"]
            s = " ".join([pr[i] if rd.doors[i] else "·" for i in range(4)])
            text(screen, s, self.font, TEXT, topleft=(rect.left + 16, y2)); y2 += 36

            if getattr(rd, "placement_condition", None) == "border_only":
                text(screen, "Placement: bordure",
                     self.font_small, SUBTLE,
                     topleft=(rect.left + 16, y2)); y2 += 28

            effect = getattr(rd, "effect_on_enter", None)
            if effect:
                text(screen, f"Effet: {effect}",
                     self.font_small, SUBTLE,
                     topleft=(rect.left + 16, y2)); y2 += 28

# ==========================
# Jeu principal
# ==========================

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Blue Prince — Prototype Pygame (D)")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 22)
        self.font_big = pygame.font.SysFont("arial", 28, bold=True)
        self.font_small = pygame.font.SysFont("arial", 18)

        self.inventory = Inventory()
        self.manor = Manor()

        # Manor.start doit être (row, col)
        sr, sc = self.manor.start
        self.player = Player(sr, sc, self.inventory)

        self.message = "ZQSD pour choisir, ESPACE pour valider. Objectif: atteindre l'Antechamber tout en haut."
        self.draw_ui = DrawUI(self.font_big, self.font)
        self.game_over: Optional[str] = None

    def current_room(self):
        r, c = self.player.r, self.player.c
        return self.manor.grid[r][c]

    def try_action(self):
        if self.game_over or self.draw_ui.active:
            return
        dname = self.player.dir
        dr, dc = DIRS[dname]
        r, c = self.player.r + dr, self.player.c + dc
        if not inside(r, c):
            self.message = "Un mur bloque ce côté."
            return
        here = self.current_room()
        idx_map = {"up": 0, "right": 1, "down": 2, "left": 3}
        i = idx_map[dname]
        if not here.placed_doors[i]:
            self.message = "Aucune porte de ce côté."
            return

        # pièce déjà existante
        if self.manor.grid[r][c] is not None:
            self.player.r, self.player.c = r, c
            self.player.use_step()
            rd = self.manor.grid[r][c].definition
            apply_room_effect(self.inventory, rd)
            self.post_move_check()
            return

        # nouvelle pièce : porte verrouillée
        lock = self.manor.lock_level_for_row(r)
        if not self.inventory.can_open(lock):
            if lock == 1 and self.inventory.lockpick:
                pass
            else:
                self.message = f"Porte verrouillée (niv {lock}). Il te faut des clés."
                return
        self.inventory.spend_for_lock(lock)

        cands = self.manor.draw_candidates(r, c, dname)
        if not cands:
            self.message = "Aucune pièce admissible ici…"
            return
        self.draw_ui.open(cands, (r, c), dname)

    def post_move_check(self):
        if self.inventory.steps <= 0:
            self.game_over = "Défaite: plus de pas."
            return
        if (self.player.r, self.player.c) == self.manor.goal:
            self.game_over = "Victoire! Tu as atteint l'Antechamber."

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

                if self.draw_ui.active:
                    placed = self.draw_ui.handle_event(e, self.inventory, self.manor)
                    if placed:
                        r, c, _ = placed
                        self.player.r, self.player.c = r, c
                        self.player.use_step()
                        apply_room_effect(self.inventory, self.manor.grid[r][c].definition)
                        self.post_move_check()
                    continue

                if e.key in KEY_TO_DIR:
                    self.player.set_dir(KEY_TO_DIR[e.key])
                elif e.key == pygame.K_SPACE:
                    self.try_action()

    def draw_grid(self):
        # Bandeau haut
        # Bandeau haut (titre seulement)
        header = pygame.Rect(0, 0, WIDTH, HEADER_H)
        draw_rounded(self.screen, PANEL, header, 0)
        text(
            self.screen,
            "Blue Prince — Prototype Pygame (Option D)",
            self.font_big, TEXT,
            center=(WIDTH // 2, 28)
        )

        # Panneau latéral droit
        right_x = GRID_X + GRID_W + 40
        right_w = WIDTH - right_x - 40
        right_panel = pygame.Rect(
            right_x,
            HEADER_H + 20,
            right_w,
            HEIGHT - HEADER_H - 40
        )
        draw_rounded(self.screen, PANEL, right_panel, 18)

        # Inventaire en haut du panneau droit
        y = right_panel.y + 20
        text(self.screen, "Inventaire", self.font_big, TEXT,
             topleft=(right_panel.x + 20, y))
        y += 40

        stats_lines = [
            f"Pas : {self.inventory.steps}",
            f"Gemmes : {self.inventory.gems}",
            f"Clés : {self.inventory.keys}",
            f"Dés : {self.inventory.dice}",
            f"Pièces : {self.inventory.coins}",
        ]
        for line in stats_lines:
            text(self.screen, line, self.font, TEXT,
                 topleft=(right_panel.x + 30, y))
            y += 28

        # Permanents (lockpick, etc.)
        perks = []
        if self.inventory.lockpick:
            perks.append("Crochetage")
        if self.inventory.rabbit_foot:
            perks.append("Patte de lapin")
        if self.inventory.metal_detector:
            perks.append("Détecteur")

        if perks:
            y += 10
            text(self.screen, "Objets permanents :", self.font_small, SUBTLE,
                 topleft=(right_panel.x + 20, y))
            y += 26
            text(self.screen, " • " + " | ".join(perks),
                 self.font_small, TEXT,
                 topleft=(right_panel.x + 30, y))

        # Message de jeu en bas du panneau droit
        text(
            self.screen,
            self.message,
            self.font_small, SUBTLE,
            topleft=(right_panel.x + 24, right_panel.bottom - 60)
        )
        # Panneau qui encadre la grille
        grid_panel = pygame.Rect(
            GRID_X - 20,
            GRID_Y - 20,
            GRID_W + 40,
            GRID_H + 40
        )
        draw_rounded(self.screen, (26, 30, 40), grid_panel, 18)

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                rect = grid_to_px(r, c)
                draw_rounded(self.screen, (45, 50, 62), rect, 10)
                rm = self.manor.grid[r][c]
                if rm is None:
                    continue
                col = ROOM_COLORS.get(rm.definition.color, (110, 110, 110))
                inner = rect.inflate(-14, -14)
                draw_rounded(self.screen, col, inner, 12)
                text(self.screen, rm.definition.name, self.font_small, (20, 20, 20),
                     center=(inner.centerx, inner.top + 18))
                up, right, down, left = rm.placed_doors
                if up:
                    pygame.draw.rect(self.screen, OUTLINE, (inner.centerx - 10, inner.top - 2, 20, 8))
                if right:
                    pygame.draw.rect(self.screen, OUTLINE, (inner.right - 2, inner.centery - 10, 8, 20))
                if down:
                    pygame.draw.rect(self.screen, OUTLINE, (inner.centerx - 10, inner.bottom - 6, 20, 8))
                if left:
                    pygame.draw.rect(self.screen, OUTLINE, (inner.left - 6, inner.centery - 10, 8, 20))

        pr = grid_to_px(self.player.r, self.player.c)
        pygame.draw.circle(self.screen, ACCENT, pr.center, 14)
        off = {"up": (0, -20), "right": (20, 0), "down": (0, 20), "left": (-20, 0)}[self.player.dir]
        tip = (pr.centerx + off[0], pr.centery + off[1])
        pygame.draw.line(self.screen, ACCENT, pr.center, tip, 3)

        gr, gc = self.manor.goal
        goal_rect = grid_to_px(gr, gc)
        pygame.draw.rect(self.screen, SUCCESS, goal_rect.inflate(6, 6), 3, border_radius=10)

        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            panel = pygame.Rect(WIDTH // 2 - 320, HEIGHT // 2 - 120, 640, 240)
            draw_rounded(self.screen, PANEL, panel, 16)
            text(self.screen, self.game_over, self.font_big, TEXT, center=panel.center)

    def run(self):
        while True:
            self.handle_events()
            self.screen.fill(BG)
            self.draw_grid()
            if self.draw_ui.active:
                self.draw_ui.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Game().run()
