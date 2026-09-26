"""線1本の並べ替え手順を費用モデルで比べる（move・swap = 200，measure = 1）．

盤面 32x32 の値（0..9 一様）を作り，
  列の段階：各列を植え付け（北へ）→ 整列
  行の段階：列整列後の各行を整列
を手順ごとに数え，段階の最大値（律速する線）と平均を出す．
行数（ソース行）の費用は数えていない（交換・移動だけ）．

手順
  cocktail     現行．戻り歩をそのまま1パス目にする双方向バブル
  plantbub     植え付けの前進中に，植えたマスと1つ南を比べて大きい方を運ぶ
  pull         各歩で後ろ側の隣とも比べ，逆順なら swap(back) する（3マス整列）
"""
import random
import sys

N = 32


def sort_line(a, pos, pull, stats):
    """a を破壊的に昇順にする．pos は開始位置．戻り値：終了位置"""
    n = len(a)
    lo = 0
    hi = n - 1
    while lo < hi:
        if pos < hi:
            last = -1
            for i in range(hi - pos):
                if a[pos] > a[pos + 1]:
                    a[pos], a[pos + 1] = a[pos + 1], a[pos]
                    stats[0] += 1
                    last = pos
                    if pull and pos > lo and a[pos - 1] > a[pos]:
                        a[pos - 1], a[pos] = a[pos], a[pos - 1]
                        stats[0] += 1
                stats[1] += 1
                pos += 1
            if last < 0:
                return pos
            hi = last
        if lo < hi and pos > lo:
            last = -1
            for i in range(pos - lo):
                if a[pos] < a[pos - 1]:
                    a[pos], a[pos - 1] = a[pos - 1], a[pos]
                    stats[0] += 1
                    last = pos
                    if pull and pos < hi and a[pos + 1] < a[pos]:
                        a[pos + 1], a[pos] = a[pos], a[pos + 1]
                        stats[0] += 1
                stats[1] += 1
                pos -= 1
            if last < 0:
                return pos
            lo = last
    return pos


def column(vals, plantbub, pull, stats):
    a = list(vals)
    n = len(a)
    if plantbub:
        # 植えながら北へ：y を植えたら y-1 と比べ，南の方が大きければ swap(South)
        last = -1
        for y in range(1, n):
            if a[y - 1] > a[y]:
                a[y - 1], a[y] = a[y], a[y - 1]
                stats[0] += 1
                last = y - 1
        # 前進1パスを済ませたのと同じ．hi を詰めた状態から後ろ向きに始める
        hi = last
        return a, sort_from(a, n - 1, hi, pull, stats)
    return a, sort_line(a, n - 1, pull, stats)


def sort_from(a, pos, hi0, pull, stats):
    n = len(a)
    if hi0 <= 0:
        return pos
    lo = 0
    hi = hi0
    # pos > hi：後ろ向きのパスを pos から始める（hi より奥は交換が起きない）
    first = True
    while lo < hi:
        if pos < hi and not first:
            last = -1
            for i in range(hi - pos):
                if a[pos] > a[pos + 1]:
                    a[pos], a[pos + 1] = a[pos + 1], a[pos]
                    stats[0] += 1
                    last = pos
                    if pull and pos > lo and a[pos - 1] > a[pos]:
                        a[pos - 1], a[pos] = a[pos], a[pos - 1]
                        stats[0] += 1
                stats[1] += 1
                pos += 1
            if last < 0:
                return pos
            hi = last
        first = False
        if lo < hi and pos > lo:
            last = -1
            for i in range(pos - lo):
                if a[pos] < a[pos - 1]:
                    a[pos], a[pos - 1] = a[pos - 1], a[pos]
                    stats[0] += 1
                    last = pos
                    if pull and pos < hi and a[pos + 1] < a[pos]:
                        a[pos + 1], a[pos] = a[pos], a[pos + 1]
                        stats[0] += 1
                stats[1] += 1
                pos -= 1
            if last < 0:
                return pos
            lo = last
    return pos


def trial(seed, plantbub, pull):
    rng = random.Random(seed)
    grid = [[rng.randrange(10) for y in range(N)] for x in range(N)]
    ct = []
    cols = []
    for x in range(N):
        st = [0, 0]
        a, p = column(grid[x], plantbub, pull, st)
        cols.append(a)
        ct.append(st)
    rt = []
    for y in range(N):
        st = [0, 0]
        row = [cols[x][y] for x in range(N)]
        sort_line(row, 0, pull, st)
        assert row == sorted(row)
        rt.append(st)
    return ct, rt


def summary(name, plantbub, pull, S=200):
    cmax = rmax = 0
    csw = cmv = rsw = rmv = 0
    for s in range(S):
        ct, rt = trial(s, plantbub, pull)
        cmax += max(200 * (a + b) for a, b in ct)
        rmax += max(200 * (a + b) for a, b in rt)
        csw += sum(a for a, b in ct) / N
        cmv += sum(b for a, b in ct) / N
        rsw += sum(a for a, b in rt) / N
        rmv += sum(b for a, b in rt) / N
    print("%-22s 列: 交換%6.1f 移動%6.1f 最大%8.0f | 行: 交換%6.1f 移動%6.1f 最大%8.0f | 計 %8.0f"
          % (name, csw / S, cmv / S, cmax / S, rsw / S, rmv / S, rmax / S, (cmax + rmax) / S))


if __name__ == "__main__":
    summary("cocktail", False, False)
    summary("plantbub", True, False)
    summary("pull", False, True)
    summary("plantbub+pull", True, True)
