"""maze_idle.py の時間の順序を直した版．
待っている機体の目的地は「直前に集めた宝」で決まり，歩けるのは「次の旅」の間（L+1 歩ぶん）だけ．
担当の判定：
  spot  : 待っている機体は目的地にいるとみなす（実装 v2 と同じ．実際の位置とずれる）
  track : 2機とも同じ計算で，待っている機体の実際の位置（目的地へ L+1 歩進んだ位置）を追う
"""
import random, statistics as S
from maze_model import maze_dfs, dist_from
from maze_idle import tree_parts, centroid

def run(adj, m, rng, mode, T=301):
    n = m * m
    D = [dist_from(adj, a) for a in range(n)]
    s1, s2 = tree_parts(adj, m); A = centroid(D, s1); B = centroid(D, s2)
    def step_toward(p, tgt, k):
        for i in range(k):
            if p == tgt: break
            p = min(adj[p], key=lambda x: D[x][tgt])
        return p
    pos = [0, 0]; tgt = [None, None]; tot = 0
    t = rng.randrange(n)
    for i in range(T):
        if mode == "near":
            view = pos
        elif mode == "spot":
            view = [tgt[j] if tgt[j] is not None else pos[j] for j in range(2)]
        else:
            view = pos
        o = 0 if D[view[0]][t] <= D[view[1]][t] else 1
        L = D[pos[o]][t]; tot += L
        j = 1 - o
        if mode != "near" and tgt[j] is not None:
            pos[j] = step_toward(pos[j], tgt[j], L + 1)
        pos[o] = t; tgt[o] = None
        if mode != "near":
            tgt[j] = B if D[t][A] <= D[t][B] else A
        nt = t
        while nt == t: nt = rng.randrange(n)
        t = nt
    return tot

m = 8
for mode in ("near", "spot", "track"):
    per = []
    for s in range(48):
        adj = maze_dfs(m, random.Random(s), (m // 2) * m + m // 2)
        per.append(run(adj, m, random.Random(s + 777), mode))
    mx = [max(per[i:i + 16]) for i in range(0, 48, 16)]
    print("%-6s 1迷路の歩数 平均 %.0f，16迷路の最大 平均 %.0f" % (mode, S.mean(per), S.mean(mx)))
