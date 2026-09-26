# 大きさは「育ち切った収穫」でしか作り直されない，という実測に基づく見積もり
# 列ごとに：北へ植える → 上下に往復しながら「隣と比べて交換」＋「余っている値で
# 育ち切ったものは収穫して植え直す」→ 整列かつ値の組が一致したら終わり
import random
N=32; G=5877
M=[3]*10; M[0]+=1; M[9]+=1
def col(rng, use_rr, cap_passes=10**9):
    val=[0]*N; pt=[0]*N; t=0
    for y in range(N):
        t+=201+201; val[y]=rng.randrange(10); pt[y]=t
        if y<N-1: t+=200
    cnt=[0]*10
    for v in val: cnt[v]+=1
    pos=N-1; d=-1; passes=0
    while True:
        sw=0; rr=0
        steps=N-1
        for i in range(steps):
            # 植え直し判定
            if use_rr and passes<cap_passes and cnt[val[pos]]>M[val[pos]] and t-pt[pos]>=G:
                cnt[val[pos]]-=1; t+=400; v=rng.randrange(10); val[pos]=v; pt[pos]=t; cnt[v]+=1; rr+=1
            t+=1
            q=pos+d
            if (d>0 and val[pos]>val[q]) or (d<0 and val[pos]<val[q]):
                val[pos],val[q]=val[q],val[pos]; pt[pos],pt[q]=pt[q],pt[pos]; t+=200; sw+=1
            t+=200; pos=q
        # 端のマスも判定
        if use_rr and passes<cap_passes and cnt[val[pos]]>M[val[pos]] and t-pt[pos]>=G:
            cnt[val[pos]]-=1; t+=400; v=rng.randrange(10); val[pos]=v; pt[pos]=t; cnt[v]+=1; rr+=1
        passes+=1; d=-d
        ok=(cnt==M) or not use_rr or passes>=cap_passes
        if sw==0 and rr==0 and ok: break
    exact = cnt==M
    t=max(t, max(pt)+G)
    return t, exact, val
def run(seed, use_rr, cap=10**9):
    rng=random.Random(seed)
    res=[col(rng,use_rr,cap) for _ in range(N)]
    tcol=max(r[0] for r in res)
    exact=all(r[1] for r in res)
    return tcol+6400, exact
