import subprocess
import random
import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import os
import sys

# ─────────────────────────────────────────────
#  PROLOG BRIDGE
# ─────────────────────────────────────────────

SWIPL      = r"C:\Program Files\swipl\bin\swipl.exe"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PL_FILE    = os.path.join(SCRIPT_DIR, "dungeon_logic.pl")

def query_prolog(goal: str) -> str:
    if not os.path.exists(PL_FILE):
        print(f"[ERROR] PL not found: {PL_FILE}", file=sys.stderr); return ""
    if not os.path.exists(SWIPL):
        print(f"[ERROR] swipl not found: {SWIPL}", file=sys.stderr); return ""
    tmp = os.path.join(SCRIPT_DIR, "_tmp_query.pl")
    fwd = PL_FILE.replace("\\", "/")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(f":- ['{fwd}'].\n")
        f.write(f":- forall(({goal}), true), halt.\n")
    r = subprocess.run([SWIPL, "-q", tmp], capture_output=True)
    out = r.stdout.decode("utf-8", errors="replace")
    err = r.stderr.decode("utf-8", errors="replace")
    try: os.remove(tmp)
    except OSError: pass
    if not out and err:
        print(f"[SWIPL ERR] {err[:400]}", file=sys.stderr)
    return out

def _rows(raw: str, n: int):
    rows = []
    for line in raw.splitlines():
        line = line.strip()
        if "|" in line and not line.startswith("%"):
            p = line.split("|")
            if len(p) >= n:
                rows.append(p)
    return rows

def fetch_all_items():
    raw = query_prolog(
        "item(ID,Name,Type,BStat,BVal,DStat,DVal,Desc),"
        "format('~w|~w|~w|~w|~w|~w|~w|~w~n',[ID,Name,Type,BStat,BVal,DStat,DVal,Desc])"
    )
    items = []
    for p in _rows(raw, 8):
        try:
            items.append({
                "id":    p[0], "name":  p[1], "type":  p[2],
                "bstat": p[3], "bval":  int(p[4]),
                "dstat": p[5], "dval":  int(p[6]),
                "desc":  p[7], "rare":  False
            })
        except ValueError:
            pass
    return items

def fetch_all_rare_items():
    raw = query_prolog(
        "rare_item(ID,Name,Type,BStat,BVal,DStat,DVal,Desc,PName,PDesc),"
        "format('~w|~w|~w|~w|~w|~w|~w|~w|~w|~w~n',"
        "[ID,Name,Type,BStat,BVal,DStat,DVal,Desc,PName,PDesc])"
    )
    items = []
    for p in _rows(raw, 10):
        try:
            items.append({
                "id":           p[0], "name":  p[1], "type":  p[2],
                "bstat":        p[3], "bval":  int(p[4]),
                "dstat":        p[5], "dval":  int(p[6]),
                "desc":         p[7], "rare":  True,
                "passive_name": p[8],
                "passive_desc": p[9],
            })
        except ValueError:
            pass
    return items

def fetch_room_enemy():
    raw = query_prolog(
        "room_enemy(Name,HP,Atk,Def),"
        "format('~w|~w|~w|~w~n',[Name,HP,Atk,Def])"
    )
    pool = []
    for p in _rows(raw, 4):
        try:
            pool.append({"name": p[0], "hp": int(p[1]),
                         "atk": int(p[2]), "def": int(p[3])})
        except ValueError:
            pass
    return random.choice(pool) if pool else \
           {"name": "goblin_scout", "hp": 30, "atk": 10, "def": 4}

def fetch_boss(floor_num: int):
    """Floor 5 → fixed final boss.  Floors 1-4 → random from pool."""
    if floor_num == 5:
        raw = query_prolog(
            "final_boss(Name,HP,Atk,Def,Desc,PName,PDesc),"
            "format('~w|~w|~w|~w|~w|~w|~w~n',[Name,HP,Atk,Def,Desc,PName,PDesc])"
        )
    else:
        raw = query_prolog(
            "random_boss(Name,HP,Atk,Def,Desc,PName,PDesc),"
            "format('~w|~w|~w|~w|~w|~w|~w~n',[Name,HP,Atk,Def,Desc,PName,PDesc])"
        )
    for p in _rows(raw, 7):
        try:
            return {
                "name":         p[0], "hp":  int(p[1]),
                "atk":          int(p[2]), "def": int(p[3]),
                "desc":         p[4],
                "passive":      p[5],
                "passive_desc": p[6],
            }
        except ValueError:
            pass
    return {"name": "dungeon_guardian", "hp": 120, "atk": 22,
            "def": 10, "desc": "A fierce dungeon guardian.",
            "passive": "none", "passive_desc": "No special ability."}

def fetch_floor_rooms():
    raw = query_prolog(
        "generate_floor(Rooms),"
        "atomic_list_concat(Rooms,'|',Line),"
        "format('~w~n',[Line])"
    )
    for line in raw.splitlines():
        line = line.strip()
        if "|" in line and not line.startswith("%"):
            rooms = line.split("|")
            if len(rooms) >= 3:
                return rooms
    return ["r_entrance", "r_crypt", "r_armory",
            "r_library", "r_sanctuary", "r_barracks"]

def fetch_room_info(room_id: str):
    raw = query_prolog(
        f"room_type({room_id},Label,Type),"
        f"format('~w|~w~n',[Label,Type])"
    )
    for p in _rows(raw, 2):
        return p[0], p[1]
    return room_id.replace("r_", "").replace("_", " ").title(), "combat"

def fetch_shrine_buff():
    raw = query_prolog(
        "shrine_buff(ID,Label,Stat,Val),"
        "format('~w|~w|~w|~w~n',[ID,Label,Stat,Val])"
    )
    pool = []
    for p in _rows(raw, 4):
        try:
            pool.append({"label": p[1], "stat": p[2], "val": int(p[3])})
        except ValueError:
            pass
    return random.choice(pool) if pool else \
           {"label": "Altar of Strength", "stat": "attack", "val": 3}

def fetch_random_skills():
    """Returns a list of 3 distinct skill dicts: {name, keyword, desc}."""
    raw = query_prolog(
        "random_skills(S1,S2,S3),"
        "S1=sk(N1,K1,D1),S2=sk(N2,K2,D2),S3=sk(N3,K3,D3),"
        "format('~w|~w|~w~n~w|~w|~w~n~w|~w|~w~n',[N1,K1,D1,N2,K2,D2,N3,K3,D3])"
    )
    skills = []
    for p in _rows(raw, 3):
        skills.append({"name": p[0], "keyword": p[1], "desc": p[2]})
    # Fallback if Prolog fails
    if len(skills) < 3:
        skills = [
            {"name": "Iron Will",    "keyword": "iron_will",    "desc": "Reduces all incoming damage by 2."},
            {"name": "Quick Strike", "keyword": "quick_strike", "desc": "20% chance to attack twice per turn."},
            {"name": "Resilience",   "keyword": "resilience",   "desc": "Heal 5 HP at the end of every battle turn."},
        ]
    return skills[:3]

# ─────────────────────────────────────────────
#  SPRITES  (canvas-drawn, no ASCII symbols)
# ─────────────────────────────────────────────

def _draw_player(c, cx, cy):
    """Simple adventurer: round head, body, arms, legs."""
    # head
    c.create_oval(cx-10, cy,    cx+10, cy+20,  fill="#f4c87a", outline="#c8a050", width=1)
    # eyes
    c.create_oval(cx-5,  cy+5,  cx-2,  cy+8,   fill="#1a1a2e", outline="")
    c.create_oval(cx+2,  cy+5,  cx+5,  cy+8,   fill="#1a1a2e", outline="")
    # body (tunic)
    c.create_rectangle(cx-9, cy+20, cx+9, cy+46, fill="#4466aa", outline="#2244aa", width=1)
    # belt
    c.create_rectangle(cx-9, cy+38, cx+9, cy+42, fill="#996633", outline="")
    # left arm
    c.create_rectangle(cx-16, cy+21, cx-9,  cy+38, fill="#4466aa", outline="#2244aa", width=1)
    # right arm (holding sword)
    c.create_rectangle(cx+9,  cy+21, cx+16, cy+38, fill="#4466aa", outline="#2244aa", width=1)
    # sword
    c.create_rectangle(cx+16, cy+14, cx+20, cy+40, fill="#cccccc", outline="#888888", width=1)
    c.create_rectangle(cx+13, cy+24, cx+23, cy+28, fill="#c8a050", outline="")
    # left leg
    c.create_rectangle(cx-8,  cy+46, cx-1,  cy+65, fill="#2e4a1e", outline="#1e3a0e", width=1)
    # right leg
    c.create_rectangle(cx+1,  cy+46, cx+8,  cy+65, fill="#2e4a1e", outline="#1e3a0e", width=1)
    # boots
    c.create_rectangle(cx-10, cy+62, cx-1,  cy+68, fill="#5c3a1e", outline="")
    c.create_rectangle(cx+1,  cy+62, cx+10, cy+68, fill="#5c3a1e", outline="")


def _draw_goblin_scout(c, cx, cy):
    """Small, hunched green goblin with big ears and tiny dagger."""
    # body (hunched, smaller than player)
    c.create_oval(cx-11, cy+18, cx+11, cy+44, fill="#4a7a2a", outline="#2a5a10", width=1)
    # head
    c.create_oval(cx-10, cy+2,  cx+10, cy+22, fill="#5a8a3a", outline="#2a5a10", width=1)
    # big ears
    c.create_oval(cx-18, cy+4,  cx-8,  cy+16, fill="#5a8a3a", outline="#2a5a10", width=1)
    c.create_oval(cx+8,  cy+4,  cx+18, cy+16, fill="#5a8a3a", outline="#2a5a10", width=1)
    # eyes (yellow, beady)
    c.create_oval(cx-6,  cy+8,  cx-2,  cy+12, fill="#ddcc00", outline="")
    c.create_oval(cx+2,  cy+8,  cx+6,  cy+12, fill="#ddcc00", outline="")
    # pupils
    c.create_oval(cx-5,  cy+9,  cx-3,  cy+11, fill="#111111", outline="")
    c.create_oval(cx+3,  cy+9,  cx+5,  cy+11, fill="#111111", outline="")
    # snout / mouth
    c.create_oval(cx-4,  cy+14, cx+4,  cy+20, fill="#4a7a2a", outline="#2a5a10", width=1)
    c.create_line(cx-3,  cy+17, cx+3,  cy+17, fill="#111111", width=1)
    # arms
    c.create_oval(cx-18, cy+22, cx-8,  cy+36, fill="#4a7a2a", outline="#2a5a10", width=1)
    c.create_oval(cx+8,  cy+22, cx+18, cy+36, fill="#4a7a2a", outline="#2a5a10", width=1)
    # dagger (right hand)
    c.create_rectangle(cx+16, cy+28, cx+20, cy+38, fill="#aaaaaa", outline="#666666", width=1)
    # legs
    c.create_oval(cx-8,  cy+40, cx-1,  cy+58, fill="#3a6a1a", outline="#2a5a10", width=1)
    c.create_oval(cx+1,  cy+40, cx+8,  cy+58, fill="#3a6a1a", outline="#2a5a10", width=1)


