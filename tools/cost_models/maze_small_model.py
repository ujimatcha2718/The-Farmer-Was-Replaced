"""小さな迷路を並べて集める案の費用モデル（推定）．
1迷路あたりの時間 = 探索 + 宝の数 x (use_item 200 + 移動 200 x 距離 + 1個あたりの処理 O) + 作り直し
距離：迷路の中で宝は一様ランダム．担当は木の上の多始点 BFS（待機地点は迷路を k 等分した中心）．
集めたドローンはその場に残り，担当でない方は待機地点へ戻る（間に合うとみなす）．
目標 9,863,168 = 金 m*m*32 の宝を全迷路で集める．1迷路で301個（再配置300＋収穫1）を超えるなら作り直す．"""
import random, statistics as S
from maze_model import maze_dfs, maze_wilson, bfs, dist_from

TARGET = 9863168
O = 250      # 宝1個あたりの処理（行の費用など．推定）

def per_treasure_dist(m, k, gen, seeds=30, T=300):
    r = []
    for s in range(seeds):
        rng = random.Random(s)
        adj = gen(m, rng, (m // 2) * m + m // 2)
        # 待機地点：k=1 は中心，k=2 は左右の半分の中心
        # k 機を a x b の格子の中心に置く（現行の make_stations と同じ）
        a = 1
        while (a + 1) * (a + 1) <= k: a += 1
        while k % a: a -= 1
        b = k // a
        st = [((2 * i + 1) * m // (2 * a)) * m + (2 * j + 1) * m // (2 * b) for i in range(a) for j in range(b)]
        _, own = bfs(adj, st)
        dc = {}
        def d(a, b):
            if a not in dc: dc[a] = dist_from(adj, a)
            return dc[a][b]
        pos = list(st); tot = 0
        t = rng.randrange(m * m)
        for i in range(T):
            o = own[t]; tot += d(pos[o], t); pos[o] = t
            nt = rng.randrange(m * m)
            for j in range(k):
                if j != own[nt]: pos[j] = st[j]
            t = nt
        r.append(tot / T)
    return S.mean(r)

def plan(m, nmaze, k, gen):
    gold = m * m * 32
    need = -(-TARGET // gold)                 # 必要な宝の数
    per_maze = need / nmaze
    rebuilds = int((per_maze - 1) // 301)     # 301個を超えるぶんの作り直し回数
    dist = per_treasure_dist(m, k, gen)
    explore = 200 * 2 * (m * m - 1) / 1.0     # 1機で全探索（往復）．推定
    t = explore * (1 + rebuilds) + rebuilds * 600 + per_maze * (200 + 200 * dist + O)
    return per_maze, dist, t

if __name__ == "__main__":
    for gname, gen in (("dfs", maze_dfs), ("wilson", maze_wilson)):
        print("迷路の作り方:", gname)
        for m, nmaze, k in ((8, 16, 2), (8, 16, 1), (5, 32, 1), (6, 25, 1), (7, 16, 2), (16, 4, 8), (32, 1, 32)):
            pm, d, t = plan(m, nmaze, k, gen)
            print("  %2dx%-2d 迷路%2d個 1迷路%d機 : 1迷路の宝 %5.1f 個，距離 %4.1f，収集 %7.0f tick"
                  % (m, m, nmaze, k, pm, d, t))
