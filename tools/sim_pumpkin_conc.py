"""かぼちゃの並行シミュレータ（sim_maze_conc.py と同じ手番方式：1度に1機だけ動かし，仮想時刻で実時間を出す）．

仕様（実機の小実験に合わせた部分と推定の部分．CLAUDE.md 5b 節）
  ・植える：耕した土（Soil）で plant(Entities.Pumpkin)．にんじん 512 個
  ・成長：一様分布 [GROW_LO, GROW_HI] tick を (1+4w) で割る（w は植えたときの地面の水）
  ・育ち切った時点で確率 DEATH で枯れる（Entities.Dead_Pumpkin）．上から植え直せる
  ・合体（推定のモデル）：生きたかぼちゃが育ち切るたびに，そのマスを含む正方形のうち，
    中が全部「育ち切った生きたかぼちゃ」で，既存の塊を切らない（中の塊が全部入る）最大のもの
    （一辺 MAXMERGE まで）を1つの塊にする．実機の「枯れがあると小さな塊にしかならない」
    「全部生きていれば大きくまとまる」とは合うが，細かい規則は不明
  ・収穫：塊の一辺 s で，s<=5 は s^3，s>=6 は s^2*6，それぞれ ×512．塊ごと消える．
    育つ前に収穫すると消える（何も得ない）．枯れたものは何も得ない
  ・measure()：かぼちゃの ID（塊は同じ ID）．かぼちゃ以外では None
  ・水：WATER_EVERY tick ごとに1タンク溜まる．use_item(Items.Water) で地面の水 +0.25（上限1）．減りは無視
  ・盤面の端で move は回り込む

引数: src seed [maxdrones] [NAME=value ...]
環境変数: N（既定32） LINE（1行の費用．既定2.37） GOAL（合否の額．既定200000000） MAXMERGE（既定32）
          GROW_LO GROW_HI DEATH WATER_EVERY WATER0（最初の水タンク） PROGRESS PROFILE
"""
import ast
import heapq
import os
import random
import re
import sys
import threading

SRC = sys.argv[1]
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 1
MAXD = int(sys.argv[3]) if len(sys.argv) > 3 else 32
N = int(os.environ.get('N', '32'))
LINE = float(os.environ.get('LINE', '2.37'))
GOAL = int(os.environ.get('GOAL', '200000000'))
MAXMERGE = int(os.environ.get('MAXMERGE', '32'))
GROW_LO = float(os.environ.get('GROW_LO', '1500'))
GROW_HI = float(os.environ.get('GROW_HI', '23000'))
DEATH = float(os.environ.get('DEATH', '0.22'))
WATER_EVERY = float(os.environ.get('WATER_EVERY', '237'))
WATER0 = int(os.environ.get('WATER0', '0'))
FERT_EVERY = float(os.environ.get('FERT_EVERY', '8583'))   # LB で肥料1個／約8,583 tick（実測）
FERT_TICKS = float(os.environ.get('FERT_TICKS', '100000'))  # 肥料1回で縮む成長時間（実測で使った直後に育ち切った）

North, East, South, West = "N", "E", "S", "W"
DXY = {North: (0, 1), East: (1, 0), South: (0, -1), West: (-1, 0)}


class Items:
    Pumpkin = "Pumpkin"
    Water = "Water"
    Carrot = "Carrot"
    Fertilizer = "Fertilizer"


class Entities:
    Pumpkin = "Entities.Pumpkin"
    Dead_Pumpkin = "Entities.Dead_Pumpkin"
    Grass = "Entities.Grass"


class Grounds:
    Grassland = "Grounds.Grassland"
    Soil = "Grounds.Soil"


class Drone:
    def __init__(self, clock, x, y):
        self.clock = clock
        self.x = x
        self.y = y
        self.alive = True
        self.blocked = None
        self.thread = None
        self.ret = None
        self.pending = 0.0
        self.ev = threading.Event()


local = threading.local()
DRONES = []


class W:
    pass


def reset():
    W.rng = random.Random(SEED)
    W.pumpkin = 0
    W.carrot = 10 ** 9
    W.water_used = 0
    W.now = 0.0
    W.cell = {}
    for x in range(N):
        for y in range(N):
            # e: None / 'grass' / 'p'（かぼちゃ） / 'dead'
            W.cell[(x, y)] = {'g': Grounds.Grassland, 'e': 'grass', 'ripe': False, 'done': 0.0,
                              'die': False, 'w': 0.0, 'gid': None, 'uid': 0}
    W.ev = []          # (時刻, 連番, マス, uid)
    W.seq = 0
    W.groups = {}      # gid -> [x0, y0, s]
    W.nextid = 1
    W.harvests = 0
    W.sizes = {}
    W.plants = 0
    W.water_fail = 0
    W.htimes = []
    W.fert_used = 0
    W.infected = 0


