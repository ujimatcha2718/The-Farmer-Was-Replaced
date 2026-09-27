"""かぼちゃの費用モデル その2：区画ごとに「植える → 育っていない・枯れたマスだけを回る → そろったら収穫」．

実測に合わせた仕様（CLAUDE.md 5b 節）
  ・成長時間：水なしで一様分布 [1500, 23000] tick，水の量 w で 1/(1+4w) 倍
  ・育ち切った時点で確率 0.22 で枯れる
  ・区画の全マスが生きて育ち切ると1つにまとまる（枯れたマスがあると小さな塊にしかならない：merge probe）
  ・水：1タンク／237 tick で溜まる．1タンクで +0.25（上限1）．植えても水はほとんど減らない（water probe）ので減りは無視
  ・行動 200 tick，調べる LINE_CHECK tick
方式
  B×B の区画を k 機で受け持つ（区画を k 本の帯に分ける）．各機は
   1. 自分の帯を往復しながら，空いたマスに（水を目標まで入れて）植える
   2. 自分の帯で「育ち切った」と確かめていないマスのうち一番近いものへ行き，
      育っていれば待ち，枯れていれば植え直す．帯の全マスが育ち切るまで繰り返す
   3. 区画の全マスが育ち切ったら（相棒の帯も），どちらかが収穫する．1 に戻る
"""
import heapq, random

TICK = 200
LINE_CHECK = 15
GROW_LO, GROW_HI = 1500, 23000
DEATH = 0.22
TANK_EVERY = 237
TARGET = 200000000
N = 32

def per_cell(n):
    return (n if n <= 5 else 6) * 512

def run(B, k, water_target, seed, spread=True, max_t=30_000_000):
    rng = random.Random(seed)
    nb = N // B
    st = {}
    for x in range(N):
        for y in range(N):
            st[(x, y)] = {'s': None, 'done': 0, 'die': False, 'w': 0.0, 'till': False}
    used = [0]
    gold = [0]
    harvests = [0]
    def tanks(t):
        return int(t // TANK_EVERY) - used[0]
    def settle(c, t):
        s = st[c]
        if s['s'] == 'g' and t >= s['done']:
            s['s'] = 'dead' if s['die'] else 'ok'
    drones = []
    for bx in range(nb):
        for by in range(nb):
            w = B // k
            for j in range(k):
                x0 = bx * B + j * w
                cells = []
                for ci, x in enumerate(range(x0, x0 + w)):
                    ys = list(range(by * B, by * B + B))
                    if ci % 2: ys.reverse()
                    for y in ys: cells.append((x, y))
                block = [(x, y) for x in range(bx * B, bx * B + B) for y in range(by * B, by * B + B)]
                drones.append({'cells': cells, 'block': block, 'pos': cells[0], 'phase': 'plant', 'i': 0, 'gen': 0})
    blockgen = {}
    q = []
    for d_i, d in enumerate(drones):
        # 配布の時間（目安）：遠い順に生成＋歩く．最大 3,600 程度（サボテンと同じ配り方）
        heapq.heappush(q, (min(3600, 200 * (d_i % 16) + 200 * (d_i // 16)), d_i))
    def dist(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    while q:
        t, d_i = heapq.heappop(q)
        if gold[0] >= TARGET:
            return t, harvests[0], used[0]
        if t > max_t:
            return None, harvests[0], used[0]
        d = drones[d_i]
        bid = d['block'][0]
        # 相棒が収穫したら（区画の世代が進んだら）植え直しから
        if blockgen.get(bid, 0) != d['gen']:
            d['gen'] = blockgen.get(bid, 0); d['phase'] = 'plant'; d['i'] = 0
        dt = LINE_CHECK
        if d['phase'] == 'plant':
            c = d['cells'][d['i']]
            dt += TICK * dist(d['pos'], c); d['pos'] = c
            s = st[c]; settle(c, t)
            if s['s'] is None or s['s'] == 'dead':
                if not s['till']:
                    s['till'] = True; dt += TICK
                while s['w'] < water_target - 1e-9 and tanks(t + dt) >= 1:
                    used[0] += 1; s['w'] = min(1.0, s['w'] + 0.25); dt += TICK
                s['s'] = 'g'; s['done'] = t + dt + TICK + rng.uniform(GROW_LO, GROW_HI) / (1 + 4 * s['w'])
                s['die'] = rng.random() < DEATH
                dt += TICK
            d['i'] += 1
            if d['i'] >= len(d['cells']):
                d['phase'] = 'tend'
        elif d['phase'] == 'tend':
            todo = []
            for c in d['cells']:
                settle(c, t)
                if st[c]['s'] != 'ok':
                    todo.append(c)
            if not todo:
                d['phase'] = 'wait'
            else:
                c = min(todo, key=lambda z: (dist(d['pos'], z), st[z]['done']))
                dt += TICK * dist(d['pos'], c); d['pos'] = c
                s = st[c]; settle(c, t + dt)
                if s['s'] == 'g':
                    dt = max(dt, s['done'] - t) + LINE_CHECK   # そこで育つのを待つ
                    settle(c, t + dt)
                if s['s'] == 'dead' or s['s'] is None:
                    while s['w'] < water_target - 1e-9 and tanks(t + dt) >= 1:
                        used[0] += 1; s['w'] = min(1.0, s['w'] + 0.25); dt += TICK
                    s['s'] = 'g'; s['done'] = t + dt + TICK + rng.uniform(GROW_LO, GROW_HI) / (1 + 4 * s['w'])
                    s['die'] = rng.random() < DEATH
                    dt += TICK
        else:  # wait：区画全体がそろうのを待つ
            ok = True
            for c in d['block']:
                settle(c, t)
                if st[c]['s'] != 'ok':
                    ok = False; break
            if ok:
                gold[0] += per_cell(B) * B * B
                harvests[0] += 1
                for c in d['block']:
                    st[c]['s'] = None
                blockgen[bid] = blockgen.get(bid, 0) + 1
                d['gen'] = blockgen[bid]; d['phase'] = 'plant'; d['i'] = 0
                dt += TICK
            else:
                dt += 100
        heapq.heappush(q, (t + dt, d_i))
    return None, harvests[0], used[0]

if __name__ == "__main__":
    for (B, k) in [(32, 32), (16, 8), (8, 2), (8, 1), (4, 1)]:
        if B // k < 1: continue
        for wt in (0.0, 0.5, 1.0):
            r = [run(B, k, wt, s) for s in range(3)]
            print("区画 %2dx%-2d 1区画%2d機 水の目標 %.1f : 時間 %s 収穫 %s 水 %s" % (B, B, k, wt, [x[0] and int(x[0]) for x in r], [x[1] for x in r], [x[2] for x in r]), flush=True)
