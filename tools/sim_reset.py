"""最速リセット（Leaderboards.Fastest_Reset）用のゲーム全体のシミュレータ（推定を多く含む）．

sim_pumpkin_conc.py と同じ手番方式（1度に1機だけ動かす）．ただし各機の時計は「秒」で持つ．
動作の tick を，その時点の Speed と Power から秒に直して足す（1秒あたり 400×1.5^Speed，Power があれば2倍）．

実機（simulate）で確かめた仕様（CLAUDE.md 5c）：
  ・全アンロックの費用，植える費用（段階 k で 2^(k-1)，サボテン・リンゴは 2^k），収穫量（段階 k で 2^(k-1) 倍，木は5）
  ・Expand の一辺 1,3,3,4,6,8,12,16,22,32．Megafarm の機数 1,2,4,8,16,32
  ・物質を植物に使うと，そのマスと上下左右の感染が反転（端で回り込まない）
  ・感染したマスの取り分の半分が物質になる（合体かぼちゃ・整列サボテンの連鎖でも）
  ・骨 ＝ 尾² × 2^(Dinosaurs-1)．リンゴ1個にサボテン 2^Dinosaurs
  ・肥料・水は 10 秒に 2^(段階-1) 個．ひまわりは最多の花びらで Power 8，ほかは 1
wiki の値（未確認を含む）：成長時間（秒），木は隣の木1本ごとに2倍，水で最大5倍，肥料で残り2秒減，
  迷路（m×m，宝の金 m²×2^(L-1)，再配置300回），恐竜の move は 400 tick から リンゴ1個ごとに3%減（下限29）
推定：Expand すると盤面が消える（clear）．ドローンは (0,0) へ．アンロックの前提（ツリー）は無視．

引数: src seed [NAME=value ...]    環境変数: LINE（1行の tick．既定 2.0） PROGRESS（秒ごとに途中経過） UNLOCKS ITEMS（JSON で初期状態）
"""
import ast
import heapq
import json
import math
import os
import random
import re
import sys
import threading

SRC = sys.argv[1]
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 1
LINE = float(os.environ.get('LINE', '2.0'))
PROGRESS = float(os.environ.get('PROGRESS', '0'))
LIMIT = float(os.environ.get('LIMIT', '36000'))   # 秒．これを超えたら打ち切る

North, East, South, West = "North", "East", "South", "West"
DXY = {North: (0, 1), East: (1, 0), South: (0, -1), West: (-1, 0)}


class _Enum:
    def __init__(self, prefix, names):
        for n in names:
            setattr(self, n, prefix + n)
        self._names = [prefix + n for n in names]

    def __iter__(self):
        return iter(self._names)


UNLOCK_NAMES = ["Auto_Unlock", "Cactus", "Carrots", "Costs", "Debug", "Debug_2", "Dictionaries", "Dinosaurs",
                "Expand", "Fertilizer", "Functions", "Grass", "Hats", "Import", "Leaderboard", "Lists", "Loops",
                "Mazes", "Megafarm", "Operators", "Plant", "Polyculture", "Pumpkins", "Senses", "Simulation",
                "Speed", "Sunflowers", "The_Farmers_Remains", "Timing", "Top_Hat", "Trees", "Utilities",
                "Variables", "Watering"]
Unlocks = _Enum("Unlocks.", UNLOCK_NAMES)
Items = _Enum("Items.", ["Hay", "Wood", "Carrot", "Pumpkin", "Cactus", "Bone", "Gold", "Weird_Substance",
                         "Water", "Fertilizer", "Power", "Piggy"])
Entities = _Enum("Entities.", ["Grass", "Bush", "Tree", "Carrot", "Pumpkin", "Dead_Pumpkin", "Cactus",
                               "Sunflower", "Hedge", "Treasure", "Apple", "Dinosaur"])
Grounds = _Enum("Grounds.", ["Grassland", "Soil"])
Hats = _Enum("Hats.", ["Straw_Hat", "Dinosaur_Hat", "Brown_Hat", "Gray_Hat", "Green_Hat", "Purple_Hat"])

H, WD, C, P, CA, B, G, WS = (Items.Hay, Items.Wood, Items.Carrot, Items.Pumpkin, Items.Cactus, Items.Bone,
                             Items.Gold, Items.Weird_Substance)
