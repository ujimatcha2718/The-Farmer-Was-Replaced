"""迷路の並行シミュレータ：ドローンを1機1スレッドで動かし，仮想時刻で実時間を出す．
（1度に1機だけが動く．API 呼び出しごとに，時刻が最小の機体へ手番を渡し，
自分の番で効果を適用してから時刻を費用ぶん進める）

迷路の仕様（probes/maze_small_probe.py の実機結果に合わせた部分と，推定の部分）
  ・茂みの上で use_item(Weird_Substance, m * 2**(段階-1)) → 茂みを中心に m x m の迷路
    （範囲は b - m//2 .. b - m//2 + m - 1．実機確認）．迷路は乱択 DFS で作る（作り方は推定）
  ・宝の上で同じ量を use_item → 金 m*m*2**(段階-1)，宝は迷路内の別のマスへ（実機確認）．
    再配置のたびに確率 WALLP で壁を1つ消す（頻度は 8x8 の実機 probe に合わせた．場所は一様ランダムと推定）．300回を超えると動かない（推定）
  ・宝の上で harvest → 金 m*m*2**(段階-1)，迷路は消えて草に戻る（実機確認）
  ・迷路の中のドローンは壁を越えられない．迷路の外から迷路のマスへは入れない（推定）
  ・複数の迷路を同時に置ける．measure() は自分がいる迷路の宝を返し，迷路の外では None
  ・盤面の端で move は回り込む（実機確認）

引数: src seed [maxdrones] [NAME=value ...]
環境変数: LINE=ソース1行の費用（既定 2.37．0 にすると待ちの空回りが多すぎて遅い），WALLP=再配置で壁が消える確率（既定 0.084．実機の8x8で299回に25枚），
          UNLOCK=迷路の段階（既定 6），WS=奇妙な物質の初期量（既定 10**9）
"""
import ast
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
WALLP = float(os.environ.get('WALLP', '0.084'))   # 実機 probe：8x8 で再配置299回に壁25枚
UNLOCK = int(os.environ.get('UNLOCK', '6'))
WS0 = int(os.environ.get('WS', str(10 ** 9)))
UNIT = 2 ** (UNLOCK - 1)
MAX_REUSE = 300

North, East, South, West = "N", "E", "S", "W"
DXY = {North: (0, 1), East: (1, 0), South: (0, -1), West: (-1, 0)}


class Items:
    Gold = "Gold"
    Weird_Substance = "WS"


class Entities:
    Bush = "Entities.Bush"
    Hedge = "Entities.Hedge"
    Treasure = "Entities.Treasure"
    Grass = "Entities.Grass"


class Grounds:
    Grassland = "Grassland"
    Soil = "Soil"


class Unlocks:
    Mazes = "Mazes"


class Drone:
    def __init__(self, clock, x, y):
        self.clock = clock
        self.x = x
        self.y = y
        self.alive = True
        self.blocked = None      # wait_for で待っている相手（Drone）
        self.thread = None
        self.ret = None
        self.pending = 0.0
        self.ev = threading.Event()


class Maze:
    pass


# 1度に1機だけが動く（手番を持つ機体）．手番は「時刻が最小の動ける機体」へ渡す
local = threading.local()
DRONES = []
LOCK = threading.Lock()


class W:
    pass


def reset():
    W.rng = random.Random(SEED)
    W.gold = 0
    W.ws = WS0
    W.ent = {}
    W.ground = {}
    for x in range(N):
        for y in range(N):
            W.ent[(x, y)] = Entities.Grass
            W.ground[(x, y)] = Grounds.Grassland
    W.mazes = []
    W.maze_of = {}       # (x,y) -> Maze
    W.moves = 0
    W.treasures = 0
    W.built = 0
    W.blocked_moves = 0


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
            sys.stderr.write("progress acts=%d gold=%d treasures=%d mazes=%d clocks=%s\n" % (
                _NACT[0], W.gold, W.treasures, len(W.mazes),
                sorted(int(o.clock) for o in DRONES if o.alive)[:4]))
    if d.pending:
        d.clock += d.pending
        d.pending = 0.0
    _yield(d)
    r = fn()
    d.clock += cost
    return r


# --- 迷路 ---
def make_maze(bx, by, m):
    x0 = bx - m // 2
    y0 = by - m // 2
    if x0 < 0 or y0 < 0 or x0 + m > N or y0 + m > N:
        return False     # 盤面からはみ出す場合の仕様は不明．ここでは失敗とする
    cells = [(x0 + i, y0 + j) for i in range(m) for j in range(m)]
    for c in cells:
        if c in W.maze_of:
            return False
    Z = Maze()
    Z.m = m
    Z.x0 = x0
    Z.y0 = y0
    Z.cells = set(cells)
    Z.edges = set()
    Z.reuse = 0
    start = (bx, by)
    seen = {start}
    st = [start]
    while st:
        cx, cy = st[-1]
        cand = []
        for d in DXY.values():
            nb = (cx + d[0], cy + d[1])
            if nb in Z.cells and nb not in seen:
                cand.append(nb)
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
        W.ent[c] = Entities.Hedge
    W.ent[Z.treasure] = Entities.Treasure
    W.mazes.append(Z)
    W.built += 1
    return True


def relocate(Z):
    old = Z.treasure
    W.ent[old] = Entities.Hedge
    cells = sorted(Z.cells)
    while True:
        t = W.rng.choice(cells)
        if t != old:
            break
    Z.treasure = t
    W.ent[t] = Entities.Treasure
    if W.rng.random() < WALLP:
        # 迷路の中の隣り合う2マスの壁を1つ消す
        for k in range(20):
            a = W.rng.choice(cells)
            d = W.rng.choice(list(DXY.values()))
            b = (a[0] + d[0], a[1] + d[1])
            if b in Z.cells and frozenset((a, b)) not in Z.edges:
                Z.edges.add(frozenset((a, b)))
                break


