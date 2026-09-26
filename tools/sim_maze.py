"""maze_lb.py を「ゲーム内API」を模したサンドボックスで実行して検証する．
ドローンは1台のみ（max_drones=1）に固定し，探索・経路・再利用回数・迷路の作り直しを確認する．
"""
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))

import ast
import random
import sys

SRC = _os.environ.get("SRC", _os.path.join(_HERE, "..", "src", "maze_lb.py"))
N = 7
START_GOLD = 9999999   # すでに大量の金を持っている状態
MAXR = 5          # 再配置上限（テスト用に小さく）
TARGET_TEST = 800  # 3つの迷路が必要になる額

North, East, South, West = "N", "E", "S", "W"
DXY = {North: (0, 1), East: (1, 0), South: (0, -1), West: (-1, 0)}


class Items:
    Gold = "Gold"
    Weird_Substance = "WS"


class Entities:
    Bush = "Bush"
    Hedge = "Hedge"
    Treasure = "Treasure"


class Grounds:
    Grassland = "Grassland"
    Soil = "Soil"


class Unlocks:
    Mazes = "Mazes"


class Leaderboards:
    Maze = "Maze"


class World:
    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.n = N
        self.x = 0
        self.y = 0
        self.gold = START_GOLD
        self.ws = 10 ** 9
        self.maze = False
        self.bush = None          # (x,y) or None
        self.edges = set()        # frozenset({cellA, cellB}) 通行可能
        self.treasure = None
        self.reuse = 0
        self.ticks = 0
        self.moves = 0
        self.mazes_built = 0
        self.ground = Grounds.Soil   # 前のプレイで耕された状態を再現

    # --- 内部 ---
    def cell(self, x, y):
        return x * self.n + y

    def gen_maze(self):
        n = self.n
        self.edges = set()
        start = (self.x, self.y)
        seen = {start}
        stack = [start]
        while stack:
            cx, cy = stack[-1]
            cand = []
            for d in (North, East, South, West):
                dx, dy = DXY[d]
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < n and 0 <= ny < n and (nx, ny) not in seen:
                    cand.append((nx, ny))
            if not cand:
                stack.pop()
                continue
            nx, ny = self.rng.choice(cand)
            self.edges.add(frozenset({self.cell(cx, cy), self.cell(nx, ny)}))
            seen.add((nx, ny))
            stack.append((nx, ny))
        assert len(seen) == n * n
        self.maze = True
        self.mazes_built += 1
        self.reuse = 0
        self.place_treasure()

    def place_treasure(self):
        n = self.n
        while True:
            t = (self.rng.randrange(n), self.rng.randrange(n))
            if t != (self.x, self.y) or self.treasure is None:
                self.treasure = t
                return

    def clear_all(self):
        self.maze = False
        self.edges = set()
        self.treasure = None
        self.bush = None


W = World(3)


def tick(k=1):
    W.ticks += k


def get_world_size():
    tick(); return W.n


def get_pos_x():
    tick(); return W.x


def get_pos_y():
    tick(); return W.y


def num_unlocked(_):
    tick(); return 1


def num_items(it):
    tick()
    return W.gold if it == Items.Gold else W.ws


def get_tick_count():
    return W.ticks


def quick_print(*a):
    print("   quick_print:", *a)


def clear():
    tick(200)
    W.clear_all()
    W.x = 0
    W.y = 0


def can_move(d):
    tick()
    dx, dy = DXY[d]
    nx, ny = W.x + dx, W.y + dy
    if not W.maze:
        return True  # 迷路が無ければ端で回り込む
    if not (0 <= nx < W.n and 0 <= ny < W.n):
        return False
    return frozenset({W.cell(W.x, W.y), W.cell(nx, ny)}) in W.edges


def move(d):
    if not can_move(d):
        tick(); return False
    dx, dy = DXY[d]
    W.x = (W.x + dx) % W.n
    W.y = (W.y + dy) % W.n
    tick(200); W.moves += 1
    return True


def get_entity_type():
    tick()
    if W.maze:
        return Entities.Treasure if (W.x, W.y) == W.treasure else Entities.Hedge
    if W.bush == (W.x, W.y):
        return Entities.Bush
    return None


def measure(direction=None):
    tick()
    if W.maze:
        return (W.treasure[0], W.treasure[1])
    return None


def plant(e):
    if W.ground != Grounds.Grassland:
        tick(); return False      # 畑には茂みを植えられない
    tick(200)
    W.bush = (W.x, W.y)
    return True


def use_item(item, n_=1):
    if W.bush == (W.x, W.y) and not W.maze:
        tick(200); W.ws -= n_
        W.gen_maze()
        return True
    if W.maze and (W.x, W.y) == W.treasure:
        tick(200); W.ws -= n_
        if W.reuse >= MAXR:
            return True            # 上限：動かない・金も増えない
        W.reuse += 1
        W.gold += W.n * W.n
        W.place_treasure()
        return True
    tick(); return False


def harvest():
    if W.maze and (W.x, W.y) == W.treasure:
        tick(200)
        W.gold += W.n * W.n
        W.clear_all()
        return True
    tick(200)
    W.clear_all()
    return True


def get_ground_type():
    tick(); return W.ground


def till():
    tick(200)
    W.ground = Grounds.Grassland if W.ground == Grounds.Soil else Grounds.Soil


def max_drones():
    tick(); return 1


def num_drones():
    tick(); return 1


def spawn_drone(f):
    tick(); return None


def wait_for(h):
    tick(); return {}


def has_finished(h):
    tick(); return True


src = open(SRC).read()
ast.parse(src)               # 構文チェック
src = src.replace("TARGET = 9863168", "TARGET = %d" % TARGET_TEST)
src = src.replace("MAX_REUSE = 300", "MAX_REUSE = %d" % MAXR)

env = {
    "North": North, "East": East, "South": South, "West": West,
    "Items": Items, "Entities": Entities, "Unlocks": Unlocks,
    "Leaderboards": Leaderboards, "Grounds": Grounds,
    "get_ground_type": get_ground_type, "till": till,
    "get_world_size": get_world_size, "get_pos_x": get_pos_x, "get_pos_y": get_pos_y,
    "num_unlocked": num_unlocked, "num_items": num_items, "get_tick_count": get_tick_count,
    "quick_print": quick_print, "clear": clear, "can_move": can_move, "move": move,
    "get_entity_type": get_entity_type, "measure": measure, "plant": plant,
    "use_item": use_item, "harvest": harvest, "max_drones": max_drones,
    "num_drones": num_drones, "spawn_drone": spawn_drone, "wait_for": wait_for,
    "has_finished": has_finished, "abs": abs, "len": len, "range": range,
    "print": quick_print,
}

sys.setrecursionlimit(10000)
exec(compile(src, SRC, "exec"), env)

print("gained    =", W.gold - START_GOLD, "(target %d)" % TARGET_TEST)
print("mazes     =", W.mazes_built)
print("moves     =", W.moves)
print("ticks     =", W.ticks)
assert W.gold - START_GOLD >= TARGET_TEST, "目標額に達していない"
print("OK")
