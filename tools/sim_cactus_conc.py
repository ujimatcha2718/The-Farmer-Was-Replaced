"""並行シミュレータ：ドローンを実際に並行動作させて実時間を測る．

各ドローンを1スレッドとし，ゲームAPIの呼び出しごとに
  1) 全ドローンのうち自分の仮想時刻が最小になるまで待つ
  2) 効果を適用する
  3) 自分の仮想時刻を費用ぶん進める
とする．これで任意の割り込み順序が仮想時刻の順に正しく並ぶ．

引数: src n seed [maxdrones]
"""
import ast
import random
import sys
import threading

SRC = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 8
SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 1
MAXD = int(sys.argv[4]) if len(sys.argv) > 4 else 32
import os
GROW = int(os.environ.get('GROW','400'))
NOMEAS = os.environ.get('NOMEAS')=='1'

North, East, South, West = "N", "E", "S", "W"
DXY = {North: (0, 1), East: (1, 0), South: (0, -1), West: (-1, 0)}


class Items:
    Cactus = "Cactus"


class Entities:
    Cactus = "Cactus"


class Grounds:
    Grassland = "Grassland"
    Soil = "Soil"


class Drone:
    def __init__(self, clock, x, y):
        self.clock = clock
        self.x = x
        self.y = y
        self.alive = True
        self.blocked = False
        self.thread = None
        self.ret = None


cond = threading.Condition()
local = threading.local()
DRONES = []


class W:
    pass


def reset(seed):
    W.rng = random.Random(seed)
    W.n = N
    W.cactus = 0
    W.size = {}
    W.plant_t = {}
    W.ground = {}
    for x in range(N):
        for y in range(N):
            W.ground[(x, y)] = Grounds.Grassland
            W.size[(x, y)] = None
            W.plant_t[(x, y)] = 0
    W.swaps = 0
    W.moves = 0
    W.harvested = 0
    W.last_grid = {}
    W.spawn_fail = 0


def me():
    return local.d


def act(cost, fn):
    d = me()
    with cond:
        while True:
            m = None
            for o in DRONES:
                if o.alive and not o.blocked:
                    if m is None or o.clock < m:
                        m = o.clock
            if m is None or d.clock <= m:
                break
            cond.wait(0.2)
        r = fn()
        d.clock += cost
        cond.notify_all()
    return r


# --- ゲームAPI ---
def get_world_size():
    return act(1, lambda: float(W.n))


def get_pos_x():
    return act(1, lambda: float(me().x))


def get_pos_y():
    return act(1, lambda: float(me().y))


def num_items(it):
    return act(1, lambda: W.cactus)


def get_tick_count():
    return me().clock


def quick_print(*a):
    print("   quick_print:", *a)


def print_(*a):
    print("   PRINT:", *a)


def _clear():
    for k in W.size:
        W.size[k] = None
    d = me()
    d.x = 0
    d.y = 0


def clear():
    return act(200, _clear)


def _move(dd):
    d = me()
    dx, dy = DXY[dd]
    nx, ny = d.x + dx, d.y + dy
    if nx < 0 or nx >= W.n or ny < 0 or ny >= W.n:
        return False
    d.x, d.y = nx, ny
    W.moves += 1
    return True


def move(dd):
    d = me()
    dx, dy = DXY[dd]
    nx, ny = d.x + dx, d.y + dy
    if nx < 0 or nx >= W.n or ny < 0 or ny >= W.n:
        return act(1, lambda: False)
    return act(200, lambda: _move(dd))


def get_ground_type():
    return act(1, lambda: W.ground[(me().x, me().y)])


def _till():
    k = (me().x, me().y)
    if W.ground[k] == Grounds.Soil:
        W.ground[k] = Grounds.Grassland
    else:
        W.ground[k] = Grounds.Soil


def till():
    return act(200, _till)


def _plant():
    k = (me().x, me().y)
    if os.environ.get('DET')=='1':
        W.size[k] = random.Random(k[0]*1000+k[1]*7+SEED*99991).randrange(10)
    else:
        W.size[k] = W.rng.randrange(10)
    W.plant_t[k] = me().clock
    return True


def plant(e):
    k = (me().x, me().y)
    if W.ground[k] != Grounds.Soil:
        return act(1, lambda: False)
    return act(200, _plant)


def can_harvest():
    def f():
        d = me()
        k = (d.x, d.y)
        if W.size[k] is None:
            return False
        return d.clock - W.plant_t[k] >= GROW
    return act(1, f)


