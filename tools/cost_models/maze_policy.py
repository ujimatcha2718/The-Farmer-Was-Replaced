"""8x8 迷路・2機の収集で，担当の決め方を比べる（歩数のみ．迷路は乱択DFS）．
  homes  : 待機地点からの多始点 BFS で担当を固定．担当でない方は待機地点へ戻る（現行）
  near   : 戻らない．新しい宝に（木の上で）近い方が行く（同じなら番号の小さい方）
1迷路あたり宝301個の歩数の合計を，迷路ごとに比べ，16迷路の最大も見る．"""
import random, statistics as S
from maze_model import maze_dfs, maze_wilson, bfs, dist_from

def run(m, gen, seed, policy, T=301):
    rng = random.Random(seed)
    adj = gen(m, rng, (m // 2) * m + m // 2)
    dc = {}
    def d(a, b):
        if a not in dc: dc[a] = dist_from(adj, a)
        return dc[a][b]
    homes = [(m // 2) * m + m // 4, (m // 2) * m + 3 * m // 4]
    _, own = bfs(adj, homes)
    pos = list(homes); tot = 0
    t = rng.randrange(m * m)
    for i in range(T):
        if policy == "homes":
            o = own[t]
        else:
            o = 0 if d(pos[0], t) <= d(pos[1], t) else 1
        tot += d(pos[o], t); pos[o] = t
        nt = t
        while nt == t: nt = rng.randrange(m * m)
        if policy == "homes":
            for j in range(2):
                if j != own[nt]: pos[j] = homes[j]
        t = nt
    return tot

for gname, gen in (("dfs", maze_dfs), ("wilson", maze_wilson)):
    for pol in ("homes", "near"):
        per = [run(8, gen, s, pol) for s in range(160)]
        mx = [max(per[i:i + 16]) for i in range(0, 160, 16)]
        print("%-6s %-5s 1迷路の歩数 平均 %.0f（宝1個 %.2f） 標準偏差 %.0f，16迷路の最大 平均 %.0f"
              % (gname, pol, S.mean(per), S.mean(per) / 301, S.stdev(per), S.mean(mx)))
