"""cactus.py をゲーム内APIを模したサンドボックスで実行して検証する．

ドローンは同期実行（親の位置を退避して子を走らせる）．線は互いに独立なので
最終状態は並列実行と同じになる．tick はドローンごとに分けて数え，
段階ごとに「最も時間のかかったドローン」を実時間の目安として報告する．

引数: n seed [maxdrones]
"""
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))

import ast
import random
import sys

SRC = _os.environ.get("SRC", _os.path.join(_HERE, "..", "src", "cactus.py"))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 1
MAXD = int(sys.argv[3]) if len(sys.argv) > 3 else 32
GROW = 400          # 植えてからこの tick で育ちきる

North, East, South, West = "N", "E", "S", "W"
DXY = {North: (0, 1), East: (1, 0), South: (0, -1), West: (-1, 0)}


class Items:
    Cactus = "Cactus"


class Entities:
    Cactus = "Cactus"


class Grounds:
    Grassland = "Grassland"
    Soil = "Soil"


class W:
    pass


def reset(seed):
    W.rng = random.Random(seed)
    W.n = N
    W.x = 0
    W.y = 0
    W.cactus = 0
    W.size = {}      # (x,y) -> サイズ 0..9（無ければ None）
    W.plant_t = {}   # (x,y) -> 植えた時刻
    W.ground = {}
    for x in range(N):
        for y in range(N):
            W.ground[(x, y)] = Grounds.Grassland
            W.size[(x, y)] = None
    W.t = 0          # 全体の経過（成長判定用）
    W.cur = 0        # いま走っているドローンの tick
    W.phase_max = 0  # その段階で最も重かったドローンの tick
    W.parent = 0
    W.depth = 0
    W.swaps = 0
    W.moves = 0
    W.harvested = 0
    W.rounds = 0
    W.touched = set()
    W.last_grid = {}
    W.child = []


def tick(k=1):
    W.cur += k
    W.t += k


def get_world_size():
    tick(); return float(W.n)


def get_pos_x():
    tick(); return float(W.x)


def get_pos_y():
    tick(); return float(W.y)


def num_items(it):
    tick(); return W.cactus


def get_tick_count():
    return W.cur


def quick_print(*a):
    print("   quick_print:", *a)


def print_(*a):
    print("   PRINT:", *a)


def clear():
    tick(200)
    for k in W.size:
        W.size[k] = None
    W.x = 0
    W.y = 0


def move(d):
    dx, dy = DXY[d]
    nx, ny = W.x + dx, W.y + dy
    if nx < 0 or nx >= W.n or ny < 0 or ny >= W.n:
        tick(); return False
    tick(200); W.moves += 1
    W.x, W.y = nx, ny
    return True


def get_ground_type():
    tick(); return W.ground[(W.x, W.y)]


def till():
    tick(200)
    k = (W.x, W.y)
    if W.ground[k] == Grounds.Soil:
        W.ground[k] = Grounds.Grassland
    else:
        W.ground[k] = Grounds.Soil


def plant(e):
    k = (W.x, W.y)
    if W.ground[k] != Grounds.Soil:
        tick(); return False        # サボテンは畑にしか植えられない
    tick(200)
    W.size[k] = W.rng.randrange(10)
    W.plant_t[k] = W.t
    return True


def can_harvest():
    tick()
    k = (W.x, W.y)
    if W.size[k] is None:
        return False
    return W.t - W.plant_t[k] >= GROW


def measure(direction=None):
    tick()
    if direction is None:
        return W.size[(W.x, W.y)]
    dx, dy = DXY[direction]
    nx, ny = W.x + dx, W.y + dy
    if nx < 0 or nx >= W.n or ny < 0 or ny >= W.n:
        return None
    return W.size[(nx, ny)]


def note_line(kind, idx):
    W.touched.add((kind, idx))


def swap(d):
    tick(200)
    dx, dy = DXY[d]
    nx, ny = W.x + dx, W.y + dy
    if nx < 0 or nx >= W.n or ny < 0 or ny >= W.n:
        return None
    a, b = (W.x, W.y), (nx, ny)
    W.size[a], W.size[b] = W.size[b], W.size[a]
    W.plant_t[a], W.plant_t[b] = W.plant_t.get(b, 0), W.plant_t.get(a, 0)
    W.swaps += 1
    return None


def sorted_ok(x, y):
    n = W.n
    s = W.size[(x, y)]
    if s is None:
        return False
    if W.t - W.plant_t[(x, y)] < GROW:
        return False
    for d, sign in ((East, 1), (North, 1), (West, -1), (South, -1)):
        dx, dy = DXY[d]
        nx, ny = x + dx, y + dy
        if 0 <= nx < n and 0 <= ny < n:
            o = W.size[(nx, ny)]
            if o is None:
                return False
            if sign > 0 and o < s:
                return False
            if sign < 0 and o > s:
                return False
    return True


