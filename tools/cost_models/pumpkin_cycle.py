"""かぼちゃの同期方式の「1周期」だけの費用モデル（後半：全マスが水1）．
1周期 = 収穫から，盤面の全マスが生きて育ち切る（＝次の収穫）まで．各機は1列32マス．
成長：U[1500,23000]/5（水1）．枯れ 0.22．行動 200，調べる CHK tick．
方式
  base : A 端から端へ植える → B 戻りながら調べ，枯れ／空は植え直す → C 未完のマスを往復で回る（現行）
"""
import random, statistics as S

N = 32
CHK = 12
LO, HI, DEATH = 1500 / 5, 23000 / 5, 0.22

def column(rng, mode="base"):
    t = 0.0
    y = 0
    done = [None] * N     # 育ち切る時刻
    die = [False] * N
    def plant(k, t):
        done[k] = t + 200 + rng.uniform(LO, HI); die[k] = rng.random() < DEATH
        return t + 200
    # A
    for k in range(N):
        if k > 0: t += 200
        t += CHK
        t = plant(k, t)
    y = N - 1
    # B
    todo = []
    for k in range(N - 1, -1, -1):
        if k != N - 1: t += 200
        t += CHK
        if t >= done[k]:
            if die[k]:
                t = plant(k, t); todo.append(k)
        else:
            todo.append(k)
    y = 0
    # C
    while todo:
        order = todo if abs(y - todo[0]) <= abs(y - todo[-1]) else todo[::-1]
        nt = []
        for k in order:
            t += 200 * abs(y - k); y = k
            t += CHK
            if t >= done[k]:
                if die[k]:
                    t = plant(k, t); nt.append(k)
            else:
                nt.append(k)
        todo = nt
    # 列の最後のマスが育ち切った時刻（確認した時刻ではなく）と，確認し終えた時刻
    return t, max(done)

def cycle(rng, mode="base"):
    cols = [column(rng, mode) for _ in range(N)]
    # 収穫は全列の確認が済み，全マスが育ち切った後（列0の機体が合図を見てから 200）
    return max(max(c[0] for c in cols), max(c[1] for c in cols)) + 200 + 400   # 400：端へ寄る・合図の見落とし等の目安

if __name__ == "__main__":
    r = [cycle(random.Random(s)) for s in range(200)]
    print("base 1周期 平均 %.0f 標準偏差 %.0f" % (S.mean(r), S.stdev(r)))
    print("下限の目安：植える 32×200 ＋ 移動 62×200 = %d" % (32 * 200 + 62 * 200))