def _draw_skeleton_warrior(c, cx, cy):
    """Bony white skeleton holding a cracked sword."""
    bone = "#dde8cc"
    dark = "#aabb88"
    # pelvis / lower body
    c.create_rectangle(cx-8, cy+38, cx+8, cy+48, fill=bone, outline=dark, width=1)
    # ribcage
    c.create_rectangle(cx-9, cy+20, cx+9, cy+40, fill=bone, outline=dark, width=1)
    # ribs (horizontal lines inside)
    for rib_y in (cy+24, cy+28, cy+32, cy+36):
        c.create_line(cx-8, rib_y, cx+8, rib_y, fill=dark, width=1)
    # neck
    c.create_rectangle(cx-3, cy+14, cx+3, cy+22, fill=bone, outline=dark, width=1)
    # skull
    c.create_oval(cx-10, cy,    cx+10, cy+18, fill=bone, outline=dark, width=1)
    # eye sockets (dark hollow)
    c.create_oval(cx-7,  cy+4,  cx-2,  cy+10, fill="#223322", outline="")
    c.create_oval(cx+2,  cy+4,  cx+7,  cy+10, fill="#223322", outline="")
    # nasal cavity
    c.create_rectangle(cx-1, cy+10, cx+1, cy+14, fill="#223322", outline="")
    # jaw teeth
    for tx in (cx-6, cx-3, cx, cx+3, cx+6):
        c.create_rectangle(tx-1, cy+16, tx+1, cy+20, fill=bone, outline=dark, width=1)
    # left arm bone
    c.create_rectangle(cx-16, cy+22, cx-9,  cy+40, fill=bone, outline=dark, width=1)
    # right arm + sword
    c.create_rectangle(cx+9,  cy+22, cx+16, cy+40, fill=bone, outline=dark, width=1)
    c.create_rectangle(cx+15, cy+12, cx+19, cy+42, fill="#bbbbbb", outline="#666666", width=1)
    c.create_rectangle(cx+12, cy+22, cx+22, cy+26, fill="#888855", outline="")
    # leg bones
    c.create_rectangle(cx-7,  cy+48, cx-2,  cy+68, fill=bone, outline=dark, width=1)
    c.create_rectangle(cx+2,  cy+48, cx+7,  cy+68, fill=bone, outline=dark, width=1)
    # knee joints
    c.create_oval(cx-8,  cy+54, cx-1,  cy+60, fill=bone, outline=dark, width=1)
    c.create_oval(cx+1,  cy+54, cx+8,  cy+60, fill=bone, outline=dark, width=1)


def _draw_dark_cultist(c, cx, cy):
    """Hooded robed figure with glowing purple eyes."""
    robe  = "#2a1a4a"
    trim  = "#6a3aaa"
    # wide robe bottom
    c.create_polygon(cx-18, cy+70, cx+18, cy+70, cx+12, cy+26, cx-12, cy+26,
                     fill=robe, outline=trim, width=1)
    # robe upper body
    c.create_rectangle(cx-12, cy+20, cx+12, cy+40, fill=robe, outline=trim, width=1)
    # hood (large dark oval)
    c.create_oval(cx-13, cy,    cx+13, cy+26, fill="#1a0a2e", outline=trim, width=2)
    # glowing eyes
    c.create_oval(cx-7,  cy+8,  cx-2,  cy+14, fill="#cc44ff", outline="#aa22ee", width=1)
    c.create_oval(cx+2,  cy+8,  cx+7,  cy+14, fill="#cc44ff", outline="#aa22ee", width=1)
    # glow halos
    c.create_oval(cx-9,  cy+6,  cx,    cy+16, outline="#aa22ee", width=1)
    c.create_oval(cx,    cy+6,  cx+9,  cy+16, outline="#aa22ee", width=1)
    # sleeves
    c.create_oval(cx-20, cy+22, cx-10, cy+38, fill=robe, outline=trim, width=1)
    c.create_oval(cx+10, cy+22, cx+20, cy+38, fill=robe, outline=trim, width=1)
    # staff hand
    c.create_rectangle(cx+18, cy+10, cx+22, cy+60, fill="#5a3a1a", outline="#3a2a0a", width=1)
    # staff orb
    c.create_oval(cx+14, cy+4,  cx+26, cy+16, fill="#8800ff", outline="#cc44ff", width=2)


def _draw_cave_bat_swarm(c, cx, cy):
    """Three bats in a loose cluster."""
    def bat(bx, by, size=1.0):
        s = size
        # body
        c.create_oval(int(bx-5*s), int(by-4*s), int(bx+5*s), int(by+4*s),
                      fill="#2a1a3a", outline="#6a3a8a", width=1)
        # left wing
        c.create_polygon(int(bx-5*s), int(by), int(bx-18*s), int(by-10*s),
                         int(bx-14*s), int(by+4*s),
                         fill="#3a2a5a", outline="#6a3a8a", width=1)
        # right wing
        c.create_polygon(int(bx+5*s), int(by), int(bx+18*s), int(by-10*s),
                         int(bx+14*s), int(by+4*s),
                         fill="#3a2a5a", outline="#6a3a8a", width=1)
        # eyes
        c.create_oval(int(bx-3*s), int(by-3*s), int(bx-1*s), int(by-1*s),
                      fill="#ff4444", outline="")
        c.create_oval(int(bx+1*s), int(by-3*s), int(bx+3*s), int(by-1*s),
                      fill="#ff4444", outline="")
    bat(cx-16, cy+20, 0.9)
    bat(cx+14, cy+14, 1.0)
    bat(cx-2,  cy+40, 1.1)


def _draw_stone_golem(c, cx, cy):
    """Chunky grey stone block creature."""
    stone = "#7a8a7a"
    dark  = "#4a5a4a"
    crack = "#3a4a3a"
    # legs (wide blocks)
    c.create_rectangle(cx-14, cy+52, cx-3,  cy+70, fill=stone, outline=dark, width=2)
    c.create_rectangle(cx+3,  cy+52, cx+14, cy+70, fill=stone, outline=dark, width=2)
    # body (big square)
    c.create_rectangle(cx-18, cy+22, cx+18, cy+54, fill=stone, outline=dark, width=2)
    # crack on body
    c.create_line(cx-4, cy+28, cx+2, cy+40, cx-2, cy+52, fill=crack, width=2)
    # arms (side blocks)
    c.create_rectangle(cx-28, cy+24, cx-18, cy+50, fill=stone, outline=dark, width=2)
    c.create_rectangle(cx+18, cy+24, cx+28, cy+50, fill=stone, outline=dark, width=2)
    # fists
    c.create_rectangle(cx-30, cy+42, cx-16, cy+54, fill=dark, outline=crack, width=1)
    c.create_rectangle(cx+16, cy+42, cx+30, cy+54, fill=dark, outline=crack, width=1)
    # head (square)
    c.create_rectangle(cx-14, cy+4,  cx+14, cy+24, fill=stone, outline=dark, width=2)
    # eye slits (glowing orange)
    c.create_rectangle(cx-10, cy+10, cx-3,  cy+14, fill="#ff8800", outline="")
    c.create_rectangle(cx+3,  cy+10, cx+10, cy+14, fill="#ff8800", outline="")
    # mouth slit
    c.create_rectangle(cx-6,  cy+17, cx+6,  cy+20, fill=crack, outline="")


def _draw_goblin_warlord(c, cx, cy):
    """Larger goblin with spiked helmet and club."""
    # body
    c.create_oval(cx-13, cy+20, cx+13, cy+50, fill="#3a6a1a", outline="#1a4a00", width=2)
    # head
    c.create_oval(cx-12, cy+2,  cx+12, cy+24, fill="#4a7a2a", outline="#1a4a00", width=2)
    # spiked helmet
    c.create_rectangle(cx-13, cy+2, cx+13, cy+10, fill="#8a6a2a", outline="#5a4a1a", width=1)
    for sx in (cx-10, cx-5, cx, cx+5, cx+10):
        c.create_polygon(sx-2, cy+2, sx+2, cy+2, sx, cy-6, fill="#aaa030", outline="")
    # eyes (angry red)
    c.create_oval(cx-7,  cy+8,  cx-2,  cy+13, fill="#ff3300", outline="")
    c.create_oval(cx+2,  cy+8,  cx+7,  cy+13, fill="#ff3300", outline="")
    # pupils
    c.create_oval(cx-6,  cy+9,  cx-3,  cy+12, fill="#220000", outline="")
    c.create_oval(cx+3,  cy+9,  cx+6,  cy+12, fill="#220000", outline="")
    # tusks
    c.create_polygon(cx-6, cy+19, cx-3, cy+19, cx-4, cy+25, fill="#eeeeaa", outline="")
    c.create_polygon(cx+3, cy+19, cx+6, cy+19, cx+4, cy+25, fill="#eeeeaa", outline="")
    # arms
    c.create_oval(cx-22, cy+22, cx-10, cy+42, fill="#3a6a1a", outline="#1a4a00", width=1)
    c.create_oval(cx+10, cy+22, cx+22, cy+42, fill="#3a6a1a", outline="#1a4a00", width=1)
    # club (right hand)
    c.create_rectangle(cx+20, cy+30, cx+26, cy+58, fill="#5a3a1a", outline="#3a2a0a", width=1)
    c.create_oval(cx+16, cy+52, cx+30, cy+64, fill="#7a5a2a", outline="#5a3a1a", width=2)
    # spikes on club
    for sa in (-1, 0, 1):
        c.create_oval(cx+20+sa*4, cy+54, cx+22+sa*4, cy+58, fill="#aaa030", outline="")
    # legs
    c.create_oval(cx-10, cy+46, cx-2,  cy+66, fill="#2a5a0a", outline="#1a4a00", width=1)
    c.create_oval(cx+2,  cy+46, cx+10, cy+66, fill="#2a5a0a", outline="#1a4a00", width=1)


def _draw_skeleton_knight(c, cx, cy):
    """Skeleton in dark plate armour with a shield and sword."""
    bone  = "#dde8cc"
    plate = "#555566"
    trim  = "#aaaacc"
    # legs with greaves
    c.create_rectangle(cx-9,  cy+50, cx-2,  cy+70, fill=plate, outline=trim, width=1)
    c.create_rectangle(cx+2,  cy+50, cx+9,  cy+70, fill=plate, outline=trim, width=1)
    # body / breastplate
    c.create_rectangle(cx-13, cy+22, cx+13, cy+52, fill=plate, outline=trim, width=2)
    c.create_line(cx, cy+22, cx, cy+52, fill=trim, width=1)
    # shoulder pauldrons
    c.create_oval(cx-18, cy+20, cx-8,  cy+32, fill=plate, outline=trim, width=2)
    c.create_oval(cx+8,  cy+20, cx+18, cy+32, fill=plate, outline=trim, width=2)
    # neck
    c.create_rectangle(cx-3, cy+16, cx+3, cy+24, fill=bone, outline=plate, width=1)
    # skull (helmet covers top half)
    c.create_oval(cx-11, cy+2,  cx+11, cy+20, fill=bone, outline=plate, width=1)
    c.create_rectangle(cx-11, cy+2, cx+11, cy+12, fill=plate, outline=trim, width=1)
    # visor slit
    c.create_rectangle(cx-8, cy+10, cx+8, cy+14, fill="#ff2200", outline="")
    # jaw teeth
    for tx in (cx-6, cx-3, cx, cx+3, cx+6):
        c.create_rectangle(tx-1, cy+17, tx+1, cy+21, fill=bone, outline=plate, width=1)
    # sword arm (right)
    c.create_rectangle(cx+13, cy+24, cx+20, cy+48, fill=plate, outline=trim, width=1)
    c.create_rectangle(cx+18, cy+10, cx+22, cy+50, fill="#cccccc", outline="#666666", width=1)
    c.create_rectangle(cx+14, cy+20, cx+26, cy+24, fill=trim,      outline="")
    # shield (left)
    c.create_oval(cx-26, cy+22, cx-10, cy+50, fill=plate, outline=trim, width=2)
    c.create_oval(cx-24, cy+24, cx-12, cy+48, outline=trim, width=1)
    c.create_oval(cx-20, cy+32, cx-16, cy+40, fill=trim, outline="")