def measure(direction=None):
    def f():
        d = me()
        if direction is None:
            k0 = (d.x, d.y)
            if NOMEAS and W.size[k0] is not None and d.clock - W.plant_t[k0] < GROW:
                return None
            return W.size[k0]
        dx, dy = DXY[direction]
        nx, ny = d.x + dx, d.y + dy
        if nx < 0 or nx >= W.n or ny < 0 or ny >= W.n:
            return None
        if NOMEAS and W.size[(nx, ny)] is not None and d.clock - W.plant_t[(nx, ny)] < GROW:
            return None
        return W.size[(nx, ny)]
    return act(1, f)


def _swap(dd):
    d = me()
    dx, dy = DXY[dd]
    nx, ny = d.x + dx, d.y + dy
    if nx < 0 or nx >= W.n or ny < 0 or ny >= W.n:
        return None
    a, b = (d.x, d.y), (nx, ny)
    W.size[a], W.size[b] = W.size[b], W.size[a]
    W.plant_t[a], W.plant_t[b] = W.plant_t[b], W.plant_t[a]
    W.swaps += 1
    return None


def swap(dd):
    return act(200, lambda: _swap(dd))


def sorted_ok(x, y, now):
    s = W.size[(x, y)]
    if s is None or now - W.plant_t[(x, y)] < GROW:
        return False
    for dd, sign in ((East, 1), (North, 1), (West, -1), (South, -1)):
        dx, dy = DXY[dd]
        nx, ny = x + dx, y + dy
        if 0 <= nx < W.n and 0 <= ny < W.n:
            o = W.size[(nx, ny)]
            if o is None:
                return False
            if sign > 0 and o < s:
                return False
            if sign < 0 and o > s:
                return False
    return True


def _harvest():
    d = me()
    now = d.clock
    W.last_grid = dict(W.size)
    k = (d.x, d.y)
    if W.size[k] is None:
        return False
    if sorted_ok(k[0], k[1], now):
        cnt = 0
        for kk in list(W.size):
            if W.size[kk] is not None and sorted_ok(kk[0], kk[1], now):
                cnt += 1
        for kk in list(W.size):
            if W.size[kk] is not None and sorted_ok(kk[0], kk[1], now):
                W.size[kk] = None
        W.cactus += cnt * cnt
        W.harvested = cnt
    else:
        W.cactus += 1
        W.size[k] = None
        W.harvested = 1
    return True


def harvest():
    return act(200, _harvest)


def num_drones():
    def f():
        c = 0
        for o in DRONES:
            if o.alive:
                c += 1
        return c
    return act(1, f)


def max_drones():
    return act(1, lambda: MAXD)


def _runner(child, fn):
    local.d = child
    try:
        fn()
    finally:
        with cond:
            child.alive = False
            cond.notify_all()


def spawn_drone(fn):
    d = me()
    # 生成そのものに200 tick．枠が無ければ失敗（1 tick）
    def f():
        c = 0
        for o in DRONES:
            if o.alive:
                c += 1
        return c
    n_alive = act(1, f)
    if n_alive >= MAXD:
        W.spawn_fail += 1
        return None
    child = Drone(d.clock + 200, d.x, d.y)
    with cond:
        DRONES.append(child)
        d.clock += 200
        cond.notify_all()
    t = threading.Thread(target=_runner, args=(child, fn))
    child.thread = t
    t.daemon = True
    t.start()
    return child


def wait_for(h):
    d = me()
    saved = d.clock
    with cond:
        d.blocked = True
        cond.notify_all()
    h.thread.join()
    with cond:
        d.blocked = False
        if h.clock > saved:
            d.clock = h.clock
        cond.notify_all()
    return None


def has_finished(h):
    return act(1, lambda: not h.alive)


def grange(*a):
    return range(*[int(v) for v in a])


src = open(SRC).read()
ast.parse(src)
import re
# OVERRIDE: 追加引数 name=value で定数を差し替える
for a in sys.argv[5:]:
    if "=" in a:
        kk, vv = a.split("=", 1)
        src = re.sub(r"^%s = \S+" % kk, "%s = %s" % (kk, vv), src, count=1, flags=re.M)
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

reset(SEED)
root = Drone(0, 0, 0)
DRONES.append(root)
local.d = root
sys.setrecursionlimit(100000)
exec(compile(src, SRC, "exec"), env)
root.alive = False


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
print("%-28s n=%d seed=%d maxd=%d : 収穫=%d/%d 交換=%d 移動=%d  実時間=%d  %s"
      % (SRC.split("/")[-1], N, SEED, MAXD, W.harvested, full, W.swaps, W.moves,
         root.clock, "OK" if ok else "*** FAIL ***"))
if not ok:
    sys.exit(1)
