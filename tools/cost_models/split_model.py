"""行の段階で，整列の途中に「独立な切れ目」ができたら右側を新しい機体に任せる案の上限見積もり．
切れ目 m：未整列区間 [lo,hi] の中で max(a[lo..m-1]) <= min(a[m..hi])．
各パスの終わり（時刻 t >= AVAIL）に，残り仕事が最も均等に分かれる切れ目を探し，
右側を子（生成200＋歩く距離×200）に任せる．枠の取り合いは無視（上限の見積もり）．
仕事の時間は 200*(交換+移動) だけ（行の費用は数えない）．"""
import random, statistics as S
import exact2 as E

C = 200

def cost_alone(a, pos, known=True):
    b = list(a); st = [0, 0, 0]
    E.sort2(b, pos, st, known)
    return C * (st[0] + st[1])

def run_split(a, pos, t0, avail, depth, known=True):
    """a を pos から整列し終える時刻（子に分ければその終わりも含めた最大）"""
    n = len(a); a = list(a); lo = 0; hi = n - 1; t = t0
    d = 1 if pos < hi else -1
    while lo < hi:
        st = [0, 0, 0]
        # 1パスだけ進める：sort2 を1パス版として使う代わりに，ここで同じ手順を書く
        if d > 0:
            if known:
                last = E.fwd_last(a, pos, hi)
                if last < 0: return t
            else:
                last = hi - 1
            known = True
            found = -1
            while True:
                if a[pos] > a[pos + 1]:
                    a[pos], a[pos + 1] = a[pos + 1], a[pos]; t += C; found = pos
                    if pos > lo and a[pos - 1] > a[pos]:
                        a[pos - 1], a[pos] = a[pos], a[pos - 1]; t += C
                if pos >= last: break
                t += C; pos += 1
            if found < 0: return t
            hi = found
        else:
            last = E.bwd_last(a, pos, lo)
            if last < 0: return t
            while True:
                if a[pos] < a[pos - 1]:
                    a[pos], a[pos - 1] = a[pos - 1], a[pos]; t += C
                    if pos < hi and a[pos + 1] < a[pos]:
                        a[pos + 1], a[pos] = a[pos], a[pos + 1]; t += C
                if pos <= last: break
                t += C; pos -= 1
            lo = last
        d = -d
        if lo >= hi: return t
        if t >= avail and depth > 0 and hi - lo >= 6:
            # 切れ目を探す
            pm = [0] * n; sm = [0] * n
            m_ = -1
            for i in range(lo, hi + 1):
                m_ = max(m_, a[i]); pm[i] = m_
            m_ = 99
            for i in range(hi, lo - 1, -1):
                m_ = min(m_, a[i]); sm[i] = m_
            best = None
            rest = cost_alone(a[lo:hi + 1], pos - lo) if lo <= pos <= hi else None
            for m in range(lo + 2, hi):
                if pm[m - 1] <= sm[m]:
                    # 左：自分が pos から [lo,m-1] を整列．右：子が m..hi を整列（始点 m から）
                    L = list(a[lo:m]); R = list(a[m:hi + 1])
                    p = min(max(pos, lo), m - 1) - lo
                    walkL = abs(pos - (lo + p)) * C
                    tl = t + walkL + cost_alone(L, p)
                    tr = t + C + abs(pos - m) * C + cost_alone(R, 0)
                    mk = max(tl, tr)
                    if best is None or mk < best[0]: best = (mk, m)
            base = t + cost_alone(a[lo:hi + 1], min(max(pos, lo), hi) - lo)
            if best is not None and best[0] < base:
                m = best[1]
                p = min(max(pos, lo), m - 1)
                tl = run_split(a[lo:m], p - lo, t + abs(pos - p) * C, avail, depth - 1)
                tr = run_split(a[m:hi + 1], 0, t + C + abs(pos - m) * C, avail, depth - 1)
                return max(tl, tr)
    return t

def trial(seed, avail, depth):
    rng = random.Random(seed)
    grid = [[rng.randrange(10) for y in range(32)] for x in range(32)]
    cols = [sorted(c) for c in grid]
    base = []; spl = []
    for y in range(32):
        row = [cols[x][y] for x in range(32)]
        base.append(cost_alone(row, 0, False))
        spl.append(run_split(row, 0, 0, avail, depth, False))
    return max(base), max(spl), S.mean(base)

if __name__ == "__main__":
    for avail in (0, 15000, 30000):
        for depth in (1, 3):
            r = [trial(s, avail, depth) for s in range(40)]
            b = S.mean(x[0] for x in r); sp = S.mean(x[1] for x in r)
            print("空く時刻 %5d 分割の深さ %d : 最大 %6.0f → %6.0f （%.1f%%）平均 %.0f"
                  % (avail, depth, b, sp, 100 * (sp - b) / b, S.mean(x[2] for x in r)))
