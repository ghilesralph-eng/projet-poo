"""
Blue Prince – Neon Mansion UI (polish edition)
---------------------------------------------
Visual upgrade of the previous scaffold – same controls & data flow, but with a
cooler theme and micro-animations:
• Midnight gradient background + faint grid
• Glassmorphism right HUD panel with icons
• Neon-glow tiles by color family (blue/orange/green/purple/yellow/red)
• Pulsing cursor with smooth lerp movement
• Door pips (N/E/S/W) with lock color hints
• Room picker overlay redesigned as neon cards with selection glow

No external assets, pure pygame drawing so it runs out-of-the-box.

Controls: ZQSD/Arrows to move cursor • Hold direction + SPACE to open • A/D or ←/→
select a card • ENTER confirm • ESC cancel/quit
"""
import sys
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

import pygame as pg

# ----------------------------- CONFIG ----------------------------------
GRID_ROWS = 5
GRID_COLS = 9
CELL_SIZE = 92
GRID_MARGIN = 10
LEFT_MARGIN = 48
TOP_MARGIN = 54

PANEL_W = 280
SCREEN_W = LEFT_MARGIN + GRID_COLS*CELL_SIZE + (GRID_COLS-1)*GRID_MARGIN + PANEL_W + 60
SCREEN_H = TOP_MARGIN + GRID_ROWS*CELL_SIZE + (GRID_ROWS-1)*GRID_MARGIN + 100
FPS = 60

# ----------------------------- THEME -----------------------------------
class Theme:
    BG_TOP = (10, 14, 26)
    BG_BOT = (16, 8, 32)
    GRID_LINE = (38, 46, 70)
    TEXT = (230, 232, 240)
    SUBTLE = (170, 175, 190)
    PANEL = (255, 255, 255, 34)   # translucent glass
    PANEL_BORDER = (180, 200, 255, 90)
    PANEL_SHADOW = (0, 0, 0, 120)

    COLORS = {
        'blue':   ((60,140,255), (20,80,220)),
        'orange': ((255,170,80), (230,120,30)),
        'green':  ((120,230,160), (35,170,95)),
        'purple': ((200,140,255), (140,100,210)),
        'yellow': ((255,230,120), (230,195,60)),
        'red':    ((255,110,110), (220,70,70)),
        'empty':  ((80,90,110), (55,60,78)),
    }

    LOCKS = {
        0: (120, 220, 255),  # cyan (open)
        1: (255, 210, 100),  # bronze
        2: (190, 210, 230),  # silver
        3: (255, 180, 210),  # pink/gold-ish (hard)
    }

# Fonts declared after pg.init
FONT_S = 15
FONT_M = 20
FONT_L = 28

# --------------------------- DATA MODELS --------------------------------
DIRS = { 'N': (-1,0), 'S': (1,0), 'W': (0,-1), 'E': (0,1) }

@dataclass
class Room:
    name: str
    color: str
    doors: Dict[str, bool]
    gem_cost: int = 0
    rarity: int = 0
    effect: Optional[str] = None
    locks: Dict[str, int] = None  # 0..3

    def color_pair(self):
        return Theme.COLORS.get(self.color, Theme.COLORS['empty'])

@dataclass
class Inventory:
    steps: int = 70
    coins: int = 0
    gems: int = 2
    keys: int = 0
    dice: int = 0