def harvest():
    tick(200)
    W.last_grid = dict(W.size)
    k = (W.x, W.y)
    if W.size[k] is None:
        return False
    # 整列している区画は連鎖して収穫される
    if sorted_ok(k[0], k[1]):
        cnt = 0
        for kk in list(W.size):
            if W.size[kk] is not None and sorted_ok(kk[0], kk[1]):
                cnt += 1
        for kk in list(W.size):
            if W.size[kk] is not None and sorted_ok(kk[0], kk[1]):
                W.size[kk] = None
        W.cactus += cnt * cnt
        W.harvested = cnt
    else:
        W.cactus += 1
        W.size[k] = None
        W.harvested = 1
    W.rounds += 1
    return True


def num_drones():
    tick(); return 1 + W.depth


def max_drones():
    tick(); return MAXD


class Handle:
    def __init__(self, ticks):
        self.ticks = ticks


def spawn_drone(f):
    tick(200)
    if 1 + W.depth >= MAXD:
        return None
    # 同期実行：親の位置と tick を退避して子を走らせる
    px, py, pc = W.x, W.y, W.cur
    W.depth += 1
    W.cur = 0
    f()
    child = W.cur
    W.depth -= 1
    W.x, W.y, W.cur = px, py, pc
    W.child.append(child)
    if child > W.phase_max:
        W.phase_max = child
    return Handle(child)


def wait_for(h):
    tick(); return None


def has_finished(h):
    tick(); return True


def grange(*a):
    return range(*[int(v) for v in a])


src = open(SRC).read()
ast.parse(src)
import re
src = re.sub(r"TARGET_CACTUS = \d+", "TARGET_CACTUS = %d" % ((N * N) ** 2), src, count=1)

env = {
    "North": North, "East": East, "South": South, "West": West,
    "Items": Items, "Entities": Entities, "Grounds": Grounds,
    "get_world_size": get_world_size, "get_pos_x": get_pos_x, "get_pos_y": get_pos_y,
    "num_items": num_items, "get_tick_count": get_tick_count, "quick_print": quick_print,
    "print": print_, "move": move, "measure": measure, "swap": swap,
    "get_ground_type": get_ground_type, "till": till, "plant": plant,
    "can_harvest": can_harvest, "harvest": harvest, "clear": clear,
    "spawn_drone": spawn_drone, "wait_for": wait_for, "has_finished": has_finished,
    "num_drones": num_drones, "max_drones": max_drones,
    "abs": abs, "len": len, "range": grange,
}

sys.setrecursionlimit(100000)
reset(SEED)
exec(compile(src, SRC, "exec"), env)

def mono_ok():
    for x in range(N):
        for y in range(N):
            s0 = W.last_grid.get((x, y))
            if s0 is None:
                return False
            if x + 1 < N and W.last_grid[(x + 1, y)] < s0:
                return False
            if y + 1 < N and W.last_grid[(x, y + 1)] < s0:
                return False
    return True


full = N * N
ok = (W.harvested == full) and (W.cactus >= full * full) and mono_ok()
half = len(W.child) // 2
if half > 0:
    a = sorted(W.child[:half]); b = sorted(W.child[half:])
    open("DUMPCHILD.txt","w").write(repr((a,b)))
    print("  列の1機あたり: 最小=%d 中央=%d 平均=%d 最大=%d  （最大/平均=%.3f）"
          % (a[0], a[len(a)//2], sum(a)//len(a), a[-1], a[-1]/(sum(a)/len(a))))
    print("  行の1機あたり: 最小=%d 中央=%d 平均=%d 最大=%d  （最大/平均=%.3f）"
          % (b[0], b[len(b)//2], sum(b)//len(b), b[-1], b[-1]/(sum(b)/len(b))))
if half > 0:
    print("  段階別の最大tick: 列=%d 行=%d  （機数 列=%d 行=%d）"
          % (max(W.child[:half]), max(W.child[half:]), half, len(W.child) - half))
print("n=%d seed=%d maxdrones=%d : 収穫=%d/%d  サボテン=%d  交換=%d 移動=%d  "
      "1機の最大tick=%d  %s"
      % (N, SEED, MAXD, W.harvested, full, W.cactus, W.swaps, W.moves,
         W.phase_max, "OK" if ok else "*** FAIL ***"))
if not ok:
    sys.exit(1)
