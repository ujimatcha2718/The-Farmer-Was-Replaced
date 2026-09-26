"""exact_turn に「パスの最後の交換のあとは動かない（その場で折り返す）」を加えた版．
ドローンが p にいれば，辺 (p,p+1) も辺 (p-1,p) も交換できるので，最後の交換位置で
向きを変えれば1パスにつき1歩減る．"""
import random

def fwd_last(a, pos, hi):
    m = a[pos]; last = -1
    for p in range(pos, hi):
        if m > a[p + 1]: last = p
        else: m = a[p + 1]
    return last

def bwd_last(a, pos, lo):
    m = a[pos]; last = -1
    for p in range(pos, lo, -1):
        if m < a[p - 1]: last = p
        else: m = a[p - 1]
    return last

def sort2(a, pos, st, known=True, pull=True):
    """st = [交換, 移動, パス数]．known=False なら1パス目は値を知らない（端まで進む）"""
    n = len(a); lo = 0; hi = n - 1
    d = 1 if pos < hi else -1
    while lo < hi:
        st[2] += 1
        if d > 0:
            if known:
                last = fwd_last(a, pos, hi)
                if last < 0: return pos
            else:
                last = hi - 1
            known = True
            found = -1
            while True:
                if a[pos] > a[pos + 1]:
                    a[pos], a[pos + 1] = a[pos + 1], a[pos]; st[0] += 1; found = pos
                    if pull and pos > lo and a[pos - 1] > a[pos]:
                        a[pos - 1], a[pos] = a[pos], a[pos - 1]; st[0] += 1
                if pos >= last: break
                st[1] += 1; pos += 1
            if found < 0: return pos
            hi = found
            # found < pos のとき（1パス目で未知だった場合）は found まで戻る必要はない
        else:
            last = bwd_last(a, pos, lo)
            if last < 0: return pos
            while True:
                if a[pos] < a[pos - 1]:
                    a[pos], a[pos - 1] = a[pos - 1], a[pos]; st[0] += 1
                    if pull and pos < hi and a[pos + 1] < a[pos]:
                        a[pos + 1], a[pos] = a[pos], a[pos + 1]; st[0] += 1
                if pos <= last: break
                st[1] += 1; pos -= 1
            lo = last
        d = -d
    return pos

def plant_pass(a, st):
    for y in range(1, len(a)):
        if a[y - 1] > a[y]:
            a[y - 1], a[y] = a[y], a[y - 1]; st[0] += 1

def trial(seed, N=32, K=10):
    rng = random.Random(seed)
    grid = [[rng.randrange(K) for y in range(N)] for x in range(N)]
    ct = []; cols = []
    for x in range(N):
        a = list(grid[x]); st = [0, 0, 0]
        plant_pass(a, st)
        sort2(a, N - 1, st)
        assert a == sorted(grid[x])
        cols.append(a); ct.append(st)
    rt = []
    for y in range(N):
        row = [cols[x][y] for x in range(N)]; st = [0, 0, 0]
        sort2(row, 0, st, known=False)
        assert row == sorted(row)
        rt.append(st)
    return ct, rt

if __name__ == "__main__":
    S = 200; cm = rm = cmv = rmv = cp = rp = 0
    for s in range(S):
        ct, rt = trial(s)
        cm += max(200 * (a + b) for a, b, c in ct); rm += max(200 * (a + b) for a, b, c in rt)
        cmv += sum(b for a, b, c in ct) / 32; rmv += sum(b for a, b, c in rt) / 32
        cp += sum(c for a, b, c in ct) / 32; rp += sum(c for a, b, c in rt) / 32
    print("exact2 列: 移動%6.1f パス%5.1f 最大%8.0f | 行: 移動%6.1f パス%5.1f 最大%8.0f | 計 %8.0f"
          % (cmv/S, cp/S, cm/S, rmv/S, rp/S, rm/S, (cm+rm)/S))
