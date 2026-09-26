"""8x8・2機（近い方が行く）で，迷路ごとの歩数のばらつきを「迷路の形」と「宝の運」に分ける．
同じ迷路で宝の列だけ変えて何度も回し，迷路ごとの平均（形の効果）と，その中のばらつき（運）を比べる．
あわせて，待っている機体を動かす方式を比べる：
  near      : 動かない（現行）
  near_home : 集めなかった方は，自分の待機地点（迷路を左右に分けた中心）へ戻る．担当判定では待機地点にいるとみなす
"""
import random, statistics as S
from maze_model import maze_dfs, dist_from

def steps(adj, m, rng, policy, T=301):
    dc = {}
    def d(a, b):
        if a not in dc: dc[a] = dist_from(adj, a)
        return dc[a][b]
    homes = [(m // 2) * m + m // 4, (m // 2) * m + 3 * m // 4]
    pos = list(homes); tot = 0
    t = rng.randrange(m * m)
    for i in range(T):
        o = 0 if d(pos[0], t) <= d(pos[1], t) else 1
        tot += d(pos[o], t); pos[o] = t
        if policy == "near_home":
            pos[1 - o] = homes[1 - o]
        nt = t
        while nt == t: nt = rng.randrange(m * m)
        t = nt
    return tot

m = 8
for pol in ("near", "near_home"):
    means = []; within = []
    for s in range(60):
        adj = maze_dfs(m, random.Random(s), (m // 2) * m + m // 2)
        r = [steps(adj, m, random.Random(1000 * s + k), pol) for k in range(20)]
        means.append(S.mean(r)); within.append(S.stdev(r))
    print("%-9s 1迷路の歩数 平均 %.0f，形による標準偏差 %.0f，運による標準偏差 %.0f"
          % (pol, S.mean(means), S.stdev(means), S.mean(within)))


def steps_opt(adj, m, rng, T=301):
    """上限の見積もり：集めなかった方は，集めた方の位置 p に対して E[min(d(c,t), d(p,t))] が最小の c へ
    瞬時に移るとみなす（移動の時間は無視．実際は間に合わないこともある）"""
    D = [dist_from(adj, a) for a in range(m * m)]
    best = {}
    for p in range(m * m):
        bc = min(range(m * m), key=lambda c: sum(min(D[c][t], D[p][t]) for t in range(m * m)))
        best[p] = bc
    pos = [0, 0]; tot = 0
    t = rng.randrange(m * m)
    for i in range(T):
        o = 0 if D[pos[0]][t] <= D[pos[1]][t] else 1
        tot += D[pos[o]][t]; pos[o] = t
        pos[1 - o] = best[t]
        nt = t
        while nt == t: nt = rng.randrange(m * m)
        t = nt
    return tot

r = []
for s in range(30):
    adj = maze_dfs(m, random.Random(s), (m // 2) * m + m // 2)
    r.append(steps_opt(adj, m, random.Random(s)))
print("near_opt（上限） 1迷路の歩数 平均 %.0f" % S.mean(r))