def tanks():
    return WATER0 + int(W.now // WATER_EVERY) - W.water_used


def ferts():
    return int(W.now // FERT_EVERY) - W.fert_used


def new_id():
    W.nextid += 1
    return W.nextid


def advance(t):
    """時刻 t までに育ち切るマスを順に処理する（手番方式なので t は単調に増える）"""
    if t > W.now:
        W.now = t
    while W.ev and W.ev[0][0] <= t:
        _, _, c, uid = heapq.heappop(W.ev)
        s = W.cell[c]
        if s['e'] != 'p' or s['uid'] != uid or s['ripe']:
            continue
        if s['die']:
            s['e'] = 'dead'
            s['gid'] = None
        else:
            s['ripe'] = True
            gid = new_id()
            s['gid'] = gid
            W.groups[gid] = [c[0], c[1], 1]
            try_merge(c)


def ok(x, y):
    if x < 0 or y < 0 or x >= N or y >= N:
        return False
    s = W.cell[(x, y)]
    return s['e'] == 'p' and s['ripe']


def try_merge(c):
    """c が育ち切ったとき：c を含み，中が全部「育ち切った生きたかぼちゃ」で，中にかかる塊が全部
    中に収まる正方形のうち最大のもの（一辺 MAXMERGE まで，2つ以上の塊を含むもの）を1つの塊にする"""
    cx, cy = c
    M = min(MAXMERGE, N)
    # dp[i][j]：(i,j) を右上（x,y が最大の角）とする全部 ok の正方形の最大の一辺
    dp = [[0] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            if ok(i, j):
                if i == 0 or j == 0:
                    dp[i][j] = 1
                else:
                    a1 = dp[i - 1][j]; a2 = dp[i][j - 1]; a3 = dp[i - 1][j - 1]
                    m = a1 if a1 < a2 else a2
                    m = m if m < a3 else a3
                    dp[i][j] = m + 1
    cands = []
    for i in range(cx, min(N, cx + M)):
        for j in range(cy, min(N, cy + M)):
            need = max(i - cx, j - cy) + 1
            top = min(dp[i][j], M)
            for sz in range(top, max(need, 2) - 1, -1):
                cands.append((sz, i - sz + 1, j - sz + 1))
    cands.sort(reverse=True)
    groups = list(W.groups.items())
    for sz, x0, y0 in cands:
        inside = []
        good = True
        for g, (gx, gy, gs) in groups:
            # 交わるか
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


def me():
    return local.d


PROF = {}
PROFILE = os.environ.get('PROFILE')   # 1 なら関数ごとの実行行数を最後に出す


def _trace(frame, event, arg):
    if frame.f_code.co_filename != SRC:
        return None
    if event == 'line':
        local.d.pending += LINE
        if PROFILE:
            k = frame.f_code.co_name
            PROF[k] = PROF.get(k, 0) + 1
    return _trace


def _pick():
    m = None
    for o in DRONES:
        if o.alive and o.blocked is None:
            if m is None or o.clock < m.clock:
                m = o
    return m


def _yield(d):
    """d が手番を持っている．時刻が最小の機体へ手番を渡し，自分の番が来るまで待つ"""
    m = _pick()
    if m is d or m is None:
        return
    d.ev.clear()
    m.ev.set()
    d.ev.wait()


_NACT = [0]
PROGRESS = int(os.environ.get('PROGRESS', '0'))   # >0 なら，この回数の API 呼び出しごとに途中経過を出す


def act(cost, fn):
    d = me()
    if PROGRESS:
        _NACT[0] += 1
        if _NACT[0] % PROGRESS == 0:
            if os.environ.get('DUMP'):
                for yy in range(N - 1, -1, -1):
                    row = ''
                    for xx in range(N):
                        c = W.cell[(xx, yy)]
                        row += {None: '.', 'grass': ',', 'dead': 'x'}.get(c['e'], 'O' if c['ripe'] else 'g')
                    sys.stderr.write(row + '   ' + ' '.join(str(W.cell[(xx, yy)]['gid']) for xx in range(N)) + '\n')
                sys.stderr.write("groups %s\n" % W.groups)
                sys.stderr.write("drones %s\n" % [(o.x, o.y) for o in DRONES if o.alive])
            sys.stderr.write("progress acts=%d pumpkin=%d harvests=%d clocks=%s\n" % (
                _NACT[0], W.pumpkin, W.harvests,
                sorted(int(o.clock) for o in DRONES if o.alive)[:4]))
    if d.pending:
        d.clock += d.pending
        d.pending = 0.0
    _yield(d)
    advance(d.clock)
    r = fn()
    d.clock += cost
    return r



def here():
    d = me()
    return (d.x, d.y)


def get_world_size():
    return act(1, lambda: float(N))


def get_pos_x():
    return act(1, lambda: float(me().x))


def get_pos_y():
    return act(1, lambda: float(me().y))


def num_items(it):
    def f():
        if it == Items.Pumpkin:
            return float(W.pumpkin)
        if it == Items.Water:
            return float(tanks())
        if it == Items.Fertilizer:
            return float(ferts())
        if it == Items.Carrot:
            return float(W.carrot)
        return 0.0
    return act(1, f)


def get_tick_count():
    return act(0, lambda: me().clock)


def quick_print(*a):
    print("   quick_print:", *a)


def print_(*a):
    print("   PRINT:", *a)


def clear():
    def f():
        for c in W.cell:
            W.cell[c].update({'g': Grounds.Grassland, 'e': 'grass', 'ripe': False, 'gid': None, 'w': 0.0})
        W.groups = {}
        me().x = 0
        me().y = 0
    return act(200, f)


def move(dd):
    d = me()
    def f():
        dx, dy = DXY[dd]
        d.x = (d.x + dx) % N
        d.y = (d.y + dy) % N
        return True
    return act(200, f)


def get_entity_type():
    def f():
        s = W.cell[here()]
        return {None: None, 'grass': Entities.Grass, 'p': Entities.Pumpkin, 'dead': Entities.Dead_Pumpkin}[s['e']]
    return act(1, f)


def get_ground_type():
    return act(1, lambda: W.cell[here()]['g'])


def get_water():
    return act(1, lambda: round(W.cell[here()]['w'], 2))


def can_harvest():
    return act(1, lambda: W.cell[here()]['e'] == 'p' and W.cell[here()]['ripe'])


def measure(direction=None):
    def f():
        c = here()
        if direction is not None:
            dx, dy = DXY[direction]
            c = ((c[0] + dx) % N, (c[1] + dy) % N)
        s = W.cell[c]
        if s['e'] != 'p':
            return None
        if s['ripe']:
            return float(s['gid'])
        return float(-s['uid'])
    return act(1, f)


def till():
    def f():
        s = W.cell[here()]
        s['g'] = Grounds.Soil if s['g'] == Grounds.Grassland else Grounds.Grassland
        s['e'] = None
        s['ripe'] = False
        s['gid'] = None
    return act(200, f)


def plant(e):
    d = me()
    def f():
        s = W.cell[here()]
        if s['g'] != Grounds.Soil or s['e'] == 'p' or W.carrot < 512:
            return False
        W.carrot -= 512
        W.plants += 1
        s['e'] = 'p'
        s['ripe'] = False
        s['gid'] = None
        W.seq += 1
        s['uid'] = W.seq
        s['die'] = W.rng.random() < DEATH
        s['inf'] = False
        # 効果は行動の終わり（200 tick 後）に出るとみなして，そこから成長を数える
        done = d.clock + 200 + W.rng.uniform(GROW_LO, GROW_HI) / (1 + 4 * s['w'])
        s['done'] = done
        heapq.heappush(W.ev, (done, W.seq, here(), W.seq))
        return True
    return act(200, f)


def harvest():
    def f():
        c = here()
        s = W.cell[c]
        if s['e'] == 'p' and s['ripe']:
            g = W.groups.get(s['gid'])
            x0, y0, sz = g
            base = sz ** 3 if sz <= 5 else sz * sz * 6
            inf = 0
            for x in range(x0, x0 + sz):
                for y in range(y0, y0 + sz):
                    if W.cell[(x, y)].get('inf'):
                        inf += 1
            W.infected += inf
            W.pumpkin += base * 512 - inf * (base * 512 // (sz * sz)) // 2
            W.harvests += 1
            W.htimes.append(W.now)
            W.sizes[sz] = W.sizes.get(sz, 0) + 1
            del W.groups[s['gid']]
            for x in range(x0, x0 + sz):
                for y in range(y0, y0 + sz):
                    t = W.cell[(x, y)]
                    t['e'] = None
                    t['ripe'] = False
                    t['gid'] = None
            return True
        if s['e'] in ('p', 'dead', 'grass'):
            s['e'] = None
            s['ripe'] = False
            s['gid'] = None
            return True
        return False
    return act(200, f)


def use_item(it, amt=1):
    def f():
        if it == Items.Water:
            if tanks() < amt:
                W.water_fail += 1
                return False
            W.water_used += amt
            s = W.cell[here()]
            s['w'] = min(1.0, s['w'] + 0.25 * amt)
            return True
        if it == Items.Fertilizer:
            s = W.cell[here()]
            if ferts() < amt:
                return False
            W.fert_used += amt
            if s['e'] == 'p' and not s['ripe']:
                # 残りの成長時間を縮める（事象の時刻を早めて入れ直す）．感染の印を付ける
                s['done'] = max(W.now, s['done'] - FERT_TICKS * amt)
                s['inf'] = True
                W.seq += 1
                s['uid'] = W.seq
                heapq.heappush(W.ev, (s['done'], W.seq, here(), W.seq))
            return True
        return False
    return act(200, f)


def num_drones():
    return act(1, lambda: sum(1 for o in DRONES if o.alive))


def max_drones():
    return act(1, lambda: MAXD)


def _finish(d):
    d.alive = False
    for o in DRONES:
        if o.blocked is d:
            o.blocked = None
            if d.clock > o.clock:
                o.clock = d.clock
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
    finally:
        child.clock += child.pending
        child.pending = 0.0
        _finish(child)


def spawn_drone(fn):
    d = me()
    n_alive = act(1, lambda: sum(1 for o in DRONES if o.alive))
    if n_alive >= MAXD:
        return None
    child = Drone(d.clock + 200, d.x, d.y)
    DRONES.append(child)
    d.clock += 200
    t = threading.Thread(target=_runner, args=(child, fn))
    child.thread = t
    t.daemon = True
    t.start()
    return child


def wait_for(h):
    d = me()
    d.clock += d.pending
    d.pending = 0.0
    if h.alive:
        d.blocked = h
        m = _pick()
        d.ev.clear()
        if m is not None:
            m.ev.set()
        d.ev.wait()
    elif h.clock > d.clock:
        d.clock = h.clock
    return h.ret


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



src = open(SRC).read()
for a in sys.argv[4:]:
    if "=" in a:
        kk, vv = a.split("=", 1)
        src = re.sub(r"^%s = \S+" % kk, "%s = %s" % (kk, vv), src, count=1, flags=re.M)

env = {
    "North": North, "East": East, "South": South, "West": West,
    "Items": Items, "Entities": Entities, "Grounds": Grounds,
    "get_world_size": get_world_size, "get_pos_x": get_pos_x, "get_pos_y": get_pos_y,
    "num_items": num_items, "get_tick_count": get_tick_count,
    "quick_print": quick_print, "print": print_, "move": move,
    "measure": measure, "get_entity_type": get_entity_type, "get_ground_type": get_ground_type,
    "get_water": get_water, "can_harvest": can_harvest,
    "till": till, "plant": plant, "harvest": harvest, "use_item": use_item, "clear": clear,
    "spawn_drone": spawn_drone, "wait_for": wait_for,
    "num_drones": num_drones, "max_drones": max_drones,
    "abs": abs, "len": len, "range": grange, "_ix": _ix,
}

reset()
root = Drone(0, 0, 0)
DRONES.append(root)
local.d = root
sys.setrecursionlimit(100000)
if LINE > 0:
    sys.settrace(_trace)
exec(compile(ast.fix_missing_locations(_IxWrap().visit(ast.parse(src))), SRC, "exec"), env)
sys.settrace(None)
root.clock += root.pending
root.alive = False

ok_ = W.pumpkin >= GOAL
print("%-18s seed=%d maxd=%d : かぼちゃ=%d/%d 収穫=%d 大きさ別=%s 植えた=%d 水=%d 水の失敗=%d 肥料=%d 感染マス=%d 実時間=%d  %s"
      % (SRC.split("/")[-1], SEED, MAXD, W.pumpkin, GOAL, W.harvests, dict(sorted(W.sizes.items())),
         W.plants, W.water_used, W.water_fail, W.fert_used, W.infected, root.clock, "OK" if ok_ else "*** FAIL ***"))
if os.environ.get('CYCLES'):
    # 収穫と収穫の間隔（周期）を8回ずつまとめて出す
    ht = [0.0] + W.htimes
    gaps = [ht[i + 1] - ht[i] for i in range(len(ht) - 1)]
    for i in range(0, len(gaps), 8):
        g = gaps[i:i + 8]
        print("  周期 %2d-%2d 平均 %6.0f 最大 %6.0f" % (i + 1, i + len(g), sum(g) / len(g), max(g)))
if PROFILE:
    for k, v in sorted(PROF.items(), key=lambda kv: -kv[1]):
        print("  行数 %-14s %d" % (k, v))
if not ok_:
    sys.exit(1)
