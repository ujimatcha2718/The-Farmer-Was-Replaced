"""snake.py を，ゲーム挙動の前提を切り替えながら検証する．

引数: n seed WRAP GROW_ON_ARRIVAL
  WRAP=1 端で回り込む / 0 回り込まない（端で move が失敗）
  GROW_ON_ARRIVAL=1 リンゴに乗った手で尾が伸びる / 0 次の手で伸びる（Wiki の記述）
"""
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))

import ast
import random
import re
import sys
from collections import deque

SRC = _os.environ.get("SRC", _os.path.join(_HERE, "..", "src", "snake.py"))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 1
WRAP = int(sys.argv[3]) if len(sys.argv) > 3 else 1
GROW_ARR = int(sys.argv[4]) if len(sys.argv) > 4 else 0
MULT = 32

North, East, South, West = "N", "E", "S", "W"
DXY = {North: (0, 1), East: (1, 0), South: (0, -1), West: (-1, 0)}


class Items:
    Bone = "Bone"
    Cactus = "Cactus"


class Hats:
    Straw_Hat = "Straw"
    Dinosaur_Hat = "Dino"


class Leaderboards:
    Dinosaur = "Dino"


class W:
    pass


def reset_world(seed):
    W.rng = random.Random(seed)
    W.n = N
    W.all = {(x, y) for x in range(N) for y in range(N)}
    W.x = 0
    W.y = 0
    W.bones = 0
    W.hat = Hats.Straw_Hat
    W.body = deque()
    W.occ = set()
    W.apple = None
    W.next_apple = None
    W.grow_pending = False
    W.ticks = 0
    W.moves = 0
    W.move_ticks = 0
    W.eaten = 0
    W.max_len = 0
    W.runs = 0
    W.fails = 0
    W.eaten_at_move = []


def tick(k=1):
    W.ticks += k


def spawn_apple():
    f = sorted(W.all - W.occ)
    if not f:
        return None
    return W.rng.choice(f)


def get_world_size():
    tick(); return float(W.n)


def get_pos_x():
    tick(); return float(W.x)


def get_pos_y():
    tick(); return float(W.y)


def num_items(it):
    tick()
    return W.bones if it == Items.Bone else 10 ** 9


def get_tick_count():
    return W.ticks


def quick_print(*a):
    print("   quick_print:", *a)


def print_(*a):
    print("   PRINT:", *a)


def clear():
    tick(200)
    W.body = deque()
    W.occ = set()
    W.apple = None
    W.next_apple = None
    W.grow_pending = False
    W.eaten = 0
    W.hat = Hats.Straw_Hat
    W.x = 0
    W.y = 0


def change_hat(h):
    tick(200)
    if W.hat == Hats.Dinosaur_Hat and h != Hats.Dinosaur_Hat:
        tail = len(W.body) - 1
        if tail < 0:
            tail = 0
        W.bones += tail * tail * MULT
        W.runs += 1
        W.body = deque()
        W.occ = set()
        W.apple = None
        W.next_apple = None
        W.grow_pending = False
        W.eaten = 0
    W.hat = h
    if h == Hats.Dinosaur_Hat:
        W.body = deque([(W.x, W.y)])
        W.occ = {(W.x, W.y)}
        W.max_len = 1
        W.apple = spawn_apple()


def move_cost():
    c = 400
    for _ in range(W.eaten):
        c = int(c * 0.97)
        if c < 1:
            c = 1
    return c


def move(d):
    n = W.n
    dx, dy = DXY[d]
    nx, ny = W.x + dx, W.y + dy
    if nx < 0 or nx >= n or ny < 0 or ny >= n:
        if not WRAP:
            tick(); W.fails += 1
            return False
        nx = nx % n
        ny = ny % n
    if W.hat != Hats.Dinosaur_Hat:
        tick(200)
        W.x, W.y = nx, ny
        return True
    # 尾が動くか＝この手で伸びないか
    if GROW_ARR:
        grows = (W.apple is not None and (nx, ny) == W.apple)
    else:
        grows = W.grow_pending
    if len(W.body) >= n * n:
        tick(); W.fails += 1
        return False
    if (nx, ny) in W.occ:
        if grows or len(W.body) == 0 or W.body[0] != (nx, ny):
            tick(); W.fails += 1
            return False
    c = move_cost()
    tick(c); W.move_ticks += c; W.moves += 1
    W.eaten_at_move.append(W.eaten)
    if grows:
        W.eaten += 1
    else:
        if W.body:
            W.occ.discard(W.body.popleft())
    W.x, W.y = nx, ny
    W.body.append((nx, ny))
    W.occ.add((nx, ny))
    if len(W.body) > W.max_len:
        W.max_len = len(W.body)
    if GROW_ARR:
        # リンゴに乗った手で尾が伸びる解釈．乗った時点で消費されるので
        # そのマスで measure() は何も返さない（＝位置を知る手段が無い）
        if W.apple is not None and (nx, ny) == W.apple:
            W.apple = spawn_apple()
    else:
        # Wiki の記述：乗った次の手で食べて伸びる．乗っているあいだ
        # measure() は「次のリンゴ」の位置を返す
        if W.grow_pending:
            W.grow_pending = False
            W.apple = W.next_apple
            W.next_apple = None
        if W.apple is not None and (nx, ny) == W.apple:
            W.grow_pending = True
            W.next_apple = spawn_apple()
    return True


