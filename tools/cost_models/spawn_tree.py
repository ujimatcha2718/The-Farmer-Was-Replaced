"""ドローンを各列へ配る時間の下限を動的計画法で求める（生成・移動とも 200 tick）．
H(a,b)：自分の列の左に a 列，右に b 列を受け持つドローンが，全員を担当の列に
着かせるまでの最短時間．子を1機出し（200），子に片側の遠い側 [p..端] を任せる．
子は q 列目まで歩き（200*q），そこから H を再帰する．親は残りを続ける．
wrap=True なら 32 列の輪の上で根を真ん中に置く（左15，右16）．"""
import functools, sys
sys.setrecursionlimit(10000)
C = 200

@functools.lru_cache(None)
def H(a, b):
    if a == 0 and b == 0:
        return 0
    best = 10**9
    for side in (0, 1):
        m = b if side == 0 else a
        o = a if side == 0 else b
        for p in range(1, m + 1):          # 子の区間 p..m（自分から p..m 列目）
            for q in range(p, m + 1):      # 子が着く位置
                t = C + max(C * q + H(q - p, m - q) if side == 0 else C * q + H(m - q, q - p),
                            H(o, p - 1) if side == 0 else H(p - 1, o))
                best = min(best, t)
    return best

if __name__ == "__main__":
    print("直線（根は端，右に31列）:", H(0, 31))
    print("輪（根を真ん中，左15右16）:", H(15, 16))
    print("現行（親が31機を順に生成，遠い順）: 6400")