COSTS = {
    "Auto_Unlock": [{P: 5000}],
    "Cactus": [{P: 5000}, {P: 20000}, {P: 120000}, {P: 720000}, {P: 4320000}, {P: 25900000}],
    "Carrots": [{WD: v} for v in (50, 250, 1250, 6250, 31200, 156000, 781000, 3910000, 19500000, 97700000)],
    "Costs": [{P: 2500}], "Debug": [{H: 50, WD: 50}], "Debug_2": [{G: 500}], "Dictionaries": [{P: 2500}],
    "Dinosaurs": [{CA: v} for v in (2000, 12000, 72000, 432000, 2590000, 15600000)],
    "Expand": [{H: 30}, {WD: 20}, {WD: 30, C: 20}, {WD: 100, C: 50}, {P: 1000}, {P: 8000}, {P: 64000},
               {P: 512000}, {P: 4100000}],
    "Fertilizer": [{WD: 500}, {WD: 1500}, {WD: 9000}, {WD: 54000}],
    "Functions": [{C: 40}],
    "Grass": [{H: 100}, {H: 300}] + [{WD: v} for v in (500, 2500, 12500, 62500, 312000, 1560000, 7810000, 39100000)],
    "Hats": [{H: 50}], "Import": [{C: 80}], "Leaderboard": [{B: 2000000, G: 1000000}], "Lists": [{C: 500}],
    "Loops": [{H: 5}],
    "Mazes": [{WS: 1000}] + [{CA: v} for v in (12000, 72000, 432000, 2590000, 15600000)],
    "Megafarm": [{G: v} for v in (2000, 8000, 32000, 128000, 512000)],
    "Operators": [{H: 150, WD: 10}], "Plant": [{H: 50}],
    "Polyculture": [{P: 3000}] + [{B: v} for v in (10000, 50000, 250000, 1250000)],
    "Pumpkins": [{WD: 500, C: 200}] + [{C: v} for v in (1000, 4000, 16000, 64000, 256000, 1020000, 4100000, 16400000, 65500000)],
    "Senses": [{H: 100}], "Simulation": [{G: 5000}],
    "Speed": [{H: 20}, {WD: 20}, {WD: 50, C: 50}, {C: 500}, {C: 1000}],
    "Sunflowers": [{C: 500}], "The_Farmers_Remains": [{B: 100000000}], "Timing": [{P: 1000}],
    "Top_Hat": [{H: 1e9}], "Trees": [{WD: 50, C: 70}] + [{H: v} for v in (300, 1200, 4800, 19200, 76800, 307000, 1230000, 4920000, 19700000)],
    "Utilities": [{P: 1000}], "Variables": [{C: 35}],
    "Watering": [{WD: v} for v in (50, 200, 800, 3200, 12800, 51200, 205000, 819000, 3280000)],
}
SIZES = [1, 3, 3, 4, 6, 8, 12, 16, 22, 32]
GROW = {  # 秒（wiki の Plant_growth．一様分布）
    Entities.Grass: (0.5, 0.5), Entities.Bush: (3.2, 4.8), Entities.Carrot: (4.8, 7.2), Entities.Tree: (5.6, 8.4),
    Entities.Pumpkin: (0.2, 3.8), Entities.Cactus: (1.0, 1.0), Entities.Sunflower: (5.6, 8.4),
}
DEATH = float(os.environ.get('DEATH', '0.2'))


class Drone:
    def __init__(self, t, x, y):
        self.t = t          # 秒
        self.x = x
        self.y = y
        self.alive = True
        self.blocked = None
        self.ret = None
        self.pending = 0.0  # tick
        self.hat = Hats.Straw_Hat
        self.body = []      # 恐竜の尾（古い順）
        self.apples = 0
        self.ev = threading.Event()


local = threading.local()
DRONES = []


class W:
    pass


def reset():
    W.rng = random.Random(SEED)
    W.lv = dict((n, 0) for n in UNLOCK_NAMES)
    W.items = dict((i, 0.0) for i in Items)
    W.now = 0.0
    W.supply_t = 0.0
    W.ev = []
    W.seq = 0
    W.groups = {}
    W.nextid = 1
    W.mazes = []
    W.maze_of = {}
    W.apple = None
    W.log = []
    W.no_normal_next = False
    W.stats = {}
    init = os.environ.get('UNLOCKS')
    if init:
        for k, v in json.loads(init).items():
            W.lv[k] = v
    init = os.environ.get('ITEMS')
    if init:
        for k, v in json.loads(init).items():
            W.items["Items." + k] = float(v)
    make_board()


def world():
    return SIZES[min(W.lv["Expand"], 9)]


def make_board():
    W.n = world()
    W.cell = {}
    for x in range(W.n):
        for y in range(W.n):
            W.cell[(x, y)] = new_cell()
    W.groups = {}
    W.mazes = []
    W.maze_of = {}


def new_cell():
    return {'g': Grounds.Grassland, 'e': Entities.Grass, 'ripe': 0.0, 'uid': 0, 'inf': False, 'w': 0.0,
            'size': 0, 'petals': 0, 'die': False, 'gid': None, 'ripe_done': True}


