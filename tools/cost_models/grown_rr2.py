import random
from grown_rr import col, N
from strat_lib import cocktail_cost
def run(seed, cap):
    rng=random.Random(seed)
    res=[col(rng,cap>0,cap) for _ in range(N)]
    tcol=max(r[0] for r in res)+6400
    cols=[sorted(r[2]) for r in res]
    rows=max(cocktail_cost([cols[x][y] for x in range(N)],0) for y in range(N))+6400
    return tcol, rows
for cap in [0,2,4,6,10]:
    a=[run(s,cap) for s in range(12)]
    c=sum(x[0] for x in a)/12; r=sum(x[1] for x in a)/12
    print("植え直し往復=%2d 列=%d 行=%d 計=%d"%(cap,c,r,c+r),flush=True)
