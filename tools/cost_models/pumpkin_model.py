"""かぼちゃのリーダーボードの費用モデル（ドローンの行動単位の事象シミュレーション）．

実測に合わせた仕様（CLAUDE.md 5b 節）
  ・成長時間：水なしで一様分布 [1500, 23000] tick．水の量 w のとき 1/(1+4w) 倍（wiki の「w=1 で5倍」．実測は約5.3倍）
  ・育ち切った時点で確率 0.22 で枯れる．枯れたマスは植え直すまで何も生まない
  ・n×n の区画が全マス育ち切るとまとまり，収穫で 1マスあたり min(n,6)×512 個（n≤5 は n 個/マス）
  ・水：1タンク／237 tick で溜まる．1タンクで地面の水 +0.25（上限1）．減りは無視（実測で 1,000 tick に約0.2%）
  ・行動：move・plant・till・harvest・use_item は 200 tick．調べる（get_*，measure）は 1 tick＋行の費用 LINE_CHECK
方式：32機がそれぞれ1列を受け持って往復し，植える・枯れを植え直す・水をやる．
  盤面は B×B の区画に分け，区画の全マスが育ち切ったら，その区画にいる機体が収穫する．
区画どうしの合体（隣の区画も同時に育ち切っていると大きな正方形にまとまる）は無視する．
"""
import heapq, random, sys

TICK_ACT = 200
LINE_CHECK = 15          # 1マス調べる行の費用（推定）
GROW_LO, GROW_HI = 1500, 23000
DEATH = 0.22
TANK_EVERY = 237
TARGET = 200000000
N = 32

def per_cell(n):
    return (n if n <= 5 else 6) * 512

def run(B, water_target, seed, max_t=20_000_000, drones=32, first_tanks=0):
    """32機がそれぞれ1列（32マス）を受け持ち，列の中を往復する．盤面は B×B の区画に分かれ，
    区画の全マスが育ち切ったら，その区画のマスにいる機体が収穫する（区画の判定は神の目．判定の手間は LINE_CHECK に含む）"""
    rng = random.Random(seed)
    def blk(c):
        return (c[0] // B, c[1] // B)
    cells_of = {}
    for x in range(N):
        for y in range(N):
            cells_of.setdefault(blk((x, y)), []).append((x, y))
    state = {}
    water = {}
    tilled = set()
    for x in range(N):
        for y in range(N):
            state[(x, y)] = [None, 0, False]; water[(x, y)] = 0.0
    gold = [0]
    used = [0]
    def tanks_avail(t):
        return first_tanks + int(t // TANK_EVERY) - used[0]
    def settle(c, t):
        s = state[c]
        if s[0] == 'g' and t >= s[1]:
            s[0] = 'dead' if s[2] else 'ok'
    def block_ready(b, t):
        for c in cells_of[b]:
            settle(c, t)
            if state[c][0] != 'ok': return False
        return True
    q = []
    for i in range(drones):
        # 配布：回り込みで最も遠い列まで16歩，生成は2機で並行（サボテンと同じ）として約 3,600
        heapq.heappush(q, (200 * min(i, N - i) + 200 * (i % 16), i, 0, 1))
    harvests = 0
    while q:
        t, i, y, dy = heapq.heappop(q)
        if gold[0] >= TARGET or t > max_t:
            return t, harvests
        c = (i, y)
        settle(c, t)
        dt = LINE_CHECK
        s = state[c]
        b = blk(c)
        if s[0] == 'ok' and block_ready(b, t):
            gold[0] += per_cell(B) * B * B
            harvests += 1
            for cc in cells_of[b]:
                state[cc] = [None, 0, False]
            dt += TICK_ACT
            s = state[c]
        if s[0] is None or s[0] == 'dead':
            if c not in tilled:
                tilled.add(c); dt += TICK_ACT
            while water[c] < water_target - 1e-9 and tanks_avail(t + dt) >= 1:
                used[0] += 1; water[c] = min(1.0, water[c] + 0.25); dt += TICK_ACT
            g = rng.uniform(GROW_LO, GROW_HI) / (1 + 4 * water[c])
            state[c] = ['g', t + dt + TICK_ACT + g, rng.random() < DEATH]
            dt += TICK_ACT
        ny = y + dy
        if ny < 0 or ny >= N:
            dy = -dy; ny = y + dy
        dt += TICK_ACT
        heapq.heappush(q, (t + dt, i, ny, dy))
    return None, harvests


if __name__ == "__main__":
    for B in (32, 16, 8, 4, 2):
        for wt in (0.0, 0.25, 0.5, 1.0):
            r = [run(B, wt, sd) for sd in range(3)]
            print("区画 %2dx%-2d 水の目標 %.2f : 時間 %s 収穫回数 %s" % (B, B, wt, [x[0] for x in r], [x[1] for x in r]), flush=True)