def stat(k, v=1):
    W.stats[k] = W.stats.get(k, 0) + v


# --- 時間 ---
def tps():
    r = 400.0 * (1.5 ** W.lv["Speed"])
    if W.items[Items.Power] > 0:
        r *= 2
    return r


def supply(t):
    """時刻 t まで水と肥料を届ける"""
    if t <= W.supply_t:
        return
    dt = t - W.supply_t
    W.supply_t = t
    if W.lv["Watering"] > 0:
        W.items[Items.Water] += dt / 10.0 * 2 ** (W.lv["Watering"] - 1)
    if W.lv["Fertilizer"] > 0:
        W.items[Items.Fertilizer] += dt / 10.0 * 2 ** (W.lv["Fertilizer"] - 1)


def advance(t):
    if t > W.now:
        W.now = t
    supply(t)
    while W.ev and W.ev[0][0] <= t:
        _, _, c, uid = heapq.heappop(W.ev)
        s = W.cell.get(c)
        if s is None or s['uid'] != uid:
            continue
        if s['e'] == Entities.Pumpkin and not s['ripe_done']:
            s['ripe_done'] = True
            if s['die']:
                s['e'] = Entities.Dead_Pumpkin
            else:
                gid = new_id()
                s['gid'] = gid
                W.groups[gid] = [c[0], c[1], 1]
                try_merge(c)


def new_id():
    W.nextid += 1
    return W.nextid


def me():
    return local.d


def _trace(frame, event, arg):
    if frame.f_code.co_filename != SRC:
        return None
    if event == 'line':
        local.d.pending += LINE
    return _trace


def _pick():
    m = None
    for o in DRONES:
        if o.alive and o.blocked is None:
            if m is None or o.t < m.t:
                m = o
    return m


def _yield(d):
    m = _pick()
    if m is d or m is None:
        return
    d.ev.clear()
    m.ev.set()
    d.ev.wait()


_last_prog = [0.0]


def spend(d, ticks):
    """d が ticks を使う．Power を減らし，秒に直して時計を進める"""
    if ticks <= 0:
        return
    r = tps()
    d.t += ticks / r
    if W.items[Items.Power] > 0:
        W.items[Items.Power] = max(0.0, W.items[Items.Power] - ticks / 6000.0)


def act(cost, fn):
    d = me()
    if d.pending:
        spend(d, d.pending)
        d.pending = 0.0
    _yield(d)
    advance(d.t)
    if d.t > LIMIT:
        raise SystemExit("LIMIT")
    if PROGRESS and W.now - _last_prog[0] >= PROGRESS:
        _last_prog[0] = W.now
        sys.stderr.write("t=%.0f lv=%s items=%s drones=%d\n" % (
            W.now, dict((k, v) for k, v in W.lv.items() if v),
            dict((k[6:], int(v)) for k, v in W.items.items() if v >= 1), sum(1 for o in DRONES if o.alive)))
    r = fn()
    c = cost
    if isinstance(r, tuple) and len(r) == 2 and r[0] == "__cost":
        c = r[1][1]
        r = r[1][0]
    spend(d, c)
    return r


def ret(v, cost):
    return ("__cost", (v, cost))


def here():
    d = me()
    return (d.x, d.y)


# --- 植物 ---
def grow_time(e, c):
    lo, hi = GROW[e]
    t = W.rng.uniform(lo, hi)
    if e == Entities.Tree:
        x, y = c
        for dx, dy in DXY.values():
            o = W.cell.get((x + dx, y + dy))
            if o is not None and o['e'] == Entities.Tree:
                t *= 2
    return t / (1 + 4 * W.cell[c]['w'])


def put(c, e, t0):
    s = W.cell[c]
    s['e'] = e
    s['inf'] = False
    s['gid'] = None
    s['ripe_done'] = False
    W.seq += 1
    s['uid'] = W.seq
    s['ripe'] = t0 + grow_time(e, c)
    if e == Entities.Cactus:
        s['size'] = W.rng.randint(0, 9)
    if e == Entities.Sunflower:
        s['petals'] = W.rng.randint(7, 15)
    if e == Entities.Pumpkin:
        s['die'] = W.rng.random() < DEATH
        heapq.heappush(W.ev, (s['ripe'], W.seq, c, W.seq))


def ripe(s):
    if s['e'] in (Entities.Pumpkin,):
        return s['ripe_done'] and s['e'] == Entities.Pumpkin
    if s['e'] in (Entities.Grass, Entities.Bush, Entities.Tree, Entities.Carrot, Entities.Cactus, Entities.Sunflower):
        return W.now >= s['ripe']
    return False