def remove_maze(Z):
    for c in Z.cells:
        del W.maze_of[c]
        W.ent[c] = Entities.Grass
    W.mazes.remove(Z)


def target_of(d, dd):
    dx, dy = DXY[dd]
    return ((d.x + dx) % N, (d.y + dy) % N)


def passable(d, dd):
    a = (d.x, d.y)
    b = target_of(d, dd)
    za = W.maze_of.get(a)
    zb = W.maze_of.get(b)
    if za is None and zb is None:
        return True
    if za is not None and za is zb:
        return frozenset((a, b)) in za.edges
    return False


# --- ゲームAPI ---
def get_world_size():
    return act(1, lambda: float(N))


def get_pos_x():
    return act(1, lambda: float(me().x))


def get_pos_y():
    return act(1, lambda: float(me().y))


def num_unlocked(u):
    return act(1, lambda: float(UNLOCK))


def num_items(it):
    return act(1, lambda: float(W.gold if it == Items.Gold else W.ws))


def get_tick_count():
    # 手番を渡す（時刻だけを見て待つループが他の機体を止めないように）．費用は 0 とする（推定）
    return act(0, lambda: me().clock)


def quick_print(*a):
    print("   quick_print:", *a)


def print_(*a):
    print("   PRINT:", *a)


def clear():
    def f():
        for Z in list(W.mazes):
            remove_maze(Z)
        for k in W.ent:
            W.ent[k] = Entities.Grass
            W.ground[k] = Grounds.Grassland
        me().x = 0
        me().y = 0
    return act(200, f)


def can_move(dd):
    return act(1, lambda: passable(me(), dd))


def move(dd):
    d = me()
    def f():
        if not passable(d, dd):
            W.blocked_moves += 1
            return False
        d.x, d.y = target_of(d, dd)
        W.moves += 1
        return True
    return act(200, f)


def get_entity_type():
    return act(1, lambda: W.ent[(me().x, me().y)])


def get_ground_type():
    return act(1, lambda: W.ground[(me().x, me().y)])


def till():
    def f():
        k = (me().x, me().y)
        W.ground[k] = Grounds.Soil if W.ground[k] == Grounds.Grassland else Grounds.Grassland
    return act(200, f)


def plant(e):
    def f():
        k = (me().x, me().y)
        if k in W.maze_of or W.ground[k] != Grounds.Grassland:
            return False
        W.ent[k] = e
        return True
    return act(200, f)


def harvest():
    def f():
        k = (me().x, me().y)
        Z = W.maze_of.get(k)
        if Z is not None:
            if os.environ.get('WHY') and Z.reuse < MAX_REUSE:
                sys.stderr.write("早い収穫 pos=%s 宝=%s reuse=%d t=%d\n" % (k, Z.treasure, Z.reuse, me().clock))
            if Z.treasure == k:
                W.gold += Z.m * Z.m * UNIT
                W.treasures += 1
            remove_maze(Z)
            return True
        W.ent[k] = Entities.Grass
        return True
    return act(200, f)


def use_item(it, amt):
    def f():
        k = (me().x, me().y)
        if W.ws < amt:
            return False
        Z = W.maze_of.get(k)
        if Z is None:
            if W.ent[k] != Entities.Bush:
                return False
            m = int(amt) // UNIT
            if m * UNIT != amt or m < 1:
                return False
            if not make_maze(k[0], k[1], m):
                return False
            W.ws -= amt
            return True
        if Z.treasure != k or amt != Z.m * UNIT or Z.reuse >= MAX_REUSE:
            if os.environ.get('WHY'):
                sys.stderr.write("use_item 失敗 pos=%s 宝=%s amt=%s reuse=%d t=%d\n" % (k, Z.treasure, amt, Z.reuse, me().clock))
            return False
        W.ws -= amt
        W.gold += Z.m * Z.m * UNIT
        W.treasures += 1
        Z.reuse += 1
        relocate(Z)
        return True
    return act(200, f)


def measure():
    def f():
        Z = W.maze_of.get((me().x, me().y))
        if Z is None:
            return None
        return (float(Z.treasure[0]), float(Z.treasure[1]))
    return act(1, f)


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
    "Items": Items, "Entities": Entities, "Grounds": Grounds, "Unlocks": Unlocks,
    "get_world_size": get_world_size, "get_pos_x": get_pos_x, "get_pos_y": get_pos_y,
    "num_items": num_items, "num_unlocked": num_unlocked, "get_tick_count": get_tick_count,
    "quick_print": quick_print, "print": print_, "move": move, "can_move": can_move,
    "measure": measure, "get_entity_type": get_entity_type, "get_ground_type": get_ground_type,
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

TARGET = int(os.environ.get("GOAL", "9863168"))   # 合否の判定に使う額
ok = W.gold >= TARGET
print("%-22s seed=%d maxd=%d : 金=%d/%d 宝=%d 迷路=%d 移動=%d 壁にぶつかった=%d 物質=%d 実時間=%d  %s"
      % (SRC.split("/")[-1], SEED, MAXD, W.gold, TARGET, W.treasures, W.built, W.moves,
         W.blocked_moves, WS0 - W.ws, root.clock, "OK" if ok else "*** FAIL ***"))
if PROFILE:
    for k, v in sorted(PROF.items(), key=lambda kv: -kv[1]):
        print("  行数 %-14s %d" % (k, v))
if not ok:
    sys.exit(1)
