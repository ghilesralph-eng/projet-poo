# main.py

import pygame
import sys
from typing import Dict, Tuple

# Import your backend classes
from manor import Manor
from player import Player
from rooms.room_data import RoomDef

# --- Constants ---
# [PDF 2.1] Grid is 5x9
GRID_ROWS = 5
GRID_COLS = 9

# Screen dimensions
TILE_SIZE = 96
PADDING = 10
SCREEN_WIDTH = (GRID_COLS * TILE_SIZE) + ((GRID_COLS + 1) * PADDING)
SCREEN_HEIGHT = (GRID_ROWS * TILE_SIZE) + ((GRID_ROWS + 1) * PADDING) + 120 # Extra space for UI
UI_TOP = (GRID_ROWS * TILE_SIZE) + ((GRID_ROWS + 1) * PADDING)

# Colors
COLOR_BG = (20, 20, 30)
COLOR_GRID = (40, 40, 50)
COLOR_PLAYER = (50, 200, 255)
COLOR_TEXT = (230, 230, 230)
COLOR_RED = (200, 50, 50)
COLOR_GREEN = (50, 200, 50)
ROOM_COLORS = {
    "blue": (70, 110, 170),
    "yellow": (220, 190, 60),
    "green": (80, 160, 110),
    "purple": (150, 100, 170),
    "orange": (220, 140, 80),
    "red": (200, 80, 80),
}

# [PDF 2.5] Input mapping
KEY_TO_DIR: Dict[int, str] = {
    pygame.K_z: "up",
    pygame.K_s: "down",
    pygame.K_q: "left",
    pygame.K_d: "right"
}
# Helper to map directions to (dx, dy) changes
DIRECTIONS: Dict[str, Tuple[int, int]] = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0)
}