def ok_p(x, y):
    s = W.cell.get((x, y))
    return s is not None and s['e'] == Entities.Pumpkin and s['ripe_done']


def try_merge(c):
    N = W.n
    cx, cy = c
    dp = [[0] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            if ok_p(i, j):
                if i == 0 or j == 0:
                    dp[i][j] = 1
                else:
                    dp[i][j] = min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]) + 1
    cands = []
    for i in range(cx, N):
        for j in range(cy, N):
            need = max(i - cx, j - cy) + 1
            for sz in range(dp[i][j], max(need, 2) - 1, -1):
                cands.append((sz, i - sz + 1, j - sz + 1))
    cands.sort(reverse=True)
    groups = list(W.groups.items())
    for sz, x0, y0 in cands:
        inside = []
        good = True
        for g, (gx, gy, gs) in groups:
            if gx + gs <= x0 or gx >= x0 + sz or gy + gs <= y0 or gy >= y0 + sz:
                continue
            if gx < x0 or gy < y0 or gx + gs > x0 + sz or gy + gs > y0 + sz:
                good = False
                break
            inside.append(g)
        if not good or len(inside) < 2:
            continue
        nid = new_id()
        for g in inside:
            del W.groups[g]
        W.groups[nid] = [x0, y0, sz]
        for x in range(x0, x0 + sz):
            for y in range(y0, y0 + sz):
                W.cell[(x, y)]['gid'] = nid
        return


def mult(u):
    return 2 ** (max(W.lv[u], 1) - 1)


def plant_cost(e):
    if e == Entities.Carrot:
        k = mult("Carrots")
        return {Items.Hay: k, Items.Wood: k}
    if e == Entities.Pumpkin:
        return {Items.Carrot: mult("Pumpkins")}
    if e == Entities.Cactus:
        return {Items.Pumpkin: 2 * mult("Cactus")}
    if e == Entities.Sunflower:
        return {Items.Carrot: 1}
    if e == Entities.Apple:
        return {Items.Cactus: 2 * mult("Dinosaurs")}
    return {}


NEEDS = {Entities.Grass: "Plant", Entities.Bush: "Plant", Entities.Tree: "Trees", Entities.Carrot: "Carrots",
         Entities.Pumpkin: "Pumpkins", Entities.Cactus: "Cactus", Entities.Sunflower: "Sunflowers"}
SOIL = (Entities.Carrot, Entities.Pumpkin, Entities.Cactus, Entities.Sunflower)


def cactus_sorted(x, y):
    s = W.cell[(x, y)]
    if s['e'] != Entities.Cactus or not ripe(s):
        return False
    for dd, sign in ((East, 1), (North, 1), (West, -1), (South, -1)):
        dx, dy = DXY[dd]
        o = W.cell.get((x + dx, y + dy))
        if o is None:
            continue
        if o['e'] != Entities.Cactus:
            continue
        if sign > 0 and o['size'] < s['size']:
            return False
        if sign < 0 and o['size'] > s['size']:
            return False
    return True


def do_harvest(c):
    s = W.cell[c]
    e = s['e']
    if e is None or e in (Entities.Hedge,):
        return False
    if e == Entities.Treasure:
        return harvest_treasure(c)
    if not ripe(s):
        # 育つ前・枯れた：消える
        clear_cell(c)
        return True
    inf = s['inf']
    if e == Entities.Grass:
        gain(Items.Hay, mult("Grass"), inf)
    elif e == Entities.Bush:
        gain(Items.Wood, mult("Trees"), inf)
    elif e == Entities.Tree:
        gain(Items.Wood, 5 * mult("Trees"), inf)
    elif e == Entities.Carrot:
        gain(Items.Carrot, mult("Carrots"), inf)
    elif e == Entities.Sunflower:
        more = False
        cnt = 0
        for o in W.cell.values():
            if o['e'] == Entities.Sunflower:
                cnt += 1
                if o['petals'] > s['petals']:
                    more = True
        if cnt >= 10 and not more and not W.no_normal_next:
            W.items[Items.Power] += 8
            stat('power8')
        else:
            W.items[Items.Power] += 1
            stat('power1')
        W.no_normal_next = more
    elif e == Entities.Pumpkin:
        x0, y0, sz = W.groups[s['gid']]
        base = sz ** 3 if sz <= 5 else sz * sz * 6
        tot = base * mult("Pumpkins")
        share = tot / float(sz * sz)
        ninf = 0
        for x in range(x0, x0 + sz):
            for y in range(y0, y0 + sz):
                if W.cell[(x, y)]['inf']:
                    ninf += 1
        W.items[Items.Pumpkin] += tot - ninf * share / 2
        W.items[WS] += ninf * share / 2
        del W.groups[s['gid']]
        for x in range(x0, x0 + sz):
            for y in range(y0, y0 + sz):
                clear_cell((x, y))
        stat('pumpkin_harvest_%d' % sz)
        return True
    elif e == Entities.Cactus:
        if cactus_sorted(c[0], c[1]):
            comp = [c]
            seen = {c}
            i = 0
            while i < len(comp):
                x, y = comp[i]
                i += 1
                for dx, dy in DXY.values():
                    nb = (x + dx, y + dy)
                    if nb in W.cell and nb not in seen and cactus_sorted(nb[0], nb[1]):
                        seen.add(nb)
                        comp.append(nb)
            k = len(comp)
            tot = k * k * mult("Cactus")
            share = tot / float(k)
            ninf = sum(1 for q in comp if W.cell[q]['inf'])
            W.items[CA] += tot - ninf * share / 2
            W.items[WS] += ninf * share / 2
            for q in comp:
                clear_cell(q)
            stat('cactus_chain_max', 0)
            W.stats['cactus_chain_max'] = max(W.stats.get('cactus_chain_max', 0), k)
            return True
        gain(Items.Cactus, mult("Cactus"), inf)
    clear_cell(c)
    return True