def _draw_cave_troll(c, cx, cy):
    """Massive warty green-brown troll."""
    skin  = "#5a7a3a"
    dark  = "#3a5a1a"
    wart  = "#4a6a2a"
    # huge legs
    c.create_oval(cx-16, cy+52, cx-2,  cy+78, fill=skin, outline=dark, width=2)
    c.create_oval(cx+2,  cy+52, cx+16, cy+78, fill=skin, outline=dark, width=2)
    # wide body
    c.create_oval(cx-22, cy+22, cx+22, cy+58, fill=skin, outline=dark, width=2)
    # belly (lighter patch)
    c.create_oval(cx-12, cy+30, cx+12, cy+54, fill="#6a8a4a", outline="")
    # warts on body
    for wx, wy in ((cx-14, cy+30), (cx+12, cy+34), (cx-8, cy+46), (cx+6, cy+28)):
        c.create_oval(wx-3, wy-3, wx+3, wy+3, fill=wart, outline=dark, width=1)
    # massive arms
    c.create_oval(cx-36, cy+24, cx-18, cy+52, fill=skin, outline=dark, width=2)
    c.create_oval(cx+18, cy+24, cx+36, cy+52, fill=skin, outline=dark, width=2)
    # fists
    c.create_oval(cx-38, cy+44, cx-22, cy+58, fill=dark, outline=wart, width=2)
    c.create_oval(cx+22, cy+44, cx+38, cy+58, fill=dark, outline=wart, width=2)
    # big head
    c.create_oval(cx-18, cy+2,  cx+18, cy+28, fill=skin, outline=dark, width=2)
    # heavy brow
    c.create_rectangle(cx-16, cy+8, cx+16, cy+14, fill=dark, outline="")
    # small beady eyes
    c.create_oval(cx-10, cy+12, cx-4,  cy+18, fill="#ffcc00", outline=dark, width=1)
    c.create_oval(cx+4,  cy+12, cx+10, cy+18, fill="#ffcc00", outline=dark, width=1)
    c.create_oval(cx-8,  cy+14, cx-6,  cy+16, fill="#111111", outline="")
    c.create_oval(cx+6,  cy+14, cx+8,  cy+16, fill="#111111", outline="")
    # flat nose
    c.create_oval(cx-5,  cy+17, cx+5,  cy+24, fill=dark, outline="")
    # jagged teeth
    c.create_polygon(cx-8, cy+23, cx+8, cy+23, cx+6, cy+28, cx+2, cy+25,
                     cx-2, cy+28, cx-6, cy+25, fill="#eeeeaa", outline=dark, width=1)


def _draw_shadow_stalker(c, cx, cy):
    """Wispy dark wraith — semi-transparent feel with sharp claws."""
    # layered shadow wisps (bottom trail)
    for i, alpha_col in enumerate(("#1a0a2e", "#2a1a4a", "#3a1a5a")):
        spread = 14 - i * 3
        c.create_oval(cx-spread, cy+55+i*4, cx+spread, cy+75+i*4,
                      fill=alpha_col, outline="")
    # cloak body
    c.create_polygon(cx-16, cy+20, cx+16, cy+20,
                     cx+10, cy+58, cx-10, cy+58,
                     fill="#1e0a38", outline="#6622aa", width=1)
    # inner glow
    c.create_polygon(cx-8,  cy+22, cx+8,  cy+22,
                     cx+5,  cy+52, cx-5,  cy+52,
                     fill="#2a0a4a", outline="")
    # head / cowl
    c.create_oval(cx-13, cy+2, cx+13, cy+24, fill="#0e0020", outline="#6622aa", width=2)
    # glowing magenta eyes
    c.create_oval(cx-8,  cy+8,  cx-2,  cy+15, fill="#ff00cc", outline="#cc00aa", width=1)
    c.create_oval(cx+2,  cy+8,  cx+8,  cy+15, fill="#ff00cc", outline="#cc00aa", width=1)
    # glow rings
    c.create_oval(cx-10, cy+6,  cx-0,  cy+17, outline="#cc00aa", width=1)
    c.create_oval(cx+0,  cy+6,  cx+10, cy+17, outline="#cc00aa", width=1)
    # claw arms
    c.create_polygon(cx-16, cy+24, cx-22, cy+44, cx-18, cy+46,
                     cx-12, cy+28, fill="#1e0a38", outline="#6622aa", width=1)
    c.create_polygon(cx+16, cy+24, cx+22, cy+44, cx+18, cy+46,
                     cx+12, cy+28, fill="#1e0a38", outline="#6622aa", width=1)
    # claw tips
    for ox, oy in ((-22, 44), (-19, 48), (-16, 51)):
        c.create_polygon(cx+ox, cy+oy, cx+ox+2, cy+oy, cx+ox+1, cy+oy+6,
                         fill="#cc88ff", outline="")
    for ox, oy in ((22, 44), (19, 48), (16, 51)):
        c.create_polygon(cx+ox, cy+oy, cx+ox-2, cy+oy, cx+ox-1, cy+oy+6,
                         fill="#cc88ff", outline="")


def _draw_labyrinth_overlord(c, cx, cy):
    """Imposing armoured overlord with crown, cape and massive sword."""
    cape  = "#6a0000"
    plate = "#2a2a4a"
    trim  = "#cc9900"
    glow  = "#ff4400"
    # cape
    c.create_polygon(cx-20, cy+14, cx+20, cy+14,
                     cx+28, cy+72, cx-28, cy+72,
                     fill=cape, outline="#440000", width=1)
    # legs armour
    c.create_rectangle(cx-12, cy+52, cx-3,  cy+74, fill=plate, outline=trim, width=2)
    c.create_rectangle(cx+3,  cy+52, cx+12, cy+74, fill=plate, outline=trim, width=2)
    # body armour
    c.create_rectangle(cx-16, cy+22, cx+16, cy+54, fill=plate, outline=trim, width=2)
    # chest emblem
    c.create_oval(cx-6, cy+30, cx+6, cy+42, fill=glow, outline=trim, width=1)
    # shoulder plates
    c.create_oval(cx-24, cy+18, cx-12, cy+32, fill=plate, outline=trim, width=2)
    c.create_oval(cx+12, cy+18, cx+24, cy+32, fill=plate, outline=trim, width=2)
    # neck
    c.create_rectangle(cx-4, cy+14, cx+4, cy+24, fill=plate, outline=trim, width=1)
    # head / helmet
    c.create_oval(cx-13, cy+2,  cx+13, cy+22, fill=plate, outline=trim, width=2)
    # crown spikes
    for sx, sh in ((cx-10, 8), (cx-5, 12), (cx, 14), (cx+5, 12), (cx+10, 8)):
        c.create_polygon(sx-3, cy+4, sx+3, cy+4, sx, cy+4-sh,
                         fill=trim, outline="#aa7700", width=1)
    # eye slits (fiery)
    c.create_rectangle(cx-9,  cy+10, cx-2,  cy+14, fill=glow, outline="")
    c.create_rectangle(cx+2,  cy+10, cx+9,  cy+14, fill=glow, outline="")
    # massive sword (right)
    c.create_rectangle(cx+20, cy+2,  cx+26, cy+60, fill="#aaaacc", outline=trim, width=1)
    c.create_rectangle(cx+14, cy+14, cx+32, cy+20, fill=trim,      outline="")
    c.create_polygon(cx+20, cy+2, cx+26, cy+2, cx+23, cy-10,
                     fill="#ccccff", outline=trim, width=1)
    # shield (left)
    c.create_polygon(cx-16, cy+22, cx-28, cy+30, cx-28, cy+52, cx-16, cy+58,
                     fill=plate, outline=trim, width=2)
    c.create_oval(cx-26, cy+34, cx-18, cy+44, fill=glow, outline=trim, width=1)


def _draw_cursed_champion(c, cx, cy):
    """Dark warrior with blazing blade and torn armour."""
    armour = "#3a3a5a"
    trim = "#d46b00"
    skin = "#c7c7c7"
    glow = "#ff6a00"
    c.create_rectangle(cx-14, cy+22, cx+14, cy+52, fill=armour, outline=trim, width=2)
    c.create_rectangle(cx-8, cy+52, cx-2, cy+70, fill=armour, outline=trim, width=1)
    c.create_rectangle(cx+2, cy+52, cx+8, cy+70, fill=armour, outline=trim, width=1)
    c.create_oval(cx-15, cy+2, cx+15, cy+20, fill=skin, outline=trim, width=2)
    c.create_rectangle(cx-10, cy+8, cx+10, cy+12, fill=trim, outline="")
    c.create_oval(cx-7, cy+8, cx-2, cy+14, fill=glow, outline="")
    c.create_oval(cx+2, cy+8, cx+7, cy+14, fill=glow, outline="")
    c.create_oval(cx-18, cy+18, cx-10, cy+32, fill=armour, outline=trim, width=1)
    c.create_oval(cx+10, cy+18, cx+22, cy+32, fill=armour, outline=trim, width=1)
    c.create_rectangle(cx+18, cy+12, cx+23, cy+58, fill="#b0b0c6", outline="#555566", width=1)
    c.create_polygon(cx+23, cy+10, cx+28, cy+12, cx+25, cy+2, fill="#d4d4ff", outline=trim, width=1)
    c.create_oval(cx-22, cy+34, cx-14, cy+50, fill=trim, outline="")
    c.create_oval(cx+14, cy+34, cx+22, cy+50, fill=trim, outline="")


def _draw_iron_colossus(c, cx, cy):
    """Towering iron statue with glowing core."""
    iron = "#8f9aa8"
    dark = "#4f5a66"
    glow = "#ff9900"
    c.create_rectangle(cx-16, cy+52, cx-4, cy+72, fill=iron, outline=dark, width=2)
    c.create_rectangle(cx+4, cy+52, cx+16, cy+72, fill=iron, outline=dark, width=2)
    c.create_rectangle(cx-20, cy+18, cx+20, cy+52, fill=iron, outline=dark, width=2)
    c.create_oval(cx-10, cy+28, cx+10, cy+42, fill=glow, outline=dark, width=2)
    c.create_rectangle(cx-26, cy+20, cx-18, cy+44, fill=iron, outline=dark, width=2)
    c.create_rectangle(cx+18, cy+20, cx+26, cy+44, fill=iron, outline=dark, width=2)
    c.create_rectangle(cx-12, cy+4, cx+12, cy+22, fill=iron, outline=dark, width=2)
    c.create_rectangle(cx-8, cy+8, cx-2, cy+14, fill=glow, outline="")
    c.create_rectangle(cx+2, cy+8, cx+8, cy+14, fill=glow, outline="")
    c.create_rectangle(cx+24, cy+16, cx+28, cy+52, fill="#b8bec8", outline=dark, width=1)
    c.create_polygon(cx+28, cy+14, cx+32, cy+18, cx+28, cy+0, fill="#dfe7ef", outline=dark, width=1)


