"""迷路の収集段階の費用モデル（壁の消失は無視＝木のまま）．
迷路の作り方はゲームと同じとは限らない（不明）．2通りで比べる：
  dfs    : 乱択 DFS（穴掘り法．通路が長く分岐が少ない）
  wilson : 一様全域木（Wilson 法）
現行と同じ待機地点（4x8 の格子の中心）と担当範囲（木の上の多始点 BFS）を使い，
宝は一様ランダムに現れるとする．担当ドローンが今いる位置から木の経路で歩く．"""
import random, statistics as S, sys
from collections import deque

def neighbors(c, n):
    x, y = divmod(c, n)
    if x > 0: yield c - n
    if x < n - 1: yield c + n
    if y > 0: yield c - 1
    if y < n - 1: yield c + 1

def maze_dfs(n, rng, start):
    adj = {c: [] for c in range(n * n)}
    seen = {start}; st = [start]
    while st:
        c = st[-1]
        nb = [m for m in neighbors(c, n) if m not in seen]
        if not nb: st.pop(); continue
        m = rng.choice(nb); seen.add(m); adj[c].append(m); adj[m].append(c); st.append(m)
    return adj

def maze_wilson(n, rng, start):
    adj = {c: [] for c in range(n * n)}
    intree = {start}
    cells = list(range(n * n)); rng.shuffle(cells)
    for c in cells:
        if c in intree: continue
        nxt = {}; u = c
        while u not in intree:
            nxt[u] = rng.choice(list(neighbors(u, n))); u = nxt[u]
        u = c
        while u not in intree:
            intree.add(u); v = nxt[u]; adj[u].append(v); adj[v].append(u); u = v
    return adj

def bfs(adj, srcs):
    d = {}; own = {}; q = deque()
    for i, s in enumerate(srcs):
        if s not in d: d[s] = 0; own[s] = i; q.append(s)
    while q:
        c = q.popleft()
        for m in adj[c]:
            if m not in d: d[m] = d[c] + 1; own[m] = own[c]; q.append(m)
    return d, own

def dist_from(adj, s):
    return bfs(adj, [s])[0]

def stations(n, D):
    a = 1
    while (a + 1) * (a + 1) <= D: a += 1
    while D % a: a -= 1
    b = D // a
    return [((2 * i + 1) * n // (2 * a)) * n + (2 * j + 1) * n // (2 * b) for i in range(a) for j in range(b)]

def collect(adj, n, st, T, rng):
    """T 個の宝を集める移動の合計．担当は多始点 BFS．ドローンは集めた場所に残り，
    次の宝の担当でなければ家へ帰る（帰る途中でも担当になれば今の位置から歩く）．
    簡単のため，帰りは次の宝が出る前に終わっているとみなす（現行は並行して帰る）"""
    _, own = bfs(adj, st)
    pos = list(st); tot = 0; last = None
    dcache = {}
    def dist(a, b):
        if a not in dcache: dcache[a] = dist_from(adj, a)
        return dcache[a][b]
    t = rng.randrange(n * n)
    for k in range(T):
        o = own[t]
        tot += dist(pos[o], t); pos[o] = t
        # 他のドローンは家へ（間に合うとみなす）
        nt = rng.randrange(n * n)
        for i in range(len(pos)):
            if i != own[nt]: pos[i] = st[i]
        t = nt
    return tot / T

if __name__ == "__main__":
    n = 32; D = 32
    for kind, gen in (("dfs", maze_dfs), ("wilson", maze_wilson)):
        r = []
        for s in range(6):
            rng = random.Random(s)
            adj = gen(n, rng, (n // 2) * n + n // 2)
            r.append(collect(adj, n, stations(n, D), 301, rng))
        print("%-6s 宝1個あたりの移動 %.1f 回（%.0f tick）" % (kind, S.mean(r), 200 * S.mean(r)))