def gain(item, v, inf):
    if inf:
        W.items[item] += v / 2.0
        W.items[WS] += v / 2.0
    else:
        W.items[item] += v


def clear_cell(c):
    s = W.cell[c]
    s['e'] = None
    s['inf'] = False
    s['gid'] = None
    s['ripe_done'] = True
    W.seq += 1
    s['uid'] = W.seq
    if s['g'] == Grounds.Grassland:
        put(c, Entities.Grass, W.now)


# --- 迷路 ---
class Maze:
    pass


def make_maze(bx, by, m):
    x0 = bx - m // 2
    y0 = by - m // 2
    if x0 < 0 or y0 < 0 or x0 + m > W.n or y0 + m > W.n:
        x0 = max(0, min(x0, W.n - m))
        y0 = max(0, min(y0, W.n - m))
    cells = [(x0 + i, y0 + j) for i in range(m) for j in range(m)]
    for c in cells:
        if c in W.maze_of:
            return False
    Z = Maze()
    Z.m = m
    Z.cells = set(cells)
    Z.edges = set()
    Z.reuse = 0
    start = (bx, by) if (bx, by) in Z.cells else cells[0]
    seen = {start}
    st = [start]
    while st:
        cx, cy = st[-1]
        cand = [(cx + d[0], cy + d[1]) for d in DXY.values()]
        cand = [nb for nb in cand if nb in Z.cells and nb not in seen]
        if not cand:
            st.pop()
            continue
        nb = W.rng.choice(cand)
        Z.edges.add(frozenset((st[-1], nb)))
        seen.add(nb)
        st.append(nb)
    Z.treasure = W.rng.choice(cells)
    for c in cells:
        W.maze_of[c] = Z
        s = W.cell[c]
        s['e'] = Entities.Hedge
        W.seq += 1
        s['uid'] = W.seq
    W.cell[Z.treasure]['e'] = Entities.Treasure
    W.mazes.append(Z)
    stat('mazes')
    return True


def relocate(Z):
    old = Z.treasure
    W.cell[old]['e'] = Entities.Hedge
    cells = sorted(Z.cells)
    while True:
        t = W.rng.choice(cells)
        if t != old:
            break
    Z.treasure = t
    W.cell[t]['e'] = Entities.Treasure
    if W.rng.random() < 0.084:
        for k in range(20):
            a = W.rng.choice(cells)
            d = W.rng.choice(list(DXY.values()))
            b2 = (a[0] + d[0], a[1] + d[1])
            if b2 in Z.cells and frozenset((a, b2)) not in Z.edges:
                Z.edges.add(frozenset((a, b2)))
                break


def harvest_treasure(c):
    Z = W.maze_of[c]
    W.items[G] += Z.m * Z.m * mult("Mazes")
    stat('treasures')
    for q in Z.cells:
        del W.maze_of[q]
        s = W.cell[q]
        s['e'] = None
        clear_cell(q)
    W.mazes.remove(Z)
    return True


def passable(d, dd):
    a = (d.x, d.y)
    dx, dy = DXY[dd]
    b2 = ((d.x + dx) % W.n, (d.y + dy) % W.n)
    za = W.maze_of.get(a)
    zb = W.maze_of.get(b2)
    if za is None and zb is None:
        return True
    if za is not None and za is zb:
        return frozenset((a, b2)) in za.edges
    return False


# --- ゲーム API ---
def get_world_size():
    return act(1, lambda: float(W.n))


def get_pos_x():
    return act(1, lambda: float(me().x))


def get_pos_y():
    return act(1, lambda: float(me().y))