def _draw_plague_witch(c, cx, cy):
    """Mottled witch with green magic and a bubbling cauldron."""
    robe = "#2d4a3a"
    trim = "#89d08c"
    skin = "#d9d9d9"
    c.create_oval(cx-18, cy+32, cx+18, cy+62, fill=robe, outline=trim, width=2)
    c.create_oval(cx-12, cy+2, cx+12, cy+24, fill=skin, outline=trim, width=2)
    c.create_oval(cx-7, cy+8, cx-2, cy+16, fill="#9ce8a4", outline="")
    c.create_oval(cx+2, cy+8, cx+7, cy+16, fill="#9ce8a4", outline="")
    c.create_oval(cx-22, cy+20, cx-10, cy+36, fill=robe, outline=trim, width=1)
    c.create_oval(cx+10, cy+20, cx+22, cy+36, fill=robe, outline=trim, width=1)
    c.create_oval(cx-10, cy+56, cx-2, cy+72, fill=robe, outline=trim, width=1)
    c.create_oval(cx+2, cy+56, cx+10, cy+72, fill=robe, outline=trim, width=1)
    c.create_oval(cx+16, cy+12, cx+30, cy+28, fill="#5b9a5d", outline=trim, width=2)
    c.create_oval(cx+18, cy+14, cx+28, cy+24, fill="#90f3a0", outline="")
    c.create_oval(cx-16, cy+56, cx+16, cy+72, fill="#355f45", outline=trim, width=1)


def _draw_void_herald(c, cx, cy):
    """Dark herald with a swirling void aura."""
    dark = "#090d1a"
    glow = "#7b52d6"
    aura = "#2b123a"
    c.create_oval(cx-18, cy+52, cx+18, cy+82, fill=aura, outline=glow, width=1)
    c.create_oval(cx-16, cy+0, cx+16, cy+28, fill=dark, outline=glow, width=2)
    c.create_oval(cx-8, cy+8, cx-2, cy+15, fill="#e0c8ff", outline="")
    c.create_oval(cx+2, cy+8, cx+8, cy+15, fill="#e0c8ff", outline="")
    c.create_oval(cx-10, cy+30, cx+10, cy+50, fill="#1b1530", outline=glow, width=1)
    c.create_oval(cx-22, cy+16, cx-8, cy+32, fill=dark, outline=glow, width=1)
    c.create_oval(cx+8, cy+16, cx+22, cy+32, fill=dark, outline=glow, width=1)
    c.create_polygon(cx-12, cy+42, cx-20, cy+58, cx-14, cy+60, fill=glow, outline="")
    c.create_polygon(cx+12, cy+42, cx+20, cy+58, cx+14, cy+60, fill=glow, outline="")
    c.create_oval(cx-32, cy+12, cx-14, cy+28, fill=glow, outline="")
    c.create_oval(cx+14, cy+12, cx+32, cy+28, fill=glow, outline="")


# Map enemy name → draw function
ENEMY_DRAW = {
    "goblin_scout":       _draw_goblin_scout,
    "skeleton_warrior":   _draw_skeleton_warrior,
    "dark_cultist":       _draw_dark_cultist,
    "cave_bat_swarm":     _draw_cave_bat_swarm,
    "stone_golem_minion": _draw_stone_golem,
    "goblin_warlord":     _draw_goblin_warlord,
    "skeleton_knight":    _draw_skeleton_knight,
    "cave_troll":         _draw_cave_troll,
    "shadow_stalker":     _draw_shadow_stalker,
    "cursed_champion":    _draw_cursed_champion,
    "iron_colossus":      _draw_iron_colossus,
    "plague_witch":       _draw_plague_witch,
    "void_herald":        _draw_void_herald,
    "labyrinth_overlord": _draw_labyrinth_overlord,
}

ROOM_ICONS = {"combat": "⚔", "loot": "💰", "shrine": "✨", "rest": "🏕", "boss": "💀", "skill": "🌀"}

# ─────────────────────────────────────────────
#  COLOURS / FONTS
# ─────────────────────────────────────────────

BG    = "#1a1a2e"
PANEL = "#16213e"
ACCENT= "#e94560"
TEXT  = "#eaeaea"
DIM   = "#888888"
GREEN = "#0f9b58"
YELLOW= "#f5a623"
BLUE  = "#4e8ef7"
HP_BG = "#3a0000"
HP_FG = "#e94560"

FT = ("Courier New", 19, "bold")
FM = ("Courier New", 12)
FS = ("Courier New", 10)
FA = ("Courier New", 15, "bold")
FB = ("Courier New", 11, "bold")

# ─────────────────────────────────────────────
#  APP
# ─────────────────────────────────────────────

