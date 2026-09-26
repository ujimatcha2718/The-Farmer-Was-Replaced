"""8x8・2機（木の上で近い方が行く）で，再配置のたびに消える壁（近道）を使う案の歩数の見積もり．
壁の消え方：再配置1回ごとに確率 P で，迷路内のランダムな壁が1枚消える（実機 probe：299回で25枚 → P≈0.084）．
方式
  tree   : 木の経路だけ（現行）
  greedy : 歩きながら通ったマスの壁を調べ（can_move），見つけた近道で「1 + 木の距離(近道の先, 宝)」が
           残りの木の距離より短ければ跳ぶ．見つけた近道は各機が自分で覚える
  oracle : 消えた壁をすべて知っていて最短経路で歩く（上限）
担当の判定は木の上の距離（2機で一致させるため）．"""
import random, statistics as S
from collections import deque
from maze_model import maze_dfs, dist_from

def run(m, seed, mode, P=0.084, T=301):
    rng = random.Random(seed)
    adj = maze_dfs(m, rng, (m // 2) * m + m // 2)
    n = m * m
    tree = {c: set(adj[c]) for c in range(n)}
    D = [dist_from(adj, a) for a in range(n)]        # 木の距離
    real = {c: set(adj[c]) for c in range(n)}         # 本当の通路
    known = [dict((c, set()) for c in range(n)) for _ in range(2)]   # 各機が知っている近道
    def nbrs(c):
        x, y = divmod(c, m)
        if x > 0: yield c - m
        if x < m - 1: yield c + m
        if y > 0: yield c - 1
        if y < m - 1: yield c + 1
    def bfs(s, t, g):
        prev = {s: None}; q = deque([s])
        while q:
            c = q.popleft()
            if c == t: break
            for x in g[c]:
                if x not in prev: prev[x] = c; q.append(x)
        L = 0; c = t
        while prev[c] is not None: c = prev[c]; L += 1
        return L
    def tree_next(c, t):
        return min(tree[c], key=lambda x: D[x][t])
    pos = [n // 2, n // 2]; tot = 0; checks = 0
    t = rng.randrange(n)
    for i in range(T):
        o = 0 if D[pos[0]][t] <= D[pos[1]][t] else 1
        c = pos[o]
        if mode == "oracle":
            tot += bfs(c, t, real)
        elif mode == "tree":
            tot += D[c][t]
        else:
            kn = known[o]
            while c != t:
                # 足元の壁を調べる（木の辺でも既知の近道でもない方向）
                for x in nbrs(c):
                    if x not in tree[c] and x not in kn[c]:
                        checks += 1
                        if x in real[c]:
                            kn[c].add(x); kn[x].add(c)
                rem = D[c][t]
                nxt = tree_next(c, t)
                for x in kn[c]:
                    if 1 + D[x][t] < rem:
                        rem = 1 + D[x][t]; nxt = x
                c = nxt; tot += 1
        pos[o] = t
        # 再配置：宝が動き，確率 P で壁が1枚消える
        if rng.random() < P:
            for k in range(50):
                a = rng.randrange(n); b = rng.choice(list(nbrs(a)))
                if b not in real[a]:
                    real[a].add(b); real[b].add(a); break
        nt = t
        while nt == t: nt = rng.randrange(n)
        t = nt
    return tot, checks

for mode in ("tree", "greedy", "oracle"):
    r = [run(8, s, mode) for s in range(48)]
    st = [x[0] for x in r]
    mx = [max(st[i:i + 16]) for i in range(0, 48, 16)]
    print("%-6s 1迷路の歩数 平均 %.0f，16迷路の最大 平均 %.0f，壁を調べた回数 %.0f" % (mode, S.mean(st), S.mean(mx), S.mean(x[1] for x in r)))
