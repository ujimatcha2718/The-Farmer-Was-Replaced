"""同期方式の1周期（後半：全マス水1）で，「自分の列が済んだ機体が隣の列（東）を往復して枯れを植え直す」
手伝いの効果を見る．周期の終わり＝盤面の全マスが生きて育ち切った時刻（合体して収穫できる時刻）．
行動は時刻順に1つずつ進める（各機の次の行動時刻の小さい順）．"""
import heapq, random, statistics as S

N = 32
CHK = 12
LO, HI, DEATH = 1500 / 5, 23000 / 5, 0.22

def cycle(seed, help_on):
    rng = random.Random(seed)
    done = {}; die = {}
    def plant(c, t):
        done[c] = t + 200 + rng.uniform(LO, HI); die[c] = rng.random() < DEATH
    def status(c, t):
        if c not in done: return 'empty'
        if t < done[c]: return 'grow'
        return 'dead' if die[c] else 'ok'
    # 各機の状態：段階 A/B/C/H，位置 y，列 x，todo
    dr = []
    for x in range(N):
        dr.append({'x': x, 'cx': x, 'y': 0, 'ph': 'A', 'k': 0, 'todo': [], 'dir': 1})
    q = [(0.0, x) for x in range(N)]
    heapq.heapify(q)
    def all_ok(t):
        for x in range(N):
            for y in range(N):
                if status((x, y), t) != 'ok': return False
        return True
    last_check = 0
    while q:
        t, i = heapq.heappop(q)
        # 全部そろったか（重いので時々）
        if t - last_check > 300:
            last_check = t
            if all_ok(t):
                return t
        d = dr[i]
        dt = CHK
        if d['ph'] == 'A':
            c = (d['x'], d['y'])
            plant(c, t); dt += 200
            if d['y'] < N - 1:
                d['y'] += 1; dt += 200
            else:
                d['ph'] = 'B'
        elif d['ph'] == 'B':
            c = (d['x'], d['y'])
            s = status(c, t)
            if s == 'dead':
                plant(c, t); dt += 200; d['todo'].append(d['y'])
            elif s == 'grow':
                d['todo'].append(d['y'])
            if d['y'] > 0:
                d['y'] -= 1; dt += 200
            else:
                d['ph'] = 'C'
                d['todo'].reverse()
        elif d['ph'] == 'C':
            if not d['todo']:
                if help_on and i != 0:
                    d['ph'] = 'H'; d['cx'] = (d['x'] + 1) % N; dt += 200   # 東の列へ1歩
                else:
                    d['ph'] = 'W'
            else:
                k = min(d['todo'], key=lambda z: abs(z - d['y']))
                dt += 200 * abs(k - d['y']); d['y'] = k
                c = (d['x'], k)
                s = status(c, t + dt)
                if s == 'ok':
                    d['todo'].remove(k)
                elif s == 'dead':
                    plant(c, t + dt); dt += 200
        elif d['ph'] == 'H':
            c = (d['cx'], d['y'])
            s = status(c, t)
            if s == 'dead' or s == 'empty':
                plant(c, t); dt += 200
            ny = d['y'] + d['dir']
            if ny < 0 or ny >= N:
                d['dir'] = -d['dir']; ny = d['y'] + d['dir']
            d['y'] = ny; dt += 200
        else:
            dt = 300
        heapq.heappush(q, (t + dt, i))

if __name__ == "__main__":
    for h in (False, True):
        r = [cycle(s, h) for s in range(60)]
        print("手伝い %-5s 1周期 平均 %.0f 標準偏差 %.0f" % (h, S.mean(r), S.stdev(r)))
