import random
from strat_lib import cocktail_cost, N
M=[3]*10; M[0]+=1; M[9]+=1
T=[]
for v in range(10): T+=[v]*M[v]
def column(rng, mode, a, b):
    R=list(M); vals=[]; t=0
    for y in range(N):
        t += 201
        while True:
            t += 201; v=rng.randrange(10)
            if R[v]>0:
                if mode=="fix":
                    lo=T[y]-a; hi=T[y]+b
                else:
                    m=min(u for u in range(10) if R[u]>0); lo=m; hi=m+b
                ok = lo<=v<=hi
                if not ok and not any(R[u]>0 and lo<=u<=hi for u in range(10)): ok=True
                if ok: break
            t += 200
        vals.append(v); R[v]-=1
        if y<N-1: t+=200
    return t + cocktail_cost(vals, N-1)
def ev(mode,a,b,S=60):
    res=[]
    for sd in range(S):
        rng=random.Random(sd)
        res.append(max(column(rng,mode,a,b) for _ in range(N)))
    return sum(res)//len(res)