def can_move(d):
    tick()
    n = W.n
    dx, dy = DXY[d]
    nx, ny = W.x + dx, W.y + dy
    if nx < 0 or nx >= n or ny < 0 or ny >= n:
        if not WRAP:
            return False
        nx = nx % n
        ny = ny % n
    if W.hat != Hats.Dinosaur_Hat:
        return True
    if len(W.body) >= n * n:
        return False
    if (nx, ny) in W.occ:
        if GROW_ARR:
            grows = (W.apple is not None and (nx, ny) == W.apple)
        else:
            grows = W.grow_pending
        if grows or len(W.body) == 0 or W.body[0] != (nx, ny):
            return False
    return True


def measure(direction=None):
    tick()
    if W.hat == Hats.Dinosaur_Hat and W.grow_pending:
        return W.next_apple
    return None


def grange(*a):
    # ゲームは小数を含む range を受け付けるので，それに合わせる
    return range(*[int(v) for v in a])


SAFE = sys.argv[5] if len(sys.argv) > 5 else None
CUT = sys.argv[6] if len(sys.argv) > 6 else None
src = open(SRC).read()
ast.parse(src)
if SAFE:
    src = re.sub(r"SAFE_MARGIN = \d+", "SAFE_MARGIN = " + SAFE, src, count=1)
if CUT:
    src = re.sub(r"CUT_LEN = \d+", "CUT_LEN = " + CUT, src, count=1)
src = src.replace("DEBUG = False", "DEBUG = True")
full = (N * N - 1) ** 2 * MULT
src = src.replace("TARGET_BONES = 33488928", "TARGET_BONES = %d" % full)

env = {
    "North": North, "East": East, "South": South, "West": West,
    "Items": Items, "Hats": Hats, "Leaderboards": Leaderboards,
    "get_world_size": get_world_size, "get_pos_x": get_pos_x, "get_pos_y": get_pos_y,
    "num_items": num_items, "get_tick_count": get_tick_count, "quick_print": quick_print,
    "print": print_, "move": move, "measure": measure, "change_hat": change_hat,
    "clear": clear, "can_move": can_move, "abs": abs, "len": len, "range": grange,
}

lines = [0]
per_line = {}


def tracer(frame, event, arg):
    if event == "line" and frame.f_code.co_filename == SRC:
        lines[0] += 1
        per_line[frame.f_lineno] = per_line.get(frame.f_lineno, 0) + 1
    return tracer


def line_costs(text):
    tree = ast.parse(text)
    cb = {}
    for node in ast.walk(tree):
        ln = getattr(node, "lineno", None)
        if ln is None:
            continue
        c = 0
        if isinstance(node, ast.BinOp) or isinstance(node, ast.UnaryOp):
            c = 1
        elif isinstance(node, ast.Compare):
            c = len(node.ops)
        elif isinstance(node, ast.BoolOp):
            c = len(node.values) - 1
        elif isinstance(node, ast.Call):
            c = 1
        elif isinstance(node, ast.Subscript):
            c = 1
        if c:
            cb[ln] = cb.get(ln, 0) + c
    return cb


reset_world(SEED)
sys.settrace(tracer)
exec(compile(src, SRC, "exec"), env)
sys.settrace(None)

cb = line_costs(src)
comp = 0
for ln, c in per_line.items():
    comp += c * cb.get(ln, 0)


# --- 移動コストの減衰モデルを2通りで比較 ---
def costs_A(kmax):
    # floor(x*0.97) を繰り返す（下限1）
    out = []
    c = 400
    for k in range(kmax + 2):
        out.append(c)
        c = int(c * 0.97)
        if c < 1:
            c = 1
    return out


def costs_B(kmax):
    # x -= floor(0.03*x)．0.03x<1 になると減らなくなる（下限33）
    out = []
    c = 400
    for k in range(kmax + 2):
        out.append(c)
        c = c - int(0.03 * c)
    return out


kmax = max(W.eaten_at_move) if W.eaten_at_move else 0
A = costs_A(kmax); B = costs_B(kmax)
ta = 0
tb = 0
for e in W.eaten_at_move:
    ta += A[e]
    tb += B[e]
other = W.ticks - W.move_ticks     # move 以外のAPI tick
hist = {}
for e in W.eaten_at_move:
    hist[e] = hist.get(e, 0) + 1
fn = "fitdump_%s.txt" % (CUT if CUT else "def")
f = open(fn, "w")
f.write("lines %d\n" % lines[0])
f.write("other %d\n" % (W.ticks - W.move_ticks))
for e in sorted(hist):
    f.write("h %d %d\n" % (e, hist[e]))
f.close()
print("lines=%d  other_api=%d" % (lines[0], W.ticks - W.move_ticks))
print("moves=%d  move_ticks(modelA)=%d  move_ticks(modelB)=%d" % (W.moves, ta, tb))
print("  model A 合計= %d" % (ta + other + comp))
print("  model B 合計= %d" % (tb + other + comp))
print("  B の下限コスト=%d" % B[-1])
tag = "n=%d seed=%d WRAP=%d GROW_ON_ARRIVAL=%d" % (N, SEED, WRAP, GROW_ARR)
ok = (W.max_len == N * N) and (W.bones >= full) and W.runs == 1
print("%-42s maxlen=%4d/%4d runs=%d moves=%7d total_ticks=%9d %s"
      % (tag, W.max_len, N * N, W.runs, W.moves, W.ticks + comp, "OK" if ok else "*** FAIL ***"))
if not ok:
    sys.exit(1)