def num_items(it):
    return act(1, lambda: math.floor(W.items[it] + 1e-9) if it != Items.Power else W.items[it])


def num_unlocked(u):
    return act(1, lambda: float(W.lv[u[len("Unlocks."):]]))


def get_cost(thing, k=None):
    def f():
        if thing.startswith("Unlocks."):
            name = thing[len("Unlocks."):]
            lv = W.lv[name] if k is None else int(k)
            lst = COSTS.get(name, [])
            if lv >= len(lst):
                return {}
            return dict(lst[lv])
        return plant_cost(thing)
    return act(1, f)


def unlock(u):
    def f():
        name = u[len("Unlocks."):]
        lst = COSTS[name]
        lv = W.lv[name]
        if lv >= len(lst):
            return ret(False, 1)
        cost = lst[lv]
        for it, v in cost.items():
            if W.items[it] < v:
                return ret(False, 1)
        for it, v in cost.items():
            W.items[it] -= v
        W.lv[name] = lv + 1
        W.log.append((round(W.now, 1), name, lv + 1))
        if name == "Expand":
            make_board()
            for o in DRONES:
                o.x = min(o.x, W.n - 1)
                o.y = min(o.y, W.n - 1)
        return ret(True, 200)
    return act(200, f)


def get_tick_count():
    return act(0, lambda: me().t * 400)


def get_time():
    return act(0, lambda: me().t)


def quick_print(*a):
    print("   quick_print: %.1f" % me().t, *a)


def print_(*a):
    print("   PRINT:", *a)


def clear():
    def f():
        make_board()
        me().x = 0
        me().y = 0
        return True
    return act(200, f)


def can_move(dd):
    return act(1, lambda: _can_move(me(), dd))


def _can_move(d, dd):
    if W.lv["Expand"] < 1:
        return False
    dx, dy = DXY[dd]
    nx, ny = d.x + dx, d.y + dy
    if d.hat == Hats.Dinosaur_Hat:
        if nx < 0 or ny < 0 or nx >= W.n or ny >= W.n:
            return False
        if (nx, ny) in d.body[1:] if len(d.body) > 0 else False:
            return False
    return passable(d, dd)


def move(dd):
    d = me()

    def f():
        if not _can_move(d, dd):
            return ret(False, 1)
        dx, dy = DXY[dd]
        if d.hat == Hats.Dinosaur_Hat:
            cost = max(29.0, math.floor(400 * 0.97 ** d.apples))
            old = (d.x, d.y)
            d.x += dx
            d.y += dy
            d.body.append(old)
            if (d.x, d.y) == W.apple:
                d.apples += 1
                spawn_apple(d)
            else:
                if len(d.body) > d.apples:
                    d.body.pop(0)
            stat('dino_moves')
            return ret(True, cost)
        d.x = (d.x + dx) % W.n
        d.y = (d.y + dy) % W.n
        stat('moves')
        return True
    return act(200, f)


def spawn_apple(d):
    cost = plant_cost(Entities.Apple)
    for it, v in cost.items():
        if W.items[it] < v:
            W.apple = None
            return
    free = [c for c in W.cell if c != (d.x, d.y) and c not in d.body]
    if not free:
        W.apple = None
        return
    for it, v in cost.items():
        W.items[it] -= v
    W.apple = W.rng.choice(free)


def change_hat(h):
    d = me()

    def f():
        if h == Hats.Dinosaur_Hat:
            if W.lv["Dinosaurs"] < 1:
                return
            d.hat = h
            d.body = []
            d.apples = 0
            spawn_apple(d)
        else:
            if d.hat == Hats.Dinosaur_Hat:
                L = d.apples
                W.items[B] += L * L * mult("Dinosaurs")
                stat('bones_runs')
                W.apple = None
            d.hat = h
            d.body = []
            d.apples = 0
    return act(200, f)


def get_entity_type():
    def f():
        d = me()
        if d.hat == Hats.Dinosaur_Hat and W.apple == (d.x, d.y):
            return Entities.Apple
        return W.cell[here()]['e']
    return act(1, f)


def get_ground_type():
    return act(1, lambda: W.cell[here()]['g'])


def get_water():
    return act(1, lambda: round(W.cell[here()]['w'], 2))


def can_harvest():
    def f():
        s = W.cell[here()]
        if s['e'] == Entities.Treasure:
            return True
        return ripe(s)
    return act(1, f)


