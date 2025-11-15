# game.py
import pygame
from graphics import Graphics, GRID_COLS, GRID_ROWS

class Game:
    def __init__(self):
        # Interface graphique
        self.gfx = Graphics()

        # ÉTAT DU JEU
        self.inventory = {"Steps": 76, "Coins": 0, "Gems": 2, "Keys": 1, "Dice": 1}
        self.STEPS_KEY = "Steps"

        # Grille logique (même dimensions que dans graphics)
        self.placed = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

        # Position joueur
        self.cur_c, self.cur_r = 2, 8

        # Cartes
        self.room_names  = ["Closet", "Aquarium", "Bedroom"]
        self.room_colors = [(52, 140, 210), (70, 170, 120), (120, 100, 160)]
        self.room_sub    = ["", "", "Gain 2 steps every time you visit this room."]

        self.focused    = 0
        self.card_hover = [0.0, 0.0, 0.0]

        # Droit de bouger 1 case après choix de chambre
        self.can_move  = False
        self.sel_cool  = 0
        self.move_cool = 0
        self.running   = True

    # -------- LOGIQUE : placer une salle ----------
    def place_current_cell(self):
        self.placed[self.cur_r][self.cur_c] = self.focused

    # -------- LOGIQUE : gestion événements ----------
    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.running = False
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.place_current_cell()
                    self.can_move = True
                elif e.key in (pygame.K_1, pygame.K_KP1):
                    self.focused = 0
                elif e.key in (pygame.K_2, pygame.K_KP2):
                    self.focused = 1
                elif e.key in (pygame.K_3, pygame.K_KP3):
                    self.focused = 2
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                m = pygame.mouse.get_pos()
                # clic cartes
                for i, r in enumerate(self.gfx.CARD_RECTS):
                    if r.collidepoint(m):
                        self.focused = i
                # clic bouton Roll
                if (self.gfx.DICE_BTN
                        and self.gfx.DICE_BTN.collidepoint(m)
                        and self.inventory["Dice"] > 0):
                    self.inventory["Dice"] -= 1  # placeholder reroll

    # -------- LOGIQUE : déplacement + steps ----------
    def update_game_state(self, dt):
        keys = pygame.key.get_pressed()

        # Déplacement : UNE case après choix de chambre
        if self.can_move and self.move_cool <= 0:
            moved = False
            old_c, old_r = self.cur_c, self.cur_r

            if keys[pygame.K_q] and self.cur_c > 0:
                self.cur_c -= 1; moved = True
            elif keys[pygame.K_d] and self.cur_c < GRID_COLS - 1:
                self.cur_c += 1; moved = True
            elif keys[pygame.K_z] and self.cur_r > 0:
                self.cur_r -= 1; moved = True
            elif keys[pygame.K_s] and self.cur_r < GRID_ROWS - 1:
                self.cur_r += 1; moved = True

            if moved and (self.cur_c != old_c or self.cur_r != old_r):
                self.move_cool = 120
                # Ici tu décrémentes ou incrémentes Steps selon la règle voulue
                self.inventory[self.STEPS_KEY] = self.inventory.get(self.STEPS_KEY, 0) + 1
                self.can_move = False
        elif self.move_cool > 0:
            self.move_cool -= dt

        # Navigation cartes ← →
        if self.sel_cool <= 0:
            if keys[pygame.K_LEFT]:
                if self.focused > 0:
                    self.focused -= 1
                self.sel_cool = 140
            elif keys[pygame.K_RIGHT]:
                if self.focused < 2:
                    self.focused += 1
                self.sel_cool = 140
        else:
            self.sel_cool -= dt

    # -------- BOUCLE PRINCIPALE ----------
    def run(self):
        while self.running:
            dt = self.gfx.clock.tick(self.gfx.FPS)
            self.handle_events()
            self.update_game_state(dt)
            self.gfx.draw_all(self)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
