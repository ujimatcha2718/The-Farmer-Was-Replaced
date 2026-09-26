"""行の段階：空いた枠を使って重い行を「小／大の半分に分けて2機で整列」する案を，
枠の取り合いを含めて見積もる（仕事の時間は 200*(交換+移動)，判断の行の費用は数えない）．
各行はパスの終わりごとに，枠が空いていて，残りの予測（そのまま続けた場合の終了時刻）が
しきい値 TH を超えていれば分割する．分割した子も同じ規則で再分割できる（深さ制限あり）．
枠：32機．行0..31 の担当が時刻0に一斉に始める．"""
import heapq, random, statistics as S
import exact2 as E
from partition_model import sort_with_labels
C = 200

def one_pass(a, pos, lo, hi, d, known):
    """1パス進める．戻り値 (pos, lo, hi, 所要, 終了したか)"""
    t = 0
    if d > 0:
        if known:
            last = E.fwd_last(a, pos, hi)
            if last < 0: return pos, lo, hi, t, True
        else:
            last = hi - 1
        found = -1
        while True:
            if a[pos] > a[pos + 1]:
                a[pos], a[pos + 1] = a[pos + 1], a[pos]; t += C; found = pos
                if pos > lo and a[pos - 1] > a[pos]:
                    a[pos - 1], a[pos] = a[pos], a[pos - 1]; t += C
            if pos >= last: break
            t += C; pos += 1
        if found < 0: return pos, lo, hi, t, True
        hi = found
    else:
        last = E.bwd_last(a, pos, lo)
        if last < 0: return pos, lo, hi, t, True
        while True:
            if a[pos] < a[pos - 1]:
                a[pos], a[pos - 1] = a[pos - 1], a[pos]; t += C
                if pos < hi and a[pos + 1] < a[pos]:
                    a[pos + 1], a[pos] = a[pos], a[pos + 1]; t += C
            if pos <= last: break
            t += C; pos -= 1
        lo = last
    return pos, lo, hi, t, lo >= hi

def rest_cost(a, pos, lo, hi):
    b = list(a[lo:hi + 1]); st = [0, 0, 0]
    E.sort2(b, min(max(pos, lo), hi) - lo, st)
    return C * (st[0] + st[1]) + C * max(0, lo - pos, pos - hi)

def simulate(rows, TH, depth, maxd=32):
    # 各タスク：dict(a, pos, lo, hi, d, known, t, depth)
    ev = []  # (時刻, 連番, タスク)
    k = 0
    for r in rows:
        heapq.heappush(ev, (0, k, dict(a=list(r), pos=0, lo=0, hi=len(r) - 1, d=1, known=False, dep=depth))); k += 1
    alive = len(rows); end = 0
    while ev:
        t, _, T = heapq.heappop(ev)
        a = T['a']
        pos, lo, hi, dt, done = one_pass(a, T['pos'], T['lo'], T['hi'], T['d'], T['known'])
        t += dt
        T.update(pos=pos, lo=lo, hi=hi, d=-T['d'], known=True)
        if done:
            alive -= 1; end = max(end, t); continue
        if alive < maxd and T['dep'] > 0 and hi - lo >= 8 and t + rest_cost(a, pos, lo, hi) > TH:
            seg = a[lo:hi + 1]; n = len(seg)
            order = sorted(range(n), key=lambda i: (seg[i], i))
            lab = [0] * n
            for i in order[n // 2:]: lab[i] = 1
            st = [0, 0, 0]
            p0 = min(max(pos, lo), hi) - lo
            t += C * max(0, lo - pos, pos - hi)
            seg2, p2 = sort_with_labels(seg, lab, p0, st)
            t += C * (st[0] + st[1])
            m = n // 2
            a[lo:hi + 1] = seg2
            # 自分：左 [lo, lo+m-1]，子：右 [lo+m, hi]（生成200＋歩く）
            pl = min(p2, m - 1)
            L = dict(a=a[lo:lo + m], pos=pl, lo=0, hi=m - 1, d=(1 if pl < m - 1 else -1), known=True, dep=T['dep'] - 1)
            R = dict(a=a[lo + m:hi + 1], pos=0, lo=0, hi=n - m - 1, d=1, known=True, dep=T['dep'] - 1)
            alive += 1
            heapq.heappush(ev, (t + abs(p2 - pl) * C, k, L)); k += 1
            heapq.heappush(ev, (t + C + abs(p2 - m) * C, k, R)); k += 1
            continue
        heapq.heappush(ev, (t, k, T)); k += 1
    return end

def rows_of(seed):
    rng = random.Random(seed)
    grid = [[rng.randrange(10) for y in range(32)] for x in range(32)]
    cols = [sorted(c) for c in grid]
    return [[cols[x][y] for x in range(32)] for y in range(32)]

if __name__ == "__main__":
    S_ = 40
    base = [simulate(rows_of(s), 10**9, 0) for s in range(S_)]
    print("分割なし 最大 %.0f" % S.mean(base))
    for TH in (50000, 60000, 65000, 70000):
        for dep in (1, 2):
            r = [simulate(rows_of(s), TH, dep) for s in range(S_)]
            d = [x - y for x, y in zip(r, base)]
            print("TH %5d 深さ %d : %.0f （差 %.0f，標準誤差 %.0f）" % (TH, dep, S.mean(r), S.mean(d), S.stdev(d) / S_ ** .5))