class DungeonApp(tk.Tk):

    MAX_HP = 100

    def __init__(self):
        super().__init__()
        self.title("Logic Labyrinth")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.geometry("960x760")
        self.minsize(920, 720)

        self.all_items        = []
        self.all_rare_items   = []
        self.player           = {}
        self.enemy            = {}
        self.e_hp             = 0
        self.floor            = 1
        self.floor_rooms      = []   # [[rid, label, rtype, cleared], ...]
        self.current_room_idx = None
        self.battle_over      = True
        self.in_boss          = False
        self.boss_turn_count  = 0    # counts turns during boss fights
        self.passive_stacks   = {}   # tracks stacking passive effects
        self.second_wind_used = False  # for soulstone_pendant passive
        self.boss_cleared     = False  # tracks whether this floor's boss is done
        self.consumables_shown= []
        self.undying_used     = False  # resets each floor

        self._build_ui()
        self._start_game()

    # ════════════════════════════════════════
    #  UI BUILD
    # ════════════════════════════════════════

    def _build_ui(self):
        # ── title bar ──
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=10, pady=(8, 0))
        tk.Label(top, text="⚔  LOGIC LABYRINTH  ⚔",
                 font=FT, bg=BG, fg=ACCENT).pack(side="left")
        self.floor_lbl = tk.Label(top, text="Floor 1 / 5",
                                  font=FS, bg=BG, fg=DIM)
        self.floor_lbl.pack(side="right")

        # ── arena  +  map (side by side) ──
        mid = tk.Frame(self, bg=BG)
        mid.pack(fill="x", padx=10, pady=4)

        arena_wrap = tk.Frame(mid, bg=PANEL, relief="ridge", bd=2)
        arena_wrap.pack(side="left")
        self.canvas = tk.Canvas(arena_wrap, width=540, height=260,
                                bg=BG, highlightthickness=0)
        self.canvas.pack()

        # map panel — large enough for all rooms, with internal scrolling
        map_outer = tk.Frame(mid, bg=PANEL, relief="ridge", bd=2,
                             width=260, height=260)
        map_outer.pack(side="left", padx=(8, 0))
        map_outer.pack_propagate(False)
        tk.Label(map_outer, text=" Floor Map ", font=FS,
                 bg=PANEL, fg=DIM).pack(anchor="w", padx=4)

        map_canvas = tk.Canvas(map_outer, bg=PANEL, highlightthickness=0, height=220)
        map_scroll = tk.Scrollbar(map_outer, orient="vertical", command=map_canvas.yview)
        map_canvas.configure(yscrollcommand=map_scroll.set)
        map_scroll.pack(side="right", fill="y")
        map_canvas.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=(0, 4))

        self.map_frame = tk.Frame(map_canvas, bg=PANEL)
        self.map_canvas = map_canvas
        map_canvas.create_window((0, 0), window=self.map_frame, anchor="nw")
        self.map_frame.bind("<Configure>", lambda e: map_canvas.configure(scrollregion=map_canvas.bbox("all")))

        # ── HP bars ──
        bars = tk.Frame(self, bg=BG)
        bars.pack(fill="x", padx=10, pady=2)

        pl = tk.Frame(bars, bg=BG)
        pl.pack(side="left", fill="x", expand=True)
        tk.Label(pl, text="PLAYER", font=FS, bg=BG, fg=ACCENT).pack(anchor="w")
        self.pl_hp_bar   = self._bar(pl, HP_BG, HP_FG, 290)
        self.pl_hp_lbl   = tk.Label(pl, text="HP: 100/100", font=FS, bg=BG, fg=TEXT)
        self.pl_hp_lbl.pack(anchor="w")
        self.pl_stat_lbl = tk.Label(pl, text="ATK: 20  DEF: 15", font=FS, bg=BG, fg=DIM)
        self.pl_stat_lbl.pack(anchor="w")

        en = tk.Frame(bars, bg=BG)
        en.pack(side="right", fill="x", expand=True)
        self.en_name_lbl = tk.Label(en, text="—", font=FS, bg=BG, fg=YELLOW)
        self.en_name_lbl.pack(anchor="e")
        self.en_hp_bar   = self._bar(en, HP_BG, YELLOW, 290)
        self.en_hp_lbl   = tk.Label(en, text="", font=FS, bg=BG, fg=TEXT)
        self.en_hp_lbl.pack(anchor="e")
        self.en_stat_lbl = tk.Label(en, text="", font=FS, bg=BG, fg=DIM)
        self.en_stat_lbl.pack(anchor="e")

        # ── battle log ──
        lf = tk.Frame(self, bg=PANEL, relief="ridge", bd=2)
        lf.pack(fill="both", expand=True, padx=10, pady=4)
        tk.Label(lf, text=" Battle Log ", font=FS, bg=PANEL, fg=DIM).pack(anchor="w")
        self.log = scrolledtext.ScrolledText(
            lf, height=9, bg="#0d0d1a", fg=TEXT, font=FM,
            state="disabled", wrap="word", relief="flat")
        self.log.pack(fill="both", expand=True, padx=4, pady=4)

        # ── action buttons ──
        bf = tk.Frame(self, bg=BG)
        bf.pack(fill="x", padx=10, pady=4)
        self.btn_attack = self._btn(bf, "⚔  Attack",   ACCENT, self._do_attack)
        self.btn_bag    = self._btn(bf, "🎒  Use Item", GREEN,  self._do_bag)
        self.btn_flee   = self._btn(bf, "🏃  Flee",     DIM,    self._do_flee)
        for b in (self.btn_attack, self.btn_bag, self.btn_flee):
            b.pack(side="left", padx=6, pady=4, ipadx=18, ipady=8)

        # ── inventory ──
        inv_f = tk.Frame(self, bg=PANEL, relief="ridge", bd=2)
        inv_f.pack(fill="x", padx=10, pady=(0, 4))
        tk.Label(inv_f, text=" Inventory ", font=FS, bg=PANEL, fg=DIM).pack(anchor="w")
        self.inv_lbl = tk.Label(inv_f, text="(empty)", font=FS,
                                bg=PANEL, fg=TEXT, wraplength=600, justify="left")
        self.inv_lbl.pack(anchor="w", padx=6, pady=2)

        # ── passive skills ──
        sk_f = tk.Frame(self, bg="#0d1a2e", relief="ridge", bd=2)
        sk_f.pack(fill="x", padx=10, pady=(0, 8))
        tk.Label(sk_f, text=" Passive Skills ", font=FS, bg="#0d1a2e", fg=BLUE).pack(anchor="w")
        self.skills_lbl = tk.Label(sk_f, text="(none learned yet)",
                                   font=FS, bg="#0d1a2e", fg=DIM,
                                   wraplength=600, justify="left")
        self.skills_lbl.pack(anchor="w", padx=6, pady=2)

    def _bar(self, parent, bg, fg, width):
        frame = tk.Frame(parent, bg=bg, width=width, height=13, relief="flat")
        frame.pack_propagate(False)
        frame.pack(anchor="w", pady=1)
        fill = tk.Frame(frame, bg=fg, height=13)
        fill.place(x=0, y=0, relwidth=0, height=13)  # start empty
        frame._fill = fill
        return frame

    def _btn(self, parent, text, color, cmd):
        return tk.Button(parent, text=text, font=FM, bg=color, fg="white",
                         activebackground=color, activeforeground="white",
                         relief="flat", cursor="hand2", height=2,
                         command=cmd)

    def _set_bar(self, bar, ratio):
        bar._fill.place(relwidth=max(0.0, min(1.0, ratio)))

    # ════════════════════════════════════════
    #  LOGGING
    # ════════════════════════════════════════

    def _log(self, text, color=None):
        self.log.configure(state="normal")
        if color:
            tag = f"t{color.replace('#','')}"
            self.log.tag_configure(tag, foreground=color)
            self.log.insert("end", text + "\n", tag)
        else:
            self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _sep(self):
        self._log("─" * 52, DIM)

    # ════════════════════════════════════════
    #  CANVAS / ARENA
    # ════════════════════════════════════════

    def _draw_arena(self):
        c = self.canvas
        c.delete("all")
        W, H = 430, 200

        # background gradient
        for i in range(H):
            shade = int(10 + 30 * (i / H))
            c.create_line(0, i, W, i,
                          fill=f"#{shade:02x}{shade:02x}{shade+20:02x}")
        # ground strip
        c.create_rectangle(0, H - 28, W, H, fill="#1e3a1e", outline="")

        # player (canvas-drawn, centred at x=80, top of sprite at y=10)
        _draw_player(c, 80, 10)

        # enemy
        if not self.battle_over and self.enemy:
            ename = self.enemy.get("name", "")
            draw_fn = ENEMY_DRAW.get(ename)
            if draw_fn:
                draw_fn(c, 350, 10)
            else:
                # fallback: grey question-mark silhouette
                c.create_oval(330, 10, 370, 50, fill="#445544", outline="#667766")
                c.create_text(350, 30, text="?", font=FA, fill=TEXT)
            c.create_text(350, H - 36, text=f"HP {max(0, self.e_hp)}",
                          font=FS, fill=YELLOW)

        c.create_text(80, H - 36,
                      text=f"HP {self.player.get('hp', 0)}",
                      font=FS, fill=HP_FG)

    def _flash(self, side):
        c = self.canvas
        x = 80 if side == "player" else 350
        r = c.create_rectangle(x-38, 8, x+38, 168,
                               fill=ACCENT, outline="", stipple="gray50")
        self.after(140, lambda: c.delete(r))

    # ════════════════════════════════════════
    #  FLOOR MAP
    # ════════════════════════════════════════

    def _build_map(self):
        """Rebuild map buttons. All uncleared rooms are freely clickable."""
        for w in self.map_frame.winfo_children():
            w.destroy()

        self.map_frame.update_idletasks()
        self.map_canvas.update_idletasks()

        for idx, (rid, label, rtype, cleared) in enumerate(self.floor_rooms):
            icon  = ROOM_ICONS.get(rtype, "?")
            short = label if len(label) <= 16 else label[:15] + "..."

            if cleared:
                bg, fg, cursor, state, cmd = "#1a2a1a", DIM, "arrow", "disabled", None
                txt = f"[+] {short}"
            elif idx == self.current_room_idx:
                bg, fg, cursor, state, cmd = ACCENT, "white", "arrow", "disabled", None
                txt = f">>> {short}"
            else:
                bg, fg, cursor, state = PANEL, TEXT, "hand2", "normal"
                txt = f"{icon} {short}"
                cmd = lambda i=idx: self._enter_room(i)

            tk.Button(self.map_frame, text=txt, font=FM,
                      bg=bg, fg=fg, relief="flat", cursor=cursor,
                      anchor="w", padx=6, pady=4, height=2,
                      state=state, command=cmd
                      ).pack(fill="x", pady=2)

        # Boss button
        remaining = sum(1 for r in self.floor_rooms if not r[3])
        all_done  = (remaining == 0)

        if self.boss_cleared:
            boss_bg, boss_fg, boss_cur, boss_state, boss_cmd = "#1a2a1a", DIM, "arrow", "disabled", None
            boss_txt = "[+] Boss Defeated"
        elif all_done:
            boss_bg, boss_fg, boss_cur, boss_state, boss_cmd = "#6b0000", "white", "hand2", "normal", self._enter_boss
            boss_txt = "!! BOSS ROOM"
        else:
            boss_bg, boss_fg, boss_cur, boss_state, boss_cmd = BG, DIM, "arrow", "disabled", None
            boss_txt = f"   Boss ({remaining} left)"

        tk.Button(self.map_frame, text=boss_txt, font=FM,
                  bg=boss_bg, fg=boss_fg, relief="flat", cursor=boss_cur,
                  anchor="w", padx=6, pady=4, height=2,
                  state=boss_state, command=boss_cmd
                  ).pack(fill="x", pady=2)

        # Force scroll region to update so all buttons are reachable
        self.map_frame.update_idletasks()
        self.map_canvas.configure(scrollregion=self.map_canvas.bbox("all"))

    # ════════════════════════════════════════
    #  STAT / INV REFRESH
    # ════════════════════════════════════════

    def _refresh(self):
        p = self.player
        if not p:
            return
        max_hp = self._max_hp
        self.pl_hp_lbl.config(text=f"HP: {p['hp']}/{max_hp}")
        self.pl_stat_lbl.config(text=f"ATK: {p['atk']}  DEF: {p['def']}")
        self._set_bar(self.pl_hp_bar, p["hp"] / max(1, max_hp))

        if self.enemy and not self.battle_over:
            emx = self.enemy.get("hp", 1)
            self.en_name_lbl.config(
                text=self.enemy["name"].replace("_", " ").upper())
            self.en_hp_lbl.config(text=f"HP: {max(0,self.e_hp)}/{emx}")
            self.en_stat_lbl.config(
                text=f"ATK: {self.enemy['atk']}  DEF: {self.enemy['def']}")
            self._set_bar(self.en_hp_bar, max(0, self.e_hp) / max(1, emx))
        else:
            self.en_name_lbl.config(text="--")
            self.en_hp_lbl.config(text="")
            self.en_stat_lbl.config(text="")
            self._set_bar(self.en_hp_bar, 0)   # always explicitly zero when no battle

        self._draw_arena()

    def _refresh_inv(self):
        inv = self.player.get("inventory", [])
        if not inv:
            self.inv_lbl.config(text="(empty)")
        else:
            self.inv_lbl.config(
                text="  •  ".join(
                    f"{it['name'].replace('_',' ')} [{it['type'][0].upper()}]"
                    for it in inv))
        self._refresh_skills()

    def _refresh_skills(self):
        skills = self.player.get("passives", [])
        if not skills:
            self.skills_lbl.config(text="(none learned yet)", fg=DIM)
            return
        parts = [f"🌀 {s['name']}" for s in skills]
        self.skills_lbl.config(
            text="  |  ".join(parts),
            fg=BLUE)

    def _btns(self, on: bool):
        s = "normal" if on else "disabled"
        for b in (self.btn_attack, self.btn_bag, self.btn_flee):
            b.config(state=s)

    @property
    def _max_hp(self) -> int:
        """Per-player HP cap (raised by Endurance skill)."""
        if not self.player:
            return self.MAX_HP
        return int(self.player.get("max_hp", self.MAX_HP))

    # ════════════════════════════════════════
    #  GAME BOOTSTRAP
    # ════════════════════════════════════════

    def _start_game(self):
        self._log("Loading Prolog knowledge base...", DIM)
        self._btns(False)

        def _load():
            # All Prolog I/O happens here in the background thread
            items      = fetch_all_items()
            rare_items = fetch_all_rare_items()
            # Pre-load room info for floor 1 so the main thread doesn't block
            raw_rooms  = fetch_floor_rooms()
            room_data  = []
            for rid in raw_rooms:
                label, rtype = fetch_room_info(rid)
                room_data.append([rid, label, rtype, False])
            # Hand results back to the main thread
            self.after(0, lambda: self._init_game(items, rare_items, room_data))

        threading.Thread(target=_load, daemon=True).start()

    def _init_game(self, items, rare_items, room_data):
        if not items:
            mp = not os.path.exists(PL_FILE)
            ms = not os.path.exists(SWIPL)
            msg = "Could not load items from Prolog.\n\n"
            if ms: msg += f"• swipl not found:\n  {SWIPL}\n\n"
            if mp: msg += f"• dungeon_logic.pl not found:\n  {PL_FILE}\n\n"
            if not ms and not mp:
                msg += "Both files exist -- check terminal for swipl errors.\n\n"
            msg += "Fix above and restart."
            messagebox.showerror("Error", msg)
            return

        self.all_items      = items
        self.all_rare_items = rare_items
        self.player = {
            "hp":       self.MAX_HP,
            "max_hp":   self.MAX_HP,
            "atk":      20,
            "def":      15,
            "inventory":[],
            "passives": [],
        }
        self._log("=" * 52, ACCENT)
        self._log("   LOGIC LABYRINTH  --  DUNGEON RPG", ACCENT)
        self._log(f"   {len(items)} items + {len(rare_items)} rare relics loaded.", GREEN)
        self._log("=" * 52, ACCENT)
        self._new_floor(1, room_data)

    # ════════════════════════════════════════
    #  FLOOR & ROOM MANAGEMENT
    # ════════════════════════════════════════

    def _new_floor(self, floor, preloaded_rooms=None):
        self.floor = floor
        self.floor_lbl.config(text=f"Floor {floor} / 5")
        self._sep()
        self._log(f"  ▶  FLOOR {floor} / 5", ACCENT)
        self._sep()

        self.current_room_idx = None
        self.battle_over      = True
        self.enemy            = {}
        self.boss_cleared     = False
        self.undying_used     = False

        if preloaded_rooms is not None:
            # Already fetched in background — use immediately
            self.floor_rooms = preloaded_rooms
            self._on_floor_ready()
        else:
            # Fetch rooms in background so UI doesn't freeze
            self._log("  Loading floor...", DIM)
            def _load():
                raw = fetch_floor_rooms()
                data = []
                for rid in raw:
                    label, rtype = fetch_room_info(rid)
                    data.append([rid, label, rtype, False])
                self.after(0, lambda: self._on_floor_loaded(data))
            threading.Thread(target=_load, daemon=True).start()

    def _on_floor_loaded(self, room_data):
        self.floor_rooms = room_data
        self._on_floor_ready()

    def _on_floor_ready(self):
        self._refresh()
        # Small delay lets Tkinter finish geometry calculation on map_outer
        # before _build_map packs buttons into map_frame
        self.after(50, self._finish_floor_ready)

    def _finish_floor_ready(self):
        self._build_map()
        self._refresh_skills()
        self._log("  Pick any room on the map to explore!", BLUE)
        self._log("  Clear all rooms to unlock the Boss.", DIM)

    def _enter_room(self, idx):
        # Block mid-battle navigation
        if not self.battle_over:
            self._log("  ⚠  Finish the battle first!", ACCENT)
            return
        rid, label, rtype, cleared = self.floor_rooms[idx]
        if cleared:
            return

        self.current_room_idx = idx
        self._build_map()
        self._sep()
        self._log(f"  {ROOM_ICONS.get(rtype,'?')}  {label.upper()}", YELLOW)

        if rtype == "combat":
            enemy = fetch_room_enemy()
            # Difficulty curve per floor:
            # Floor 1: baseline  Floor 2: +25%  Floor 3: +55%  Floor 4: +90%  Floor 5: +130%
            hp_scales  = {1: 1.00, 2: 1.25, 3: 1.55, 4: 1.90, 5: 2.30}
            atk_scales = {1: 1.00, 2: 1.20, 3: 1.45, 4: 1.75, 5: 2.10}
            def_scales = {1: 1.00, 2: 1.15, 3: 1.35, 4: 1.60, 5: 1.90}
            enemy["hp"]  = int(enemy["hp"]  * hp_scales[self.floor])
            enemy["atk"] = int(enemy["atk"] * atk_scales[self.floor])
            enemy["def"] = int(enemy["def"] * def_scales[self.floor])
            self._log(f"  A {enemy['name'].replace('_',' ').upper()} appears!", TEXT)
            tier = ["", "Weak", "Seasoned", "Dangerous", "Fearsome", "Elite"][self.floor]
            self._log(f"  [{tier} — Floor {self.floor}]", DIM)
            self._begin_battle(enemy, is_boss=False)

        elif rtype == "loot":
            self._log("  Something glimmers in the corner…", TEXT)
            self.after(300, self._do_loot_room)

        elif rtype == "shrine":
            self._log("  You sense a mystical aura…", BLUE)
            self.after(300, self._do_shrine_room)

        elif rtype == "rest":
            self._log("  A quiet chamber. You take a breather.", GREEN)
            self.after(300, self._do_rest_room)

        elif rtype == "skill":
            self._log("  A mysterious voice echoes… 'Choose your path.'", BLUE)
            self.after(300, self._do_skill_room)

    def _mark_cleared(self):
        self.floor_rooms[self.current_room_idx][3] = True
        self.current_room_idx = None
        self._build_map()

    # ════════════════════════════════════════
    #  ROOM EVENTS
    # ════════════════════════════════════════

    def _do_loot_room(self):
        item = self._roll_drop()
        self._log_drop(item)
        self._show_item_choice(item, after_fn=self._mark_cleared)

    def _do_shrine_room(self):
        buff = fetch_shrine_buff()
        stat, val, label = buff["stat"], buff["val"], buff["label"]
        self._sep()
        self._log(f"  ✨  {label}", BLUE)
        if stat == "attack":
            self.player["atk"] += val
            self._log(f"  ATK +{val}!", GREEN)
        elif stat == "defense":
            self.player["def"] += val
            self._log(f"  DEF +{val}!", GREEN)
        elif stat == "hp":
            heal = min(self._max_hp, self.player["hp"] + val) - self.player["hp"]
            self.player["hp"] += heal
            self._log(f"  Restored {heal} HP!", GREEN)
        self._refresh()
        self._mark_cleared()

    def _do_rest_room(self):
        heal_amt = 15
        before = self.player["hp"]
        self.player["hp"] = min(self._max_hp, self.player["hp"] + heal_amt)
        actual = self.player["hp"] - before
        self._sep()
        self._log(f"  🏕  You rest and recover {actual} HP.", GREEN)
        self._refresh()
        self._mark_cleared()

    def _do_skill_room(self):
        """Show 3 random skills — player picks one (max 5 total)."""
        MAX_SKILLS = 5
        current = self.player["passives"]
        if len(current) >= MAX_SKILLS:
            self._sep()
            self._log("  🌀  You already know 5 skills — mastery is complete!", BLUE)
            self._log("  Your skill slots are full. No new skills can be learned.", DIM)
            self._mark_cleared()
            return

        skills = fetch_random_skills()
        self._sep()
        self._log("  🌀  SKILL ROOM — Choose a passive skill!", BLUE)
        self._log(f"  ({len(current)}/{MAX_SKILLS} slots used)", DIM)

        win = tk.Toplevel(self)
        win.title("Choose a Skill")
        win.configure(bg=PANEL)
        win.grab_set()

        tk.Label(win, text="🌀  SKILL ROOM",
                 font=("Courier New", 14, "bold"), bg=PANEL, fg=BLUE).pack(pady=(10, 2))
        tk.Label(win,
                 text=f"Pick ONE passive skill  ({len(current)}/{MAX_SKILLS} slots used)",
                 font=FS, bg=PANEL, fg=DIM).pack(pady=(0, 8))

        for sk in skills:
            # Disable if already known
            already = any(p["keyword"] == sk["keyword"] for p in current)
            card = tk.Frame(win, bg="#0d1a2e", relief="ridge", bd=1)
            card.pack(fill="x", padx=14, pady=4)
            tk.Label(card, text=sk["name"].upper(),
                     font=FB, bg="#0d1a2e", fg=BLUE).pack(anchor="w", padx=8, pady=(6, 0))
            tk.Label(card, text=sk["desc"],
                     font=FS, bg="#0d1a2e", fg=TEXT,
                     wraplength=320, justify="left").pack(anchor="w", padx=8, pady=(2, 6))
            if already:
                tk.Label(card, text="✓ Already learned",
                         font=FS, bg="#0d1a2e", fg=GREEN).pack(anchor="e", padx=8, pady=(0, 6))
            else:
                tk.Button(card, text="Learn This",
                          font=FS, bg=BLUE, fg="white",
                          relief="flat", cursor="hand2",
                          command=lambda s=sk, w=win: self._learn_skill(s, w)
                          ).pack(anchor="e", padx=8, pady=(0, 6))

        tk.Button(win, text="Skip", font=FS, bg=DIM, fg="white",
                  relief="flat", cursor="hand2",
                  command=lambda: self._skip_skill(win)
                  ).pack(pady=8)

    def _learn_skill(self, skill, win):
        win.destroy()
        self.player["passives"].append(skill)
        self._sep()
        self._log(f"  🌀  Learned: {skill['name'].upper()}!", BLUE)
        self._log(f"     {skill['desc']}", DIM)
        # Endurance: expand max HP immediately
        if skill["keyword"] == "endurance":
            self.player["max_hp"] = self.player.get("max_hp", self.MAX_HP) + 20
            self.player["hp"] = min(self.player["max_hp"], self.player["hp"] + 20)
            self._log(f"  ★  Max HP increased to {self.player['max_hp']}!", GREEN)
        self._refresh()
        self._refresh_skills()
        self._mark_cleared()

    def _skip_skill(self, win):
        win.destroy()
        self._log("  → You passed on the skills.", DIM)
        self._mark_cleared()

    # ════════════════════════════════════════
    #  BATTLE ENGINE
    # ════════════════════════════════════════

    def _has_skill(self, keyword: str) -> bool:
        """Check if the player has learned a skill by keyword."""
        return any(s["keyword"] == keyword
                   for s in self.player.get("passives", []))

    def _begin_battle(self, enemy, is_boss=False):
        self.enemy            = enemy
        self.e_hp             = enemy["hp"]
        self.battle_over      = False
        self.in_boss          = is_boss
        self.boss_turn_count  = 0
        self.passive_stacks   = {}
        self.second_wind_used = False
        self._log("  ⚔  BATTLE START!", ACCENT)

        # war_veteran: +3 temporary ATK each battle (tracked separately so
        # it doesn't permanently stack — we note it in passive_stacks)
        if self._has_skill("war_veteran"):
            self.passive_stacks["war_veteran_bonus"] = 3
            self._log("  🌀  War Veteran! +3 ATK this battle.", BLUE)

        # Show boss passive
        if is_boss and enemy.get("passive", "none") != "none":
            pname = enemy["passive"].replace("_", " ").upper()
            self._log(f"  ★  BOSS PASSIVE: {pname}", "#ff9900")
            self._log(f"     {enemy['passive_desc']}", DIM)

        # Apply battle-start passives
        self._apply_boss_passive_start()

        self._refresh()
        self._btns(True)

    def _apply_boss_passive_start(self):
        """Passives that trigger once at battle start."""
        if not self.in_boss:
            return
        passive = self.enemy.get("passive", "none")
        if passive == "war_cry":
            self.enemy["atk"] += 4
            self._log(f"  ★  War Cry! Boss ATK raised to {self.enemy['atk']}!", "#ff9900")
        elif passive == "tyrant_aura":
            self.enemy["atk"] = max(1, self.enemy["atk"] - 3)
            self.player["hp"] = max(1, self.player["hp"] - 5)
            self._log(f"  ★  Tyrant Aura! Boss ATK -{3}, you lose 5 HP.", "#ff9900")
        elif passive == "bone_armor":
            self.passive_stacks["bone_armor_remaining"] = 20
            self._log(f"  ★  Bone Armor! First 20 damage is negated!", "#ff9900")

    def _apply_boss_passive_on_attack(self, raw_damage: int) -> int:
        """Modify outgoing player damage based on boss passive. Returns adjusted damage."""
        if not self.in_boss:
            return raw_damage
        passive = self.enemy.get("passive", "none")
        dmg = raw_damage

        if passive == "bone_armor":
            remaining = self.passive_stacks.get("bone_armor_remaining", 0)
            if remaining > 0:
                absorbed = min(remaining, dmg)
                dmg -= absorbed
                self.passive_stacks["bone_armor_remaining"] = remaining - absorbed
                if absorbed > 0:
                    self._log(f"  ★  Bone Armor absorbed {absorbed} damage! ({remaining - absorbed} remaining)", "#ff9900")

        elif passive == "armor_shred":
            # Each player hit lowers enemy DEF by 1 (min 0)
            if self.enemy["def"] > 0:
                self.enemy["def"] = max(0, self.enemy["def"] - 1)
                self._log(f"  ★  Armor Shred! Enemy DEF reduced to {self.enemy['def']}.", "#ff9900")

        elif passive == "fortified":
            # DEF can't go below 8
            if self.enemy["def"] < 8:
                self.enemy["def"] = 8

        return max(0, dmg)

    def _apply_boss_passive_on_enemy_turn(self, base_dmg: int) -> int:
        """Modify boss damage and trigger per-turn passives. Returns final damage to player."""
        if not self.in_boss:
            return base_dmg
        passive = self.enemy.get("passive", "none")
        self.boss_turn_count += 1
        dmg = base_dmg

        if passive == "regeneration":
            heal = 4           # reduced from 6
            self.e_hp = min(self.enemy["hp"], self.e_hp + heal)
            self._log(f"  ★  Regeneration! Boss heals {heal} HP.", "#ff9900")

        elif passive == "phase_strike":
            if random.random() < 0.25:   # reduced from 30%
                dmg = max(4, self.enemy["atk"] + random.randint(-2, 2))
                self._log(f"  ★  Phase Strike! Bypasses armor — {dmg} dmg!", "#ff9900")

        elif passive == "cursed_strikes":
            # Only every other turn to reduce stacking misery
            if self.boss_turn_count % 2 == 0:
                self.player["atk"] = max(1, self.player["atk"] - 1)
                self._log(f"  ★  Cursed Strikes! Your ATK → {self.player['atk']}.", "#ff9900")

        elif passive == "poison_cloud":
            dmg += 0   # extra handled in _enemy_turn pre-hit

        elif passive == "void_drain":
            drain = 3   # reduced from 5
            self.player["hp"] = max(0, self.player["hp"] - drain)
            self.e_hp = min(self.enemy["hp"], self.e_hp + drain)
            self._log(f"  ★  Void Drain! -{drain} HP from you.", "#ff9900")

        elif passive == "war_cry":
            if self.boss_turn_count % 3 == 0:
                self.enemy["atk"] += 2
                self._log(f"  ★  War Cry! Boss ATK → {self.enemy['atk']}.", "#ff9900")

        elif passive == "absolute_dominion":
            if self.boss_turn_count % 3 == 0:   # slowed from every 2
                self.enemy["atk"] += 2           # reduced from 3
                self._log(f"  ★  Absolute Dominion! Boss ATK → {self.enemy['atk']}!", "#ff9900")
            # Ignore 25% of player DEF (reduced from 40%)
            def_ignored = int(self.player["def"] * 0.25)
            dmg += def_ignored
            if def_ignored > 0:
                self._log(f"  ★  Absolute Dominion ignores {def_ignored} DEF!", "#ff9900")

        elif passive == "leaden_weight":
            dmg += 3   # reduced from 4

        return dmg

    def _do_attack(self):
        if self.battle_over: return
        self._btns(False)
        p, e = self.player, self.enemy

        # Base ATK includes war_veteran temp bonus if any
        effective_atk = p["atk"] + self.passive_stacks.get("war_veteran_bonus", 0)
        raw_dmg = max(3, effective_atk - e["def"] + random.randint(-2, 2))

        # ── Player skill passives (attack side) ──
        # last_stand: +5 damage when HP ≤ 20
        if self._has_skill("last_stand") and p["hp"] <= 20:
            raw_dmg += 5
            self._log("  🌀  Last Stand! +5 bonus damage.", BLUE)

        # predator: +4 damage when enemy HP < 40%
        if self._has_skill("predator") and self.e_hp < self.enemy["hp"] * 0.4:
            raw_dmg += 4
            self._log("  🌀  Predator! Enemy is weakened — +4 damage.", BLUE)

        # adrenaline: +3 ATK when own HP < 40%
        if self._has_skill("adrenaline") and p["hp"] < self._max_hp * 0.4:
            raw_dmg += 3
            self._log("  🌀  Adrenaline! +3 damage from desperation.", BLUE)

        # shield_crush: reduce enemy DEF by 1 each hit
        if self._has_skill("shield_crush") and e["def"] > 0:
            e["def"] = max(0, e["def"] - 1)
            self._log(f"  🌀  Shield Crush! Enemy DEF → {e['def']}.", BLUE)

        # ── Relic passives (kept for backward compat) ──
        if any(it.get("passive_name") == "blood_price" for it in p.get("inventory", [])):
            raw_dmg += 8
            p["hp"] = max(1, p["hp"] - 3)
            self._log("  ★  Blood Price! +8 dmg, -3 HP.", "#ff9900")

        if any(it.get("passive_name") == "sapping_curse" for it in p.get("inventory", [])):
            raw_dmg = max(1, raw_dmg - 5)
            self._log("  ★  Sapping Curse! -5 dmg.", "#ff9900")

        if any(it.get("passive_name") == "divine_cleave" for it in p.get("inventory", [])):
            if random.random() < 0.25:
                raw_dmg *= 2
                self._log("  ★  Divine Cleave! DOUBLE damage!", "#ff9900")

        # quick_strike: 20% chance to hit twice
        double_hit = self._has_skill("quick_strike") and random.random() < 0.20

        # Boss passive may absorb/modify the damage
        final_dmg = self._apply_boss_passive_on_attack(raw_dmg)
        self.e_hp -= final_dmg
        self._flash("enemy")
        self._log(f"  ▸ You strike for {final_dmg} damage!", TEXT)

        # bloodlust: heal 4 HP per hit
        if self._has_skill("bloodlust"):
            gained = min(self._max_hp, p["hp"] + 4) - p["hp"]
            p["hp"] += gained
            if gained > 0:
                self._log(f"  🌀  Bloodlust! Healed {gained} HP.", GREEN)

        # quick_strike second hit
        if double_hit and self.e_hp > 0:
            bonus = self._apply_boss_passive_on_attack(max(2, raw_dmg // 2))
            self.e_hp -= bonus
            self._log(f"  🌀  Quick Strike! Second hit for {bonus} damage!", BLUE)
            if self._has_skill("bloodlust"):
                gained = min(self._max_hp, p["hp"] + 4) - p["hp"]
                p["hp"] += gained

        self._refresh()
        if self.e_hp <= 0:
            self._on_victory()
            return
        self.after(420, self._enemy_turn)

    def _enemy_turn(self):
        p, e = self.player, self.enemy

        # arcane_insight: 15% chance to skip enemy attack entirely
        if self._has_skill("arcane_insight") and random.random() < 0.15:
            self._log("  🌀  Arcane Insight! You predicted the attack — evaded!", BLUE)
            self._btns(True)
            return

        # Poison cloud fires before the hit
        if self.in_boss and e.get("passive") == "poison_cloud":
            p["hp"] = max(0, p["hp"] - 4)
            self._log("  ★  Poison Cloud! You lose 4 HP.", "#ff9900")
            self._refresh()
            if p["hp"] <= 0:
                if not self._check_undying() and not self._check_second_wind():
                    self._game_over()
                return

        base_dmg = max(2, e["atk"] - p["def"] + random.randint(-2, 2))
        final_dmg = self._apply_boss_passive_on_enemy_turn(base_dmg)

        # iron_will: flat -2 damage reduction
        if self._has_skill("iron_will"):
            final_dmg = max(1, final_dmg - 2)

        # mirror_thorns relic: reflect 30%
        if any(it.get("passive_name") == "mirror_thorns" for it in p.get("inventory", [])):
            reflect = int(final_dmg * 0.30)
            self.e_hp = max(0, self.e_hp - reflect)
            if reflect > 0:
                self._log(f"  ★  Mirror Thorns reflects {reflect} damage!", "#ff9900")

        # counter_stance: reflect flat 2 damage
        if self._has_skill("counter_stance"):
            self.e_hp = max(0, self.e_hp - 2)
            self._log("  🌀  Counter Stance! Reflected 2 damage.", BLUE)

        p["hp"] = max(0, p["hp"] - final_dmg)
        self._flash("player")
        self._log(f"  ◂ {e['name'].replace('_',' ')} hits for {final_dmg}!", YELLOW)
        self._refresh()

        if p["hp"] <= 0:
            if not self._check_undying() and not self._check_second_wind():
                self._game_over()
            return

        # resilience: heal 5 HP at end of turn
        if self._has_skill("resilience"):
            gained = min(self._max_hp, p["hp"] + 5) - p["hp"]
            p["hp"] += gained
            if gained > 0:
                self._log(f"  🌀  Resilience! +{gained} HP.", GREEN)

        # eternal_ward relic: +3 HP post-hit
        if any(it.get("passive_name") == "eternal_ward" for it in p.get("inventory", [])):
            p["hp"] = min(self._max_hp, p["hp"] + 3)

        # vitality_surge relic: +8 HP per turn
        if any(it.get("passive_name") == "vitality_surge" for it in p.get("inventory", [])):
            gained = min(self._max_hp, p["hp"] + 8) - p["hp"]
            p["hp"] += gained
            if gained > 0:
                self._log(f"  ★  Vitality Surge! +{gained} HP.", "#ff9900")

        self._refresh()
        self._btns(True)

    def _do_flee(self):
        if self.battle_over: return
        cost = 15
        self.player["hp"] = max(0, self.player["hp"] - cost)
        self._log(f"  🏃 You fled! Lost {cost} HP.", DIM)
        self._refresh()
        if self.player["hp"] <= 0:
            self._game_over()
            return
        self.battle_over = True
        self.enemy       = {}
        self._btns(False)
        # Only reset the room if we fled a regular room (not a boss)
        if self.current_room_idx is not None:
            self.floor_rooms[self.current_room_idx][3] = False
            self.current_room_idx = None
            self._build_map()
        self._refresh()
        self._log("  Room left open -- you can retry it later.", DIM)

    def _do_bag(self):
        if self.battle_over: return
        pool = [it for it in self.player["inventory"] if it["type"] == "consumable"]
        if not pool:
            self._log("  🎒 No consumables in bag!", DIM)
            return
        self.consumables_shown = pool
        self._btns(False)

        win = tk.Toplevel(self)
        win.title("Use Item")
        win.configure(bg=PANEL)
        win.grab_set()
        tk.Label(win, text="── Your Bag ──", font=FM,
                 bg=PANEL, fg=ACCENT).pack(pady=6)
        for idx, it in enumerate(pool):
            bline = f"+{it['bval']} {it['bstat'].upper()}"
            dline = (f"  /  -{it['dval']} {it['dstat'].upper()}"
                     if it["dstat"] != "none" else "")
            lbl = f"[{idx+1}] {it['name'].replace('_',' ')}  ({bline}{dline})"
            tk.Button(win, text=lbl, font=FS, bg=BG, fg=TEXT,
                      activebackground=ACCENT, relief="flat", cursor="hand2",
                      command=lambda i=idx, w=win: self._use_item(i, w)
                      ).pack(fill="x", padx=10, pady=2)
        tk.Button(win, text="Cancel", font=FS, bg=DIM, fg="white",
                  relief="flat",
                  command=lambda: (win.destroy(), self._btns(True))
                  ).pack(pady=6)

    def _use_item(self, idx, win):
        win.destroy()
        it = self.consumables_shown[idx]
        self.player["inventory"].remove(it)
        self._apply_effects(it, announce=True)
        self._refresh()
        self._refresh_inv()
        # absolute_dominion: boss heals 10 when player uses an item
        if self.in_boss and self.enemy.get("passive") == "absolute_dominion":
            self.e_hp = min(self.enemy["hp"], self.e_hp + 10)
            self._log("  ★  Absolute Dominion! Boss heals 10 HP from your item use.", "#ff9900")
            self._refresh()
        self.after(300, self._enemy_turn)

    # ════════════════════════════════════════
    #  ITEM EFFECTS
    # ════════════════════════════════════════

    def _apply_effects(self, it, announce=False):
        bstat, bval = it["bstat"], it["bval"]
        dstat, dval = it["dstat"], it["dval"]

        if bstat == "hp":
            gained = min(self._max_hp, self.player["hp"] + bval) - self.player["hp"]
            self.player["hp"] += gained
            if announce: self._log(f"  ✨ HP +{gained}!", GREEN)
        elif bstat == "attack":
            self.player["atk"] += bval
            if announce: self._log(f"  ✨ ATK +{bval}!", GREEN)
        elif bstat == "defense":
            self.player["def"] += bval
            if announce: self._log(f"  ✨ DEF +{bval}!", GREEN)

        if dstat != "none" and dval > 0:
            if dstat == "hp":
                self.player["hp"] = max(0, self.player["hp"] - dval)
                if announce: self._log(f"  ⚠  HP -{dval}…", ACCENT)
            elif dstat == "attack":
                self.player["atk"] = max(1, self.player["atk"] - dval)
                if announce: self._log(f"  ⚠  ATK -{dval}…", ACCENT)
            elif dstat == "defense":
                self.player["def"] = max(0, self.player["def"] - dval)
                if announce: self._log(f"  ⚠  DEF -{dval}…", ACCENT)

    # ════════════════════════════════════════
    #  VICTORY & ITEM DROP
    # ════════════════════════════════════════

    def _on_victory(self):
        self.battle_over = True
        self._btns(False)
        ename = self.enemy["name"].replace("_", " ").upper()
        self._log(f"  🎉 {ename} defeated!", GREEN)

        # battle_trance: +1 ATK permanently on kill
        if self._has_skill("battle_trance"):
            self.player["atk"] += 1
            self._log(f"  🌀  Battle Trance! ATK → {self.player['atk']}.", BLUE)

        # fortify: +1 DEF permanently after each battle
        if self._has_skill("fortify"):
            self.player["def"] += 1
            self._log(f"  🌀  Fortify! DEF → {self.player['def']}.", BLUE)

        self.enemy = {}
        self._refresh()

        if self.in_boss:
            # Mark boss as cleared so the button greys out
            self.boss_cleared = True
            self._build_map()
            self.after(500, self._after_boss)
        else:
            # Mark the regular room cleared
            self._mark_cleared()
            dropped = self._roll_drop()
            self._log_drop(dropped)
            self._show_item_choice(dropped, after_fn=lambda: None)

    def _roll_drop(self):
        """
        Roll for an item drop.  Rare relic chance increases each floor:
          Floor 1:  3%   Floor 2:  6%   Floor 3: 10%
          Floor 4: 15%   Floor 5: 22%
        Within common pool: consumables 3×, gear 1×.
        Within rare pool:   all relics equally weighted.
        """
        rare_chances = {1: 0.03, 2: 0.06, 3: 0.10, 4: 0.15, 5: 0.22}
        rare_chance  = rare_chances.get(self.floor, 0.03)

        if self.all_rare_items and random.random() < rare_chance:
            return random.choice(self.all_rare_items)

        # Common drop — consumables appear more often
        weights = [3 if it["type"] == "consumable" else 1
                   for it in self.all_items]
        return random.choices(self.all_items, weights=weights, k=1)[0]

    def _log_drop(self, item):
        self._sep()
        if item.get("rare"):
            self._log("  ✦  RARE RELIC FOUND!  ✦", "#ff9900")
        else:
            self._log("  🎁  Item found!", YELLOW)
        self._log(f"  ▸ {item['name'].replace('_',' ').upper()}  [{item['type'].upper()}]", TEXT)
        self._log(f"  {item['desc']}", DIM)
        buff  = f"+{item['bval']} {item['bstat'].upper()}" if item['bval'] > 0 else ""
        debuf = (f"  /  -{item['dval']} {item['dstat'].upper()}"
                 if item["dstat"] != "none" and item["dval"] > 0 else "")
        if buff or debuf:
            fx_color = "#ff9900" if item.get("rare") else (YELLOW if debuf else GREEN)
            self._log(f"  Effect: {buff}{debuf}", fx_color)
        self._sep()

    def _show_item_choice(self, item, after_fn):
        is_rare = item.get("rare", False)
        win = tk.Toplevel(self)
        win.title("✦ RARE RELIC!" if is_rare else "Item Found!")
        win.configure(bg="#2a1a00" if is_rare else PANEL)
        win.grab_set()

        header_color = "#ff9900" if is_rare else YELLOW
        bg           = "#2a1a00" if is_rare else PANEL
        border_color = "#ff9900" if is_rare else PANEL

        if is_rare:
            tk.Label(win, text="✦  RARE RELIC  ✦",
                     font=("Courier New", 14, "bold"),
                     bg=bg, fg="#ff9900").pack(pady=(10, 2))
            tk.Label(win, text="This item can make or break your run.",
                     font=FS, bg=bg, fg="#cc7700").pack(pady=(0, 6))
        else:
            tk.Label(win, text="🎁  ITEM FOUND  🎁",
                     font=FM, bg=bg, fg=YELLOW).pack(pady=8)

        tk.Label(win, text=item["name"].replace("_", " ").upper(),
                 font=("Courier New", 13, "bold"), bg=bg, fg=TEXT).pack()
        tk.Label(win, text=f"[{item['type'].upper()}]",
                 font=FS, bg=bg, fg=DIM).pack()

        buff  = f"+{item['bval']} {item['bstat'].upper()}" if item["bval"] > 0 else ""
        debuf = (f"  /  -{item['dval']} {item['dstat'].upper()}"
                 if item["dstat"] != "none" and item["dval"] > 0 else "")
        fx_color = "#ff9900" if is_rare else (YELLOW if debuf else GREEN)
        if buff or debuf:
            tk.Label(win, text=f"Effect: {buff}{debuf}",
                     font=FB, bg=bg, fg=fx_color).pack(pady=2)

        if item.get("rare") and item.get("passive_name", "none") != "none":
            pname = item["passive_name"].replace("_", " ").upper()
            tk.Label(win, text=f"★ PASSIVE: {pname}",
                     font=FB, bg=bg, fg="#ff9900").pack(pady=(4, 0))
            tk.Label(win, text=item.get("passive_desc", ""),
                     font=FS, bg=bg, fg="#cc7700", wraplength=320).pack(pady=(0, 4))

        tk.Label(win, text=item["desc"], font=FS, bg=bg, fg=DIM,
                 wraplength=320).pack(pady=4)

        if item["type"] == "consumable":
            note = "Consumable — use from bag during battle."
        elif is_rare:
            note = "Relic — passive effect applied immediately on pickup."
        else:
            note = "Passive — effect applied immediately on pickup."
        tk.Label(win, text=note, font=FS, bg=bg, fg=BLUE).pack(pady=(0, 4))

        bf = tk.Frame(win, bg=bg)
        bf.pack(pady=8)
        tk.Button(bf, text="Pick Up", font=FM, bg=GREEN, fg="white",
                  relief="flat", cursor="hand2",
                  command=lambda: self._pick_item(item, win, True, after_fn)
                  ).pack(side="left", padx=6, ipadx=8, ipady=4)
        tk.Button(bf, text="Leave It", font=FM, bg=DIM, fg="white",
                  relief="flat", cursor="hand2",
                  command=lambda: self._pick_item(item, win, False, after_fn)
                  ).pack(side="left", padx=6, ipadx=8, ipady=4)

    def _pick_item(self, item, win, take, after_fn):
        win.destroy()
        if take:
            if item["type"] == "consumable":
                self.player["inventory"].append(item)
                self._log(f"  -> Added to bag.", GREEN)
            else:
                # Apply stat effects immediately
                self._apply_effects(item, announce=True)
                # Always store in inventory so passive_name checks work
                self.player["inventory"].append(item)
                self._log(f"  -> Equipped {item['name'].replace('_',' ')}!", GREEN)
            self._refresh()
            self._refresh_inv()
        else:
            self._log("  -> Left the item behind.", DIM)
        after_fn()

    # ════════════════════════════════════════
    #  BOSS
    # ════════════════════════════════════════

    def _enter_boss(self):
        if not self.battle_over:
            self._log("  ⚠  Finish the battle first!", ACCENT)
            return
        boss = fetch_boss(self.floor)
        label = "FINAL BOSS" if self.floor == 5 else f"FLOOR {self.floor} BOSS"
        # Scale pool bosses (floors 1-4). Final boss (floor 5) uses its own fixed stats.
        if self.floor < 5:
            hp_scales  = {1: 1.00, 2: 1.35, 3: 1.75, 4: 2.20}
            atk_scales = {1: 1.00, 2: 1.30, 3: 1.65, 4: 2.05}
            def_scales = {1: 1.00, 2: 1.20, 3: 1.50, 4: 1.85}
            boss["hp"]  = int(boss["hp"]  * hp_scales[self.floor])
            boss["atk"] = int(boss["atk"] * atk_scales[self.floor])
            boss["def"] = int(boss["def"] * def_scales[self.floor])
        self._sep()
        self._log(f"  💀  {label}!", ACCENT)
        self._log(f"  {boss['name'].replace('_',' ').upper()}", YELLOW)
        self._log(f"  \"{boss['desc']}\"", DIM)
        self._log(f"  HP {boss['hp']}  ATK {boss['atk']}  DEF {boss['def']}", ACCENT)
        self._sep()
        self._begin_battle(boss, is_boss=True)

    def _after_boss(self):
        if self.floor == 5:
            self._victory()
        else:
            self._sep()
            self._log(f"  🏆 Floor {self.floor} complete!", GREEN)
            self._log(f"  Advancing to Floor {self.floor + 1}...", BLUE)
            self.after(800, lambda: self._new_floor(self.floor + 1))

    # ════════════════════════════════════════
    #  END STATES
    # ════════════════════════════════════════

    def _check_undying(self) -> bool:
        """Once per floor, survive a lethal hit with 1 HP (Undying skill)."""
        if self.undying_used:
            return False
        if self._has_skill("undying"):
            self.undying_used = True
            self.player["hp"] = 1
            self._log("  🌀  UNDYING! You cling to life with 1 HP!", GREEN)
            self._refresh()
            self._btns(True)
            return True
        return False

    def _check_second_wind(self) -> bool:
        """If player holds soulstone_pendant and hasn't used second wind, revive with 20 HP."""
        if self.second_wind_used:
            return False
        has_sw = any(it.get("passive_name") == "second_wind" for it in self.player.get("inventory", []))
        if has_sw:
            self.second_wind_used = True
            self.player["hp"] = 20
            self._log("  ★  SECOND WIND! Soulstone Pendant revives you with 20 HP!", GREEN)
            self._refresh()
            self._btns(True)
            return True
        return False

    def _game_over(self):
        self.battle_over = True
        self._btns(False)
        self._log("\n  💀 YOU HAVE FALLEN…", ACCENT)
        self._draw_arena()
        messagebox.showinfo("Game Over",
            f"💀 Defeated on Floor {self.floor}.\n\n"
            f"Final Stats\n"
            f"HP: 0  |  ATK: {self.player['atk']}  |  DEF: {self.player['def']}\n\n"
            "Better luck next time, adventurer.")
        self.destroy()

    def _victory(self):
        self._log("\n  🏆 YOU CONQUERED THE LABYRINTH!", GREEN)
        messagebox.showinfo("VICTORY!",
            "🏆 LEGENDARY VICTORY!\n\n"
            "You defeated the Labyrinth Overlord!\n\n"
            f"Final Stats\n"
            f"HP: {self.player['hp']}  |  ATK: {self.player['atk']}  "
            f"|  DEF: {self.player['def']}")
        self.destroy()


# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = DungeonApp()
    app.mainloop()
 
