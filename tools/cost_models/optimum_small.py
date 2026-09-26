"""小さな線で，最適な手順（移動・交換とも費用1，幅優先探索）と exact2 の手順を比べる．
引数: n 値の種類数 試行回数（例: 8 10 30）"""
import random, sys
from collections import deque
import contextlib, io
with contextlib.redirect_stdout(io.StringIO()):
    import exact2 as E

def opt(a, pos):
    tgt = tuple(sorted(a)); n = len(a)
    s0 = (tuple(a), pos)
    dist = {s0: 0}; q = deque([s0])
    while q:
        s = q.popleft(); arr, p = s; d = dist[s]
        if arr == tgt: return d
        nb = []
        if p > 0: nb.append((arr, p - 1))
        if p < n - 1: nb.append((arr, p + 1))
        for j in (p - 1, p + 1):
            if 0 <= j < n and arr[j] != arr[p]:
                l = list(arr); l[j], l[p] = l[p], l[j]; nb.append((tuple(l), p))
        for t in nb:
            if t not in dist:
                dist[t] = d + 1; q.append(t)

n = int(sys.argv[1]); K = int(sys.argv[2]); T = int(sys.argv[3])
rng = random.Random(1)
so = sh = 0
for t in range(T):
    a = [rng.randrange(K) for _ in range(n)]
    st = [0, 0]; b = list(a); st=[0,0,0]; E.sort2(b, 0, st)
    o = opt(a, 0); so += o; sh += st[0] + st[1]
print("n=%d K=%d 最適 %.2f  exact2 %.2f  比 %.3f" % (n, K, so / T, sh / T, sh / so))
