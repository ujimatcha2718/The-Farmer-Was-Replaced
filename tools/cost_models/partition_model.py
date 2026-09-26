"""行の段階で，1パス目のあと「小さい半分／大きい半分」に分け（ラベル0/1の整列），
左右を自分と子で並行して整列する案の上限見積もり（枠は時刻 AVAIL 以降いつでも空くと仮定）．
分けるときの交換はラベルが逆順の組だけなので，同じラベルどうしの順は保たれる．"""
import random, statistics as S
import exact2 as E
C = 200

def sort_with_labels(vals, lab, pos, st):
    """lab（0/1）を sort2 と同じ手順で整列し，vals も同じ置換で動かす．"""
    pairs = [(l, i) for i, l in enumerate(lab)]
    # 同じ手順を lab で実行し，置換を追う：lab に添字を持たせたキーで比較
    key = [l * 1000 + 0 for l in lab]
    idx = list(range(len(lab)))
    # sort2 は値だけを見るので，(ラベル) だけの列を整列しつつ添字も同時に動かす
    a = [(l, j) for j, l in enumerate(lab)]
    class K(tuple):
        def __gt__(s, o): return s[0] > o[0]
        def __lt__(s, o): return s[0] < o[0]
    a = [K(x) for x in a]
    p = E.sort2(a, pos, st)
    return [vals[x[1]] for x in a], p

def trial(seed, avail):
    rng = random.Random(seed)
    grid = [[rng.randrange(10) for y in range(32)] for x in range(32)]
    cols = [sorted(c) for c in grid]
    base = []; part = []
    for y in range(32):
        row = [cols[x][y] for x in range(32)]
        st = [0, 0, 0]; b = list(row); E.sort2(b, 0, st, known=False)
        tb = C * (st[0] + st[1]); base.append(tb)
        # 1パス目（未知）だけ行う：sort2 の1パス目と同じ費用を別に数える
        n = len(row); a = list(row); t = 0; pos = 0
        for p in range(n - 1):
            if a[p] > a[p + 1]:
                a[p], a[p + 1] = a[p + 1], a[p]; t += C
                if p > 0 and a[p - 1] > a[p]:
                    a[p - 1], a[p] = a[p], a[p - 1]; t += C
            if p < n - 2: t += C
        pos = n - 2
        t = max(t, avail)
        order = sorted(range(n), key=lambda i: (a[i], i))
        lab = [0] * n
        for i in order[n // 2:]: lab[i] = 1
        st = [0, 0, 0]
        a2, p2 = sort_with_labels(a, lab, pos, st)
        t += C * (st[0] + st[1])
        m = n // 2
        L = a2[:m]; R = a2[m:]
        stl = [0, 0, 0]; pl = min(p2, m - 1); E.sort2(L, pl, stl)
        tl = t + abs(p2 - pl) * C + C * (stl[0] + stl[1])
        str_ = [0, 0, 0]; E.sort2(R, 0, str_)
        tr = t + C + abs(p2 - m) * C + C * (str_[0] + str_[1])
        part.append(min(tb, max(tl, tr)))
    return max(base), max(part)

for avail in (0, 15000, 30000):
    r = [trial(s, avail) for s in range(40)]
    b = S.mean(x[0] for x in r); p = S.mean(x[1] for x in r)
    print("空く時刻 %5d : 最大 %6.0f → %6.0f （%.1f%%）" % (avail, b, p, 100 * (p - b) / b))
