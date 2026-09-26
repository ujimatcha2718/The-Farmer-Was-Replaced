"""植え直し＋整列の戦略を費用モデルで比較する（実機の単価：移動・交換・植付・収穫・耕す=200，measure=1）."""
import random, sys

N = 32
MOVE = SWAP = PLANT = HARV = TILL = 200

def cocktail_cost(a, pos):
    """ゲーム内 cocktail(n,pos,...) と同じ手順で費用を数える．a は破壊的に整列される"""
    n = len(a); lo = 0; hi = n - 1; t = 0
    while lo < hi:
        if pos < hi:
            last = -1; t += 1
            for i in range(hi - pos):
                t += 1
                if a[pos] > a[pos+1]:
                    a[pos], a[pos+1] = a[pos+1], a[pos]; t += SWAP; last = pos
                t += MOVE; pos += 1
            if last < 0: return t
            hi = last
        if lo < hi and pos > lo:
            last = -1; t += 1
            for i in range(pos - lo):
                t += 1
                if a[pos] < a[pos-1]:
                    a[pos], a[pos-1] = a[pos-1], a[pos]; t += SWAP; last = pos
                t += MOVE; pos -= 1
            if last < 0: return t
            lo = last
    return t

def make_M():
    # 32本を 0..9 にほぼ均等（3,3,...,4,4）
    M = [3] * 10
    M[0] += 1; M[9] += 1
    return M

def column(rng, policy, K, M):
    """1列：南から北へ植え，方針に従って植え直す．戻り値 (値の列, 植付段階の費用)"""
    R = list(M) if M else None
    placed = []
    t = 0
    for y in range(N):
        t += 1 + TILL                      # 地面確認＋耕す
        while True:
            t += PLANT + 1                 # 植える＋measure
            v = rng.randrange(10)
            if policy == "all":
                ok = True
            elif policy == "multiset":
                ok = R[v] > 0
                if ok and K is not None:
                    # 置いた後に生じる転倒数＝既に置いた v より大きい数＋残りで v より小さい数
                    created = sum(1 for p in placed if p > v)
                    created += sum(R[u] for u in range(v)) 
                    ok = created <= K
            if ok:
                break
            t += HARV                      # 植え直し
        placed.append(v)
        if R is not None: R[v] -= 1
        if y < N - 1: t += MOVE
    return placed, t

def run(seed, policy, K):
    rng = random.Random(seed)
    M = make_M() if policy == "multiset" else None
    cols = []; colt = []
    for x in range(N):
        vals, t = column(rng, policy, K, M)
        t += cocktail_cost(vals, N - 1)    # 植え終わりの北端から整列
        cols.append(vals); colt.append(t)
    walk = 200 * N                         # 最遠機の生成待ち＋移動（遠い順に生成）
    ph1 = walk + max(colt)
    rowt = []
    for y in range(N):
        row = [cols[x][y] for x in range(N)]
        rowt.append(cocktail_cost(row, 0))
    ph2 = walk + max(rowt)
    return ph1 + ph2 + 400, ph1, ph2