def measure(direction=None):
    def f():
        d = me()
        c = here()
        if d.hat == Hats.Dinosaur_Hat:
            if W.apple is None:
                return None
            return (float(W.apple[0]), float(W.apple[1]))
        if c in W.maze_of and direction is None:
            Z = W.maze_of[c]
            return (float(Z.treasure[0]), float(Z.treasure[1]))
        if direction is not None:
            dx, dy = DXY[direction]
            c = ((c[0] + dx) % W.n, (c[1] + dy) % W.n)
        s = W.cell[c]
        if s['e'] == Entities.Cactus:
            return float(s['size'])
        if s['e'] == Entities.Sunflower:
            return float(s['petals'])
        if s['e'] == Entities.Pumpkin:
            if s['ripe_done'] and s['gid'] is not None:
                return float(s['gid'])
            return float(-s['uid'])
        return None
    return act(1, f)


def till():
    def f():
        if W.lv["Carrots"] < 1:
            return ret(False, 1)
        c = here()
        s = W.cell[c]
        if c in W.maze_of:
            return ret(False, 1)
        s['g'] = Grounds.Soil if s['g'] == Grounds.Grassland else Grounds.Grassland
        s['e'] = None
        clear_cell(c)
        return True
    return act(200, f)


def plant(e):
    def f():
        c = here()
        s = W.cell[c]
        need = NEEDS.get(e)
        if need is None or W.lv[need] < 1:
            return ret(False, 1)
        if e in SOIL and s['g'] != Grounds.Soil:
            return ret(False, 1)
        if s['e'] not in (None, Entities.Grass, Entities.Dead_Pumpkin):
            return ret(False, 1)
        if s['e'] == Entities.Grass and e == Entities.Grass:
            return ret(False, 1)
        cost = plant_cost(e)
        for it, v in cost.items():
            if W.items[it] < v:
                return ret(False, 1)
        for it, v in cost.items():
            W.items[it] -= v
        put(c, e, W.now)
        stat('plant')
        return True
    return act(200, f)


def harvest():
    def f():
        c = here()
        if c in W.maze_of and W.cell[c]['e'] == Entities.Hedge:
            # 迷路の生け垣を収穫すると迷路が消える（推定）
            Z = W.maze_of[c]
            for q in Z.cells:
                del W.maze_of[q]
                W.cell[q]['e'] = None
                clear_cell(q)
            W.mazes.remove(Z)
            return True
        r = do_harvest(c)
        if not r:
            return ret(False, 1)
        return True
    return act(200, f)


def swap(dd):
    def f():
        d = me()
        dx, dy = DXY[dd]
        a = (d.x, d.y)
        b2 = ((d.x + dx) % W.n, (d.y + dy) % W.n)
        W.cell[a], W.cell[b2] = W.cell[b2], W.cell[a]
        for q in (a, b2):
            s = W.cell[q]
            if s['e'] == Entities.Pumpkin and not s['ripe_done']:
                heapq.heappush(W.ev, (s['ripe'], s['uid'], q, s['uid']))
        stat('swaps')
        return True
    return act(200, f)


