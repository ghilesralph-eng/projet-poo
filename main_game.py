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
"""

import sys
import os
import random
from typing import Dict, List, Optional, Tuple

import pygame

from inventory.inventory import Inventory
from rooms.room_data import RoomDef, ROOM_CATALOGUE
from player import Player
from manor import Manor, GRID_ROWS, GRID_COLS, OPPOSITE_DIR, DOOR_INDEX

# ==========================
# Constantes & couleurs
# ==========================
WIDTH, HEIGHT = 1200, 800
FPS = 60

HEADER_H = 96           # bandeau du haut
MARGIN   = 10           # marge entre les cases
TILE     = 64           # taille d’une case

# Taille de la grille (utilise GRID_ROWS / GRID_COLS importés de manor)
GRID_W = GRID_COLS * TILE + (GRID_COLS + 1) * MARGIN
GRID_H = GRID_ROWS * TILE + (GRID_ROWS + 1) * MARGIN

# Position de la grille (gauche)
GRID_X = 40
GRID_Y = HEADER_H + 24  # sous le header

BG      = (18, 20, 26)
PANEL   = (30, 34, 44)
TEXT    = (235, 240, 255)
SUBTLE  = (160, 170, 190)
ACCENT  = (120, 180, 255)
DANGER  = (230, 80, 80)
SUCCESS = (90, 200, 140)
OUTLINE = (240, 245, 255)

ROOM_COLORS = {
    "blue":   (70, 110, 170),
    "yellow": (220, 190, 60),
    "green":  (80, 160, 110),
    "purple": (150, 100, 170),
    "orange": (220, 140, 80),
    "red":    (200, 80, 80),
}

# Directions (r, c)
DIRS: Dict[str, Tuple[int, int]] = {
    "up":    (-1, 0),
    "down":  (1, 0),
    "left":  (0, -1),
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


def get_room_def(room_obj):
    """Compat : Room wrapper ou RoomDef direct."""
    if hasattr(room_obj, "definition"):
        return room_obj.definition
    return room_obj


# ==========================
# Effets de pièces
# ==========================

def apply_room_effect(inv: Inventory, rd: RoomDef):
    eid = rd.effect_id
    if not eid:
        return

    value = rd.effect_value
    if isinstance(value, tuple):
        import random
        value = random.randint(value[0], value[1])

    if eid == "add_step":
        inv.add_steps(value)
    elif eid == "add_coin":
        inv.add_coins(value)
    elif eid == "add_gem":
        inv.add_gems(value)
    elif eid == "add_key":
        inv.add_keys(value)
    elif eid == "lockpick":
        inv.add_permanent("lockpick")
    elif eid == "metaldetector":
        inv.add_permanent("metal_detector")

# ==========================
# room_loot function
#=========================

def loot_room(inv: Inventory, room):
    if room.looted:
        return []

    rd = room.definition
    import random
    messages = []

    for obj_name, (mn, mx) in rd.objects_in_room.items():
        qty = random.randint(mn, mx)
        if qty <= 0:
            continue

        if obj_name in ("apple", "banana", "cupcake", "orange"):
            inv.add_steps(2 * qty)
            messages.append(f"+{2 * qty} pas (nourriture)")
        elif obj_name == "key":
            inv.add_keys(qty)
            messages.append(f"+{qty} clé(s)")
        elif obj_name == "gem":
            inv.add_gems(qty)
            messages.append(f"+{qty} gemme(s)")
        elif obj_name == "coin":
            inv.add_coins(qty)
            messages.append(f"+{qty} pièce(s)")
        elif obj_name == "dice":
            inv.add_dice(qty)
            messages.append(f"+{qty} dé(s)")
        elif obj_name == "lockpick":
            inv.add_permanent("lockpick")
            messages.append("Kit de crochetage obtenu")
        elif obj_name == "metaldetector":
            inv.add_permanent("metal_detector")
            messages.append("Détecteur de métal obtenu")
        elif obj_name == "paw":
            inv.add_permanent("rabbit_foot")
            messages.append("Patte de lapin obtenue")

    room.looted = True
    return messages



# ==========================
# UI de tirage
# ==========================

class DrawUI:
    def __init__(self, font, font_small, game: "Game"):
        self.font = font
        self.font_small = font_small
        self.game = game
        self.active = False
        self.candidates: List[RoomDef] = []
        self.selected = 0
        self.pos: Tuple[int, int] = (0, 0)   # (row, col)
        self.from_dir: str = "up"

        # nouveaux : orientation et portes pour chaque candidat
        self.orientations: List[int] = []
        self.doors_list: List[Tuple[bool, bool, bool, bool]] = []

    def open(self, candidates: List[RoomDef], pos: Tuple[int, int], from_dir: str):
        self.active = True
        self.candidates = candidates
        self.selected = 0
        self.pos = pos
        self.from_dir = from_dir
        self._compute_orientations()


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
                    r, c = self.pos
                    self.candidates = manor.draw_candidates(r, c, self.from_dir)
                    self.selected = 0
                    self._compute_orientations()

            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                choice = self.candidates[self.selected]
                cost = choice.gem_cost if not isinstance(choice.gem_cost, tuple) else choice.gem_cost[0]
                if not inventory.use_gems(cost):
                    return None
                r, c = self.pos
                orientation = self.orientations[self.selected]
                doors = self.doors_list[self.selected]
                manor.place_room(choice, r, c, self.from_dir, orientation=orientation, doors=doors)
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
        base_y = panel.top + 90

        for i, rd in enumerate(self.candidates):
            rect = pygame.Rect(start_x + i * (card_w + gap), base_y, card_w, 360)
            sel = (i == self.selected)
            draw_rounded(screen, (60, 65, 80) if not sel else (80, 90, 110), rect, 18)

            # bandeau couleur
            color = ROOM_COLORS.get(getattr(rd, "color", "blue"), (120, 120, 120))
            head = rect.copy()
            head.height = 56
            draw_rounded(screen, color, head, 18)
            text(screen, rd.name, self.font, (20, 20, 20), center=head.center)

            # IMAGE au centre de la carte
            img = self.game.room_images.get(rd.name)
            if img is not None:
                size = int(card_w * 0.75)
                orient = self.orientations[i] if i < len(self.orientations) else 0
                rotated = pygame.transform.rotate(img, -90 * orient)   # change sign if flipped
                thumb = pygame.transform.scale(rotated, (size, size))
                thumb_rect = thumb.get_rect(center=(rect.centerx, rect.top + 160))
                screen.blit(thumb, thumb_rect)
                y2 = rect.top + 260
            else:
                y2 = rect.top + 80


            # infos texte
            text(screen, f"Couleur: {rd.color}", self.font_small, TEXT,
                 topleft=(rect.left + 16, y2)); y2 += 28
            text(screen, f"Rareté: {rd.rarity}", self.font_small, TEXT,
                 topleft=(rect.left + 16, y2)); y2 += 28
            text(screen, f"Coût gemmes: {rd.gem_cost}", self.font_small, TEXT,
                 topleft=(rect.left + 16, y2)); y2 += 28

            y2 += 8
            text(screen, "Portes:", self.font_small, SUBTLE,
                 topleft=(rect.left + 16, y2)); y2 += 24
            pr = ["↑", "→", "↓", "←"]
            doors = self.doors_list[i] if i < len(self.doors_list) else rd.doors
            s = " ".join([pr[j] if doors[j] else "·" for j in range(4)])
            text(screen, s, self.font, TEXT,
                 topleft=(rect.left + 16, y2)); y2 += 36

            if getattr(rd, "placement_condition", None) == "border_only":
                text(screen, "Placement: bordure", self.font_small, SUBTLE,
                     topleft=(rect.left + 16, y2)); y2 += 28

            effect = getattr(rd, "effect_on_enter", None)
            if effect:
                text(screen, f"Effet: {effect}", self.font_small, SUBTLE,
                     topleft=(rect.left + 16, y2)); y2 += 28
                
    def _compute_orientations(self):
        """Choisit une orientation/portes pour chaque candidat à la position courante."""
        self.orientations = []
        self.doors_list = []

        manor = self.game.manor
        r, c = self.pos
        entry_dir_name = OPPOSITE_DIR[self.from_dir]
        entry_idx = DOOR_INDEX[entry_dir_name]

        for rd in self.candidates:
            options = manor._valid_rotations_for(rd, r, c, entry_idx)
            if options:
                orientation, doors = random.choice(options)
            else:
                orientation, doors = 0, rd.doors
            self.orientations.append(orientation)
            self.doors_list.append(tuple(doors))




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

        # ---------- IMAGES DES ROOMS ----------
        # ---------- IMAGES DE ROOMS ----------
        # On charge une icône 64x64 environ pour chaque room
        self.room_images: Dict[str, pygame.Surface] = {}
        ICON_DIR = os.path.join("rooms", "icon")


        for rd in ROOM_CATALOGUE:
            # nom logique de la room
            name = rd.name

            # tes fichiers sont du type: "bedroom_icon.png", "antechamber_icon.png"
            base = name.lower().replace(" ", "_")
            filename = f"{base}_icon.png"
            path = os.path.join(ICON_DIR, filename)

            try:
                img = pygame.image.load(path).convert_alpha()
                self.room_images[name] = img
            except Exception as e:
                print(f"[WARN] pas d'image pour {name} ({path}) : {e}")

        # ---------- INVENTAIRE / MANOIR / JOUEUR ----------
        self.inventory = Inventory()
        self.manor = Manor()

        # Manor.start est (row, col)
        sr, sc = self.manor.start
        self.player = Player(sr, sc, self.inventory)

        self.message = (
            "ZQSD pour choisir, ESPACE pour valider. "
            "Objectif: atteindre l'Antechamber tout en haut."
        )
        self.draw_ui = DrawUI(self.font_big, self.font, self)
        self.game_over: Optional[str] = None

        # petit historique d'événements (loot, effets...)
        # chaque entrée = (texte, ttl_en_frames)
        self.event_log: List[Tuple[str, int]] = []


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
            room = self.manor.grid[r][c]
            rd = get_room_def(room)
            apply_room_effect(self.inventory, rd)
            msgs = loot_room(self.inventory, room)
            for m in msgs:
                self.push_event(f"{rd.name}: {m}")
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
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                if self.draw_ui.active:
                    placed = self.draw_ui.handle_event(e, self.inventory, self.manor)
                    if placed:
                        r, c, _ = placed
                        self.player.r, self.player.c = r, c
                        self.player.use_step()
                        room = self.manor.grid[r][c]
                        rd = get_room_def(room)
                        apply_room_effect(self.inventory, rd)
                        msgs = loot_room(self.inventory, room)
                        for m in msgs:
                            self.push_event(f"{rd.name}: {m}")
                        self.post_move_check()

                    continue

                if e.key in KEY_TO_DIR:
                    self.player.set_dir(KEY_TO_DIR[e.key])
                elif e.key == pygame.K_SPACE:
                    self.try_action()

    def draw_grid(self):
        # Bandeau haut (titre)
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

        # mise à jour de la durée de vie des messages d'événements
        new_log = []
        for msg, ttl in self.event_log:
            ttl -= 1
            if ttl > 0:
                new_log.append((msg, ttl))
        self.event_log = new_log



        draw_rounded(self.screen, PANEL, right_panel, 18)

        # Inventaire
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

        # Permanents
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
            
                # Historique récent de loot / effets
        log_y = right_panel.bottom - 140
        for msg, _ttl in reversed(self.event_log[-4:]):
            text(
                self.screen,
                msg,
                self.font_small,
                TEXT,
                topleft=(right_panel.x + 24, log_y)
            )
            log_y += 22

        # Message en bas du panneau droit
        text(
            self.screen,
            self.message,
            self.font_small, SUBTLE,
            topleft=(right_panel.x + 24, right_panel.bottom - 60)
        )

        # Panneau autour de la grille
        grid_panel = pygame.Rect(
            GRID_X - 20,
            GRID_Y - 20,
            GRID_W + 40,
            GRID_H + 40
        )
        draw_rounded(self.screen, (26, 30, 40), grid_panel, 18)

        # Grille + rooms
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                rect = grid_to_px(r, c)
                draw_rounded(self.screen, (45, 50, 62), rect, 10)

                rm = self.manor.grid[r][c]
                if rm is None:
                    continue

                # rm peut être soit un RoomDef soit un objet Room avec .definition
                rd = rm.definition if hasattr(rm, "definition") else rm

                col = ROOM_COLORS.get(getattr(rd, "color", "blue"), (110, 110, 110))
                inner = rect.inflate(-8, -8)
                draw_rounded(self.screen, col, inner, 12)

                # --- image de la room au centre ---
                img = self.room_images.get(rd.name)
                if img is not None:
                    orient = getattr(rm, "orientation", 0)
                    rotated = pygame.transform.rotate(img, -90 * orient)   # change sign if needed
                    target_w = inner.width - 4
                    target_h = inner.height - 4
                    thumb = pygame.transform.scale(rotated, (target_w, target_h))
                    img_rect = thumb.get_rect(center=inner.center)
                    self.screen.blit(thumb, img_rect)
                else:
                    # fallback texte si aucune image
                    text(
                        self.screen,
                        rd.name,
                        self.font_small,
                        (20, 20, 20),
                        center=inner.center,
                    )

        # Joueur
        # Joueur : surbrillance de la case courante
        pr = grid_to_px(self.player.r, self.player.c)

        # halo autour de la case
        highlight = pr.inflate(8, 8)
        pygame.draw.rect(self.screen, ACCENT, highlight, width=4, border_radius=14)

        # petit marqueur de direction sur le bord de la case
        dir_offsets = {
            "up":    (0, -pr.height // 2),
            "right": (pr.width // 2, 0),
            "down":  (0, pr.height // 2),
            "left":  (-pr.width // 2, 0),
        }
        off = dir_offsets[self.player.dir]
        center = pr.center
        tip = (center[0] + off[0] * 0.6, center[1] + off[1] * 0.6)
        pygame.draw.line(self.screen, ACCENT, center, tip, 3)


        # But
        gr, gc = self.manor.goal
        goal_rect = grid_to_px(gr, gc)
        pygame.draw.rect(self.screen, SUCCESS, goal_rect.inflate(6, 6), 3, border_radius=10)

        # Overlay fin de partie
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

    def push_event(self, msg: str, ttl: int = 240):
        """Ajoute un message temporaire (≈4s à 60 FPS)."""
        self.event_log.append((msg, ttl))



if __name__ == "__main__":
    Game().run()