# ---------------------------- GAME STATE --------------------------------
class MansionGrid:
    def __init__(self, rows:int, cols:int):
        self.rows = rows
        self.cols = cols
        self.cells: List[List[Optional[Room]]] = [[None for _ in range(cols)] for _ in range(rows)]
        self.cursor = (rows-1, cols//2)
        self.place_room(self.cursor, Room('Entrance Hall','blue', {'N':True,'S':False,'E':True,'W':True}, locks={'N':0,'E':0,'W':0,'S':3}))

    def in_bounds(self, r,c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def get(self, rc:Tuple[int,int]) -> Optional[Room]:
        r,c = rc
        return self.cells[r][c]

    def place_room(self, rc:Tuple[int,int], room:Room):
        r,c = rc
        self.cells[r][c] = room

    def neighbor(self, rc:Tuple[int,int], direction:str) -> Optional[Tuple[int,int]]:
        dr,dc = DIRS[direction]
        nr, nc = rc[0]+dr, rc[1]+dc
        if self.in_bounds(nr,nc):
            return (nr,nc)
        return None

# --------------------------- UI UTILITIES --------------------------------
class Ui:
    def __init__(self):
        pg.init()
        pg.display.set_caption('Blue Prince – Neon Mansion')
        self.screen = pg.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pg.time.Clock()
        self.font_s = pg.font.SysFont('quicksand,arial', FONT_S)
        self.font_m = pg.font.SysFont('quicksand,arial', FONT_M, bold=True)
        self.font_l = pg.font.SysFont('quicksand,arial', FONT_L, bold=True)

    def text(self, surf, txt, pos, size='m', color=Theme.TEXT):
        f = {'s':self.font_s,'m':self.font_m,'l':self.font_l}[size]
        img = f.render(txt, True, color)
        surf.blit(img, pos)

    def gradient_v(self, surf, rect, top, bot):
        x,y,w,h = rect
        for i in range(h):
            t = i/max(1,h-1)
            c = (int(top[0]*(1-t)+bot[0]*t), int(top[1]*(1-t)+bot[1]*t), int(top[2]*(1-t)+bot[2]*t))
            pg.draw.line(surf, c, (x, y+i), (x+w, y+i))

    def rounded(self, surf, rect, color, radius=12, border=0, border_color=(255,255,255)):
        pg.draw.rect(surf, color, rect, border_radius=radius)
        if border:
            pg.draw.rect(surf, border_color, rect, width=border, border_radius=radius)

    def glow_rect(self, surf, rect, color, strength=6):
        x,y,w,h = rect
        for i in range(strength,0,-1):
            a = max(10, int(180*(i/strength)))
            r = pg.Rect(x-i, y-i, w+2*i, h+2*i)
            pg.draw.rect(surf, (*color, a), r, border_radius=12)

# ------------------------ ROOM SELECTION OVERLAY -------------------------
class RoomPicker:
    def __init__(self):
        self.active = False
        self.choices: List[Room] = []
        self.sel_idx = 0
        self.target_cell: Optional[Tuple[int,int]] = None

    def open(self, choices:List[Room], target_cell:Tuple[int,int]):
        self.active = True
        self.choices = choices
        self.sel_idx = 0
        self.target_cell = target_cell

    def close(self):
        self.active = False
        self.choices = []
        self.target_cell = None

    def draw(self, ui:Ui):
        if not self.active: return
        overlay = pg.Surface((SCREEN_W, SCREEN_H), pg.SRCALPHA)
        overlay.fill((0,0,0,170)); ui.screen.blit(overlay, (0,0))

        panel_w, panel_h = 880, 280
        panel_x = (SCREEN_W - panel_w)//2
        panel_y = 60
        # Glass panel
        panel = pg.Surface((panel_w, panel_h), pg.SRCALPHA)
        pg.draw.rect(panel, Theme.PANEL_SHADOW, (8,10,panel_w-16,panel_h-10), border_radius=18)
        pg.draw.rect(panel, Theme.PANEL, (0,0,panel_w,panel_h), border_radius=18)
        pg.draw.rect(panel, Theme.PANEL_BORDER, (0,0,panel_w,panel_h), width=2, border_radius=18)
        ui.screen.blit(panel, (panel_x, panel_y))
        ui.text(ui.screen, 'Choose a room', (panel_x+22, panel_y+16), 'm')
        ui.text(ui.screen, '←/→ or A/D to select • ENTER confirm • ESC cancel', (panel_x+22, panel_y+46), 's', Theme.SUBTLE)

        # Cards
        card_w, card_h = 250, 180
        gap = 65
        start_x = panel_x + 40
        y = panel_y + 74
        for i, room in enumerate(self.choices):
            x = start_x + i*(card_w + gap)
            r = pg.Rect(x, y, card_w, card_h)
            c1,c2 = room.color_pair()
            ui.gradient_v(ui.screen, r, c1, c2)
            border = 4 if i==self.sel_idx else 2
            ui.rounded(ui.screen, r, (0,0,0,0), radius=14, border=border, border_color=(240,240,255))
            if i==self.sel_idx:
                ui.glow_rect(ui.screen, r, c1, strength=8)
            ui.text(ui.screen, room.name, (x+14, y+12), 'm')
            doors = ''.join([d for d,ok in room.doors.items() if ok]) or '—'
            ui.text(ui.screen, f'Doors: {doors}', (x+14, y+56), 's', Theme.TEXT)
            ui.text(ui.screen, f'Gems: {room.gem_cost}  •  Rarity: {room.rarity}/3', (x+14, y+80), 's', Theme.TEXT)
            if room.effect:
                ui.text(ui.screen, f'Effect: {room.effect}', (x+14, y+104), 's', Theme.TEXT)

# ----------------------------- MAIN GAME ---------------------------------
class Game:
    def __init__(self):
        self.ui = Ui()
        self.grid = MansionGrid(GRID_ROWS, GRID_COLS)
        self.inv = Inventory()
        self.picker = RoomPicker()
        self.message = ''
        # Smooth cursor animation
        self.cursor_px = self.cell_to_px(self.grid.cursor)

    # ---------------- MOCK SYSTEMS (replace with real logic) -------------
    def can_move(self, direction:str) -> bool:
        cur = self.grid.cursor
        room = self.grid.get(cur)
        if not room or not room.doors.get(direction, False):
            return False
        nb = self.grid.neighbor(cur, direction)
        return nb is not None

    def open_door(self, direction:str):
        cur = self.grid.cursor
        nb = self.grid.neighbor(cur, direction)
        if nb is None:
            self.message = 'Wall – cannot open'; return
        if self.grid.get(nb) is not None:
            self.grid.cursor = nb
            self.inv.steps = max(0, self.inv.steps - 1)
            self.message = 'Moved.'; return
        choices = self.mock_draw_three_rooms(direction)
        self.picker.open(choices, nb)

    def mock_draw_three_rooms(self, direction:str) -> List[Room]:
        base = [
            Room('Corridor','orange', {'N':True,'S':True,'E':True,'W':True}, gem_cost=0, rarity=0, locks={'N':0,'S':0,'E':0,'W':0}),
            Room('Bedroom','purple', {'N':True,'S':False,'E':True,'W':False}, gem_cost=random.choice([0,1]), rarity=1, effect='+5 steps', locks={'N':1,'E':0,'S':2,'W':2}),
            Room('Veranda','green', {'N':True,'S':True,'E':False,'W':False}, gem_cost=2, rarity=2, effect='boost green draws', locks={'N':0,'S':1,'E':3,'W':3}),
            Room('Vault','blue', {'N':False,'S':True,'E':False,'W':False}, gem_cost=3, rarity=3, locks={'S':2,'N':3,'E':3,'W':3}),
            Room('Lavatory','blue', {'N':False,'S':True,'E':True,'W':False}, gem_cost=0, rarity=0, locks={'S':0,'E':0,'N':3,'W':3}),
            Room('Chapel','yellow', {'N':True,'S':True,'E':False,'W':False}, gem_cost=1, rarity=1, effect='trade coins', locks={'N':1,'S':0,'E':3,'W':3}),
            Room('Danger Room','red', {'N':True,'S':False,'E':False,'W':True}, gem_cost=0, rarity=1, effect='-3 steps', locks={'N':2,'W':1,'S':3,'E':3}),
        ]
        random.shuffle(base)
        picks = base[:3]
        if all(r.gem_cost>0 for r in picks):
            picks[0].gem_cost = 0
        need = {'N':'S','S':'N','E':'W','W':'E'}[direction]
        for r in picks:
            r.doors[need] = True
            if r.locks is None: r.locks = {}
            r.locks[need] = 0
        return picks

    def place_room_from_choice(self, room:Room, cell:Tuple[int,int]):
        if room.gem_cost > self.inv.gems:
            self.message = 'Not enough gems.'; return False
        self.inv.gems -= room.gem_cost
        self.grid.place_room(cell, room)
        self.grid.cursor = cell
        self.inv.steps = max(0, self.inv.steps - 1)
        self.message = f'Placed {room.name}.'
        return True

    # -------------------------- DRAWING LAYERS ---------------------------
    def cell_to_px(self, rc:Tuple[int,int]) -> Tuple[int,int]:
        r,c = rc
        x0 = LEFT_MARGIN
        y0 = TOP_MARGIN
        x = x0 + c*(CELL_SIZE+GRID_MARGIN)
        y = y0 + r*(CELL_SIZE+GRID_MARGIN)
        return (x,y)

    def draw_background(self):
        self.ui.gradient_v(self.ui.screen, (0,0,SCREEN_W,SCREEN_H), Theme.BG_TOP, Theme.BG_BOT)
        # subtle grid behind content
        for i in range(0, SCREEN_W, 32):
            pg.draw.line(self.ui.screen, Theme.GRID_LINE, (i,0), (i,SCREEN_H))
        for j in range(0, SCREEN_H, 32):
            pg.draw.line(self.ui.screen, Theme.GRID_LINE, (0,j), (SCREEN_W,j))

    def draw_panel(self):
        panel_x = SCREEN_W - PANEL_W - 30
        panel_y = 28
        panel = pg.Surface((PANEL_W, SCREEN_H-56), pg.SRCALPHA)
        pg.draw.rect(panel, Theme.PANEL, (0,0,PANEL_W,SCREEN_H-56), border_radius=18)
        pg.draw.rect(panel, Theme.PANEL_BORDER, (0,0,PANEL_W,SCREEN_H-56), width=2, border_radius=18)
        self.ui.screen.blit(panel, (panel_x, panel_y))
        self.ui.text(self.ui.screen, 'Inventory', (panel_x+18, panel_y+16), 'l')

        x = panel_x + 22
        y = panel_y + 60
        line = 34
        items = [
            ('Steps', self.inv.steps, '👣'),
            ('Coins', self.inv.coins, '🪙'),
            ('Gems', self.inv.gems, '💎'),
            ('Keys', self.inv.keys, '🔑'),
            ('Dice', self.inv.dice, '🎲'),
        ]
        for label, val, icon in items:
            self.ui.text(self.ui.screen, f'{icon}  {label}', (x, y), 'm')
            self.ui.text(self.ui.screen, str(val), (x+170, y), 'm')
            y += line

        y += 8
        self.ui.text(self.ui.screen, 'Controls', (x, y), 'm', Theme.SUBTLE)
        y += 26
        for h in ['Move: ZQSD / Arrows','Open: hold dir + SPACE','Pick: A/D or ←/→','Confirm: ENTER','Quit: ESC']:
            self.ui.text(self.ui.screen, h, (x, y), 's', Theme.SUBTLE)
            y += 18
        if self.message:
            self.ui.text(self.ui.screen, self.message, (x, y+6), 's', (255,110,140))

    def draw_grid(self, t):
        # tiles
        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                x,y = self.cell_to_px((r,c))
                rect = pg.Rect(x, y, CELL_SIZE, CELL_SIZE)
                room = self.grid.cells[r][c]
                c1,c2 = Theme.COLORS['empty'] if room is None else room.color_pair()
                self.ui.gradient_v(self.ui.screen, rect, c1, c2)
                self.ui.rounded(self.ui.screen, rect, (0,0,0,0), radius=12, border=2, border_color=(220,230,255))

                if room is not None:
                    # name
                    name = room.name if len(room.name)<=14 else room.name[:12]+'…'
                    self.ui.text(self.ui.screen, name, (x+8, y+8), 's')
                    # door ticks + lock hue
                    for d,(dr,dc) in DIRS.items():
                        if room.doors.get(d):
                            lx, ly = x + (CELL_SIZE//2), y + (CELL_SIZE//2)
                            if d=='N': px,py = x+CELL_SIZE//2-6, y-3
                            if d=='S': px,py = x+CELL_SIZE//2-6, y+CELL_SIZE-1
                            if d=='W': px,py = x-3, y+CELL_SIZE//2-6
                            if d=='E': px,py = x+CELL_SIZE-1, y+CELL_SIZE//2-6
                            pg.draw.rect(self.ui.screen, (245,245,255), (px,py,12,4), border_radius=2)
                            lv = (room.locks or {}).get(d,0)
                            col = Theme.LOCKS.get(lv, (200,200,220))
                            pg.draw.rect(self.ui.screen, col, (px,py,12,4), width=2, border_radius=2)

        # pulsing cursor (neon)
        target = self.cell_to_px(self.grid.cursor)
        # lerp position
        cx = self.cursor_px[0] + (target[0]-self.cursor_px[0])*0.18
        cy = self.cursor_px[1] + (target[1]-self.cursor_px[1])*0.18
        self.cursor_px = (cx, cy)
        pulse = 4 + int(3*(0.5+0.5*pg.math.sin(t*3.14)))
        glow_col = (120, 200, 255)
        r = pg.Rect(int(cx)-3, int(cy)-3, CELL_SIZE+6, CELL_SIZE+6)
        self.ui.glow_rect(self.ui.screen, r, glow_col, strength=pulse)
        pg.draw.rect(self.ui.screen, (240,250,255), r, width=3, border_radius=14)

    def draw_room_title(self):
        room = self.grid.get(self.grid.cursor)
        if room:
            self.ui.text(self.ui.screen, room.name, (LEFT_MARGIN, TOP_MARGIN + GRID_ROWS*(CELL_SIZE+GRID_MARGIN) + 22), 'l')

    def draw(self, t):
        self.draw_background()
        self.draw_grid(t)
        self.draw_room_title()
        self.draw_panel()
        if self.picker.active:
            self.picker.draw(self.ui)
        pg.display.flip()

    # ----------------------------- INPUT ---------------------------------
    def handle_move(self, dr:int, dc:int):
        r,c = self.grid.cursor
        nr, nc = r+dr, c+dc
        if self.grid.in_bounds(nr,nc):
            self.grid.cursor = (nr,nc)

    def handle_space(self):
        keys = pg.key.get_pressed()
        dir_priority = [('N',pg.K_UP,pg.K_z),('E',pg.K_RIGHT,pg.K_d),('S',pg.K_DOWN,pg.K_s),('W',pg.K_LEFT,pg.K_q)]
        for d,k1,k2 in dir_priority:
            if keys[k1] or keys[k2]:
                if self.can_move(d):
                    self.open_door(d)
                else:
                    self.message = 'No door that way.'
                return
        self.message = 'Hold a direction + SPACE.'

    def handle_picker_keys(self, ev):
        if ev.type == pg.KEYDOWN:
            if ev.key in (pg.K_ESCAPE,):
                self.picker.close(); return
            if ev.key in (pg.K_LEFT, pg.K_a):
                self.picker.sel_idx = (self.picker.sel_idx - 1) % len(self.picker.choices)
            if ev.key in (pg.K_RIGHT, pg.K_d):
                self.picker.sel_idx = (self.picker.sel_idx + 1) % len(self.picker.choices)
            if ev.key in (pg.K_RETURN, pg.K_KP_ENTER):
                choice = self.picker.choices[self.picker.sel_idx]
                cell = self.picker.target_cell
                if cell and self.place_room_from_choice(choice, cell):
                    self.picker.close()

    def run(self):
        t = 0.0
        while True:
            for ev in pg.event.get():
                if ev.type == pg.QUIT:
                    pg.quit(); sys.exit(0)
                if self.picker.active:
                    self.handle_picker_keys(ev); continue
                if ev.type == pg.KEYDOWN:
                    if ev.key == pg.K_ESCAPE:
                        pg.quit(); sys.exit(0)
                    elif ev.key in (pg.K_UP, pg.K_z):
                        self.handle_move(-1, 0)
                    elif ev.key in (pg.K_DOWN, pg.K_s):
                        self.handle_move(1, 0)
                    elif ev.key in (pg.K_LEFT, pg.K_q):
                        self.handle_move(0, -1)
                    elif ev.key in (pg.K_RIGHT, pg.K_d):
                        self.handle_move(0, 1)
                    elif ev.key == pg.K_SPACE:
                        self.handle_space()
            self.draw(t)
            self.ui.clock.tick(FPS)
            t += 1/FPS


if __name__ == '__main__':
    Game().run()
