"""8x8・2機：待っている機体を「待機地点の組 A,B」のうち集めた機体から遠い方へ歩かせる案（歩く時間も入れる）．
担当の判定には，待っている機体は目的地にいるとみなす（2機の判断をそろえるため）．実際の歩数は実際の位置から数える．
時間の単位は歩（use_item を 1 歩ぶんとみなす）．
  pair_opt  : A,B を E[min(d(A,t),d(B,t))] 最小の組にする（総当たり．ゲームでは重い）
  pair_cent : 木を1本の辺で切って2つに分け，大きさが最も釣り合う切り方の各側の重心（ゲームでも安い）"""
import random, statistics as S
from maze_model import maze_dfs, dist_from

def tree_parts(adj, m):
    n = m * m
    # 根 0 の木で部分木の大きさ
    par = [-1] * n; order = []; st = [0]; seen = [False] * n; seen[0] = True
    while st:
        c = st.pop(); order.append(c)
        for x in adj[c]:
            if not seen[x]: seen[x] = True; par[x] = c; st.append(x)
    size = [1] * n
    for c in reversed(order):
        if par[c] >= 0: size[par[c]] += size[c]
    # 釣り合う辺（c と par[c] の間）
    best = min((c for c in range(n) if par[c] >= 0), key=lambda c: abs(n - 2 * size[c]))
    # c の部分木とそれ以外
    sub = set(); st = [best]
    while st:
        x = st.pop(); sub.add(x)
        for y in adj[x]:
            if y != par[x] and par[y] == x: st.append(y)
    other = set(range(n)) - sub
    return sub, other

def centroid(D, part):
    return min(part, key=lambda c: sum(D[c][t] for t in part))

def run(adj, m, rng, mode, T=301):
    n = m * m
    D = [dist_from(adj, a) for a in range(n)]
    if mode == "pair_opt":
        A, B = min(((a, b) for a in range(n) for b in range(a + 1, n)),
                   key=lambda ab: sum(min(D[ab[0]][t], D[ab[1]][t]) for t in range(n)))
    elif mode == "pair_cent":
        s1, s2 = tree_parts(adj, m); A = centroid(D, s1); B = centroid(D, s2)
    pos = [0, 0]; model = [0, 0]; tot = 0
    t = rng.randrange(n)
    for i in range(T):
        o = 0 if D[model[0]][t] <= D[model[1]][t] else 1
        L = D[pos[o]][t]; tot += L; pos[o] = t; model[o] = t
        if mode != "near":
            j = 1 - o
            tgt = B if D[t][A] <= D[t][B] else A
            # 待つ方は L+1 歩ぶんの時間だけ目的地へ歩ける（その後の判定では目的地にいるとみなす）
            walk = min(D[pos[j]][tgt], L + 1)
            # 歩いた歩数は tot に入れない（待ち時間の中なので律速に入らない）．位置は近似：着いたら tgt
            if walk >= D[pos[j]][tgt]:
                pos[j] = tgt
            else:
                # 途中の位置：tgt へ walk 歩進んだマス（木の経路上）
                p = pos[j]
                for k in range(walk):
                    p = min((x for x in adj[p]), key=lambda x: D[x][tgt])
                pos[j] = p
            model[j] = tgt
        nt = t
        while nt == t: nt = rng.randrange(n)
        t = nt
    return tot

m = 8
for mode in ("near", "pair_cent", "pair_opt"):
    per = []
    for s in range(48):
        adj = maze_dfs(m, random.Random(s), (m // 2) * m + m // 2)
        per.append(run(adj, m, random.Random(s + 777), mode))
    mx = [max(per[i:i + 16]) for i in range(0, 48, 16)]
    print("%-9s 1迷路の歩数 平均 %.0f 標準偏差 %.0f，16迷路の最大 平均 %.0f" % (mode, S.mean(per), S.stdev(per), S.mean(mx)))