def use_item(it, amt=1):
    def f():
        c = here()
        s = W.cell[c]
        if W.items[it] < amt:
            stat('use_fail_' + it[6:])
            return ret(False, 1)
        if it == Items.Water:
            if W.lv["Watering"] < 1:
                return ret(False, 1)
            W.items[it] -= amt
            s['w'] = min(1.0, s['w'] + 0.25 * amt)
            return True
        if it == Items.Fertilizer:
            if W.lv["Fertilizer"] < 1:
                return ret(False, 1)
            W.items[it] -= amt
            if s['e'] in GROW:
                s['ripe'] -= 2.0 * amt
                s['inf'] = True
                if s['e'] == Entities.Pumpkin and not s['ripe_done']:
                    W.seq += 1
                    s['uid'] = W.seq
                    heapq.heappush(W.ev, (max(W.now, s['ripe']), W.seq, c, W.seq))
            return True
        if it == Items.Weird_Substance:
            if s['e'] == Entities.Treasure:
                Z = W.maze_of[c]
                if amt != Z.m * mult("Mazes") or Z.reuse >= 300:
                    return ret(False, 1)
                W.items[it] -= amt
                W.items[G] += Z.m * Z.m * mult("Mazes")
                Z.reuse += 1
                stat('treasures')
                relocate(Z)
                return True
            if s['e'] == Entities.Bush:
                if W.lv["Mazes"] < 1:
                    return ret(False, 1)
                m = int(amt // mult("Mazes"))
                if m < 1:
                    return ret(False, 1)
                m = min(m, W.n)
                W.items[it] -= amt
                make_maze(c[0], c[1], m)
                return True
            W.items[it] -= amt
            if amt % 2 == 1:
                for q in [c] + [(c[0] + dx, c[1] + dy) for dx, dy in DXY.values()]:
                    o = W.cell.get(q)
                    if o is not None and o['e'] in GROW:
                        o['inf'] = not o['inf']
            return True
        return ret(False, 1)
    return act(200, f)


def num_drones():
    return act(1, lambda: float(sum(1 for o in DRONES if o.alive)))


def max_drones():
    return act(1, lambda: float(2 ** W.lv["Megafarm"]))


def _finish(d):
    d.alive = False
    for o in DRONES:
        if o.blocked is d:
            o.blocked = None
            if d.t > o.t:
                o.t = d.t
    m = _pick()
    if m is not None:
        m.ev.set()


def _runner(child, fn):
    local.d = child
    child.ev.wait()
    if LINE > 0:
        sys.settrace(_trace)
    try:
        child.ret = fn()
    except SystemExit:
        pass
    finally:
        spend(child, child.pending)
        child.pending = 0.0
        _finish(child)


def spawn_drone(fn):
    d = me()
    n_alive = act(1, lambda: sum(1 for o in DRONES if o.alive))
    if n_alive >= 2 ** W.lv["Megafarm"]:
        return None
    spend(d, 200)
    child = Drone(d.t, d.x, d.y)
    DRONES.append(child)
    t = threading.Thread(target=_runner, args=(child, fn))
    t.daemon = True
    t.start()
    stat('spawns')
    return child


def wait_for(h):
    d = me()
    spend(d, d.pending)
    d.pending = 0.0
    if h.alive:
        d.blocked = h
        m = _pick()
        d.ev.clear()
        if m is not None:
            m.ev.set()
        d.ev.wait()
    elif h.t > d.t:
        d.t = h.t
    return h.ret


def has_finished(h):
    return act(1, lambda: not h.alive)


def do_a_flip():
    d = me()
    d.t += 1.0
    return act(200, lambda: None)


def grange(*a):
    return range(*[int(v) for v in a])


class _IxWrap(ast.NodeTransformer):
    def visit_Subscript(self, node):
        self.generic_visit(node)
        if not isinstance(node.slice, ast.Slice):
            node.slice = ast.Call(func=ast.Name(id="_ix", ctx=ast.Load()), args=[node.slice], keywords=[])
        return node


def _ix(i):
    if isinstance(i, float):
        assert i == int(i), "添字が整数値でない: %r" % i
        return int(i)
    return i


def _len(x):
    return float(len(x))


src = open(SRC).read()
for a in sys.argv[3:]:
    if "=" in a:
        kk, vv = a.split("=", 1)
        src = re.sub(r"^%s = \S+" % kk, "%s = %s" % (kk, vv), src, count=1, flags=re.M)

env = {
    "North": North, "East": East, "South": South, "West": West,
    "Items": Items, "Entities": Entities, "Grounds": Grounds, "Unlocks": Unlocks, "Hats": Hats,
    "get_world_size": get_world_size, "get_pos_x": get_pos_x, "get_pos_y": get_pos_y,
    "num_items": num_items, "num_unlocked": num_unlocked, "get_cost": get_cost, "unlock": unlock,
    "get_tick_count": get_tick_count, "get_time": get_time,
    "quick_print": quick_print, "print": print_, "move": move, "can_move": can_move,
    "measure": measure, "get_entity_type": get_entity_type, "get_ground_type": get_ground_type,
    "get_water": get_water, "can_harvest": can_harvest, "swap": swap, "change_hat": change_hat,
    "till": till, "plant": plant, "harvest": harvest, "use_item": use_item, "clear": clear,
    "spawn_drone": spawn_drone, "wait_for": wait_for, "has_finished": has_finished,
    "num_drones": num_drones, "max_drones": max_drones, "do_a_flip": do_a_flip,
    "abs": abs, "len": _len, "range": grange, "_ix": _ix, "min": min, "max": max,
}

reset()
root = Drone(0.0, 0, 0)
DRONES.append(root)
local.d = root
sys.setrecursionlimit(100000)
if LINE > 0:
    sys.settrace(_trace)
try:
    exec(compile(ast.fix_missing_locations(_IxWrap().visit(ast.parse(src))), SRC, "exec"), env)
except SystemExit as e:
    print("打ち切り:", e)
sys.settrace(None)
spend(root, root.pending)
root.alive = False

done = W.lv["Leaderboard"] > 0
print("%s seed=%d : 時間 %.1f 秒 (%.1f 分)  %s" % (SRC.split("/")[-1], SEED, root.t, root.t / 60,
                                              "OK" if done else "*** 未達 ***"))
print("  段階:", dict((k, v) for k, v in W.lv.items() if v))
print("  所持:", dict((k[6:], int(v)) for k, v in W.items.items() if v >= 1))
print("  統計:", W.stats)
if os.environ.get('LOG'):
    for e in W.log:
        print("  ", e)
if not done:
    sys.exit(1)