class Game:
    """
    Manages the main pygame loop, event handling, and rendering.
    """
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Blue Prince POO Project")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)
        self.font_big = pygame.font.SysFont("Arial", 24, bold=True)
        
        self.manor = Manor()
        self.running = True
        
        # 'roaming' = moving on grid
        # 'drafting' = choosing a room
        self.game_state = 'roaming'
        
        # Player's intended direction
        self.selected_dir = "up" 
        
        # For 'drafting' state
        self.draft_candidates: list[RoomDef] = []
        self.draft_target_pos: Tuple[int, int] = (0, 0)
        
        self.message = "Use ZQSD to choose a direction, Espace to open/move."

    def run(self):
        """Starts the main game loop."""
        while self.running:
            self._handle_events()
            self._update()
            self._draw()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

    def _handle_events(self):
        """Handles all user input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                
                if self.game_state == 'roaming':
                    self._handle_roaming_input(event.key)
                elif self.game_state == 'drafting':
                    self._handle_drafting_input(event.key)

    def _handle_roaming_input(self, key):
        """Handles input for player movement."""
        if key in KEY_TO_DIR:
            self.selected_dir = KEY_TO_DIR[key]
            self.message = f"Direction selected: {self.selected_dir.upper()}"
        
        if key == pygame.K_SPACE:
            self._try_action(self.selected_dir) #

    def _handle_drafting_input(self, key):
        """Handles input for choosing a room."""
        choice = -1
        if key == pygame.K_1:
            choice = 0
        elif key == pygame.K_2:
            choice = 1
        elif key == pygame.K_3:
            choice = 2
        
        if choice != -1 and choice < len(self.draft_candidates):
            room_to_place = self.draft_candidates[choice]
            
            # --- Pay Gem Cost ---
            cost = self.manor._get_gem_cost(room_to_place)
            if not self.manor.player.use_gems(cost): # [cite: 365]
                self.message = f"Not enough gems! Need {cost}."
                return False

            # --- Place Room ---
            x, y = self.draft_target_pos
            self.manor.place_room(room_to_place, x, y)
            
            # --- Move Player into New Room ---
            self.manor.player.x = x
            self.manor.player.y = y
            self.manor.player.use_step() # [cite: 363]
            
            self.game_state = 'roaming'
            self.message = f"Placed {room_to_place.name}. Use ZQSD to move."
            self._check_game_over()

    def _try_action(self, direction: str):
        """
        Handles the logic when the player presses 'Espace'.
        Implements PDF 2.5 logic.
        """
        player = self.manor.player
        dx, dy = DIRECTIONS[direction]
        target_x, target_y = player.x + dx, player.y + dy

        # 1. Check for valid grid position (not a wall)
        if not (0 <= target_x < GRID_COLS and 0 <= target_y < GRID_ROWS):
            self.message = "Cannot move outside the manor." [cite_start]# [cite: 434]
            return

        # 2. Check if current room has a door in that direction
        current_room = self.manor.get_room(player.x, player.y)
        if not current_room.doors[self.manor.DOOR_INDEX[direction]]:
            self.message = "There is no door in that direction."
            return

        # 3. Check what's in the target cell
        target_room = self.manor.get_room(target_x, target_y)

        if target_room:
            # --- Case 1: Moving into an existing room ---
            # [PDF 2.5] "se déplace dans cette nouvelle pièce"
            player.move(dx, dy)
            player.use_step() # [cite: 363]
            self.message = f"Moved to {target_room.name}. Steps: {player.inventory.consumables.data['step']}"
            self._check_game_over()
        else:
            # --- Case 2: Opening a new door ---
            # [PDF 2.6] "essaye d'ouvrir la porte"
            lock_level = self.manor.get_lock_level(target_y) # [cite: 453]
            
            can_open = False
            # [PDF 2.6] Lock level 1 can be opened with lockpick
            if lock_level == 1 and player.has_permanent("lockpick"): # [cite: 441]
                can_open = True
            elif player.inventory.consumables.data['keys'] >= lock_level:
                # Player has enough keys
                player.use_keys(lock_level) # [cite: 440]
                can_open = True
            
            if not can_open:
                self.message = f"Door is locked (Level {lock_level})! Need {lock_level} key(s)."
                return

            # --- Show Draft Screen ---
            self.draft_candidates = self.manor.draw_candidates(target_x, target_y, direction) # [cite: 443]
            
            if not self.draft_candidates:
                self.message = "No valid rooms can be placed here! (Deck might be empty)"
                return

            self.game_state = 'drafting'
            self.draft_target_pos = (target_x, target_y)
            self.message = "Choose a room: [1] [2] [3]"

    def _check_game_over(self):
        """Checks for win or lose conditions."""
        # [PDF 2.1] Lose: 0 steps
        if self.manor.player.inventory.consumables.data['step'] <= 0:
            self.message = "You ran out of steps! Game Over."
            self.game_state = 'game_over'
            self.running = False # Or set a flag to show a "Game Over" screen
        
        # [PDF 2.5] Win: Reach Antechamber
        if (self.manor.player.x, self.manor.player.y) == self.manor.GOAL_POS:
            self.message = "You reached the Antechamber! You win!"
            self.game_state = 'game_over'
            self.running = False

    def _update(self):
        """Handle non-event-based game logic (e.g., animations)."""
        pass # Not needed for now

    def _draw(self):
        """Renders the entire game state to the screen."""
        self.screen.fill(COLOR_BG)
        
        # --- Draw Grid ---
        for y in range(GRID_ROWS):
            for x in range(GRID_COLS):
                rect = self._get_grid_rect(x, y)
                room = self.manor.get_room(x, y)
                
                if room:
                    color = ROOM_COLORS.get(room.color, (100, 100, 100))
                    pygame.draw.rect(self.screen, color, rect)
                    
                    # Draw room name
                    text = self.font.render(room.name, True, COLOR_TEXT)
                    self.screen.blit(text, text.get_rect(center=rect.center))
                else:
                    pygame.draw.rect(self.screen, COLOR_GRID, rect)

        # --- Draw Player ---
        player_rect = self._get_grid_rect(self.manor.player.x, self.manor.player.y)
        pygame.draw.rect(self.screen, COLOR_PLAYER, player_rect.inflate(-TILE_SIZE*0.7, -TILE_SIZE*0.7))
        
        # --- Draw Selected Direction ---
        if self.game_state == 'roaming':
            dx, dy = DIRECTIONS[self.selected_dir]
            target_rect = self._get_grid_rect(self.manor.player.x + dx, self.manor.player.y + dy)
            pygame.draw.rect(self.screen, COLOR_PLAYER, target_rect, 3) # 3 = border width

        # --- Draw UI Panel ---
        self._draw_ui()

        # --- Draw Drafting Screen (if active) ---
        if self.game_state == 'drafting':
            self._draw_draft_ui()

        pygame.display.flip()

    def _get_grid_rect(self, x: int, y: int) -> pygame.Rect:
        """Helper to get the pixel Rect for a grid coordinate."""
        px = (x * TILE_SIZE) + ((x + 1) * PADDING)
        py = (y * TILE_SIZE) + ((y + 1) * PADDING)
        return pygame.Rect(px, py, TILE_SIZE, TILE_SIZE)

    def _draw_ui(self):
        """Draws the bottom UI panel with inventory and messages."""
        ui_rect = pygame.Rect(0, UI_TOP, SCREEN_WIDTH, 120)
        pygame.draw.rect(self.screen, (10, 10, 15), ui_rect)
        
        # Draw Message
        msg_text = self.font_big.render(self.message, True, COLOR_GREEN)
        self.screen.blit(msg_text, (PADDING, UI_TOP + PADDING))
        
        # Draw Inventory
        inv = self.manor.player.inventory
        inv_str = f"Steps: {inv.consumables.data['step']} | Coins: {inv.consumables.data['coins']} | Gems: {inv.consumables.data['gems']} | Keys: {inv.consumables.data['keys']} | Dice: {inv.consumables.data['dice']}"
        inv_text = self.font.render(inv_str, True, COLOR_TEXT)
        self.screen.blit(inv_text, (PADDING, UI_TOP + PADDING + 40))
        
        # Draw Permanent Items
        perms = "Permanents: " + ", ".join(inv.permanants.data) if inv.permanants.data else "Permanents: None"
        perm_text = self.font.render(perms, True, COLOR_TEXT)
        self.screen.blit(perm_text, (PADDING, UI_TOP + PADDING + 65))

    def _draw_draft_ui(self):
        """Draws the "Choose a room" UI over the screen."""
        # Dark overlay
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Draw the 3 candidates
        card_width = SCREEN_WIDTH // 4
        card_height = SCREEN_HEIGHT // 2
        
        for i, room in enumerate(self.draft_candidates):
            x = (i * card_width) + (i * PADDING) + (SCREEN_WIDTH // 8)
            y = SCREEN_HEIGHT // 4
            rect = pygame.Rect(x, y, card_width, card_height)
            
            # Card background
            color = ROOM_COLORS.get(room.color, (100, 100, 100))
            pygame.draw.rect(self.screen, color, rect, border_radius=10)
            
            # Title
            title_text = self.font_big.render(f"[{i+1}] {room.name}", True, COLOR_TEXT)
            self.screen.blit(title_text, (rect.x + 20, rect.y + 20))
            
            # Cost
            cost = self.manor._get_gem_cost(room)
            cost_text = self.font.render(f"Cost: {cost} Gems", True, COLOR_TEXT)
            self.screen.blit(cost_text, (rect.x + 20, rect.y + 60))
            
            # Rarity
            rarity = room.rarity
            rarity_text = self.font.render(f"Rarity: {rarity}", True, COLOR_TEXT)
            self.screen.blit(rarity_text, (rect.x + 20, rect.y + 85))


if __name__ == "__main__":
    game = Game()
    game.run()