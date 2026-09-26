import sys
M_FLOOR = 22      # 実測2点から推定した move の下限 tick
K_LINE = 1.81     # 同じく 1 行あたりの tick

def predict(path):
    lines = other = 0
    hist = {}
    for ln in open(path):
        p = ln.split()
        if p[0] == "lines": lines = int(p[1])
        elif p[0] == "other": other = int(p[1])
        else: hist[int(p[1])] = int(p[2])
    tbl = []; c = 400
    for _ in range(max(hist) + 2):
        tbl.append(c); c = int(c * 0.97)
        if c < M_FLOOR: c = M_FLOOR
    mt = sum(tbl[e] * n for e, n in hist.items())
    mv = sum(hist.values())
    return mv, lines, mt + other + K_LINE * lines

for p in sys.argv[1:]:
    mv, ln, t = predict(p)
    print("%-16s 歩数=%7d  行数=%9d  校正後の予測= %9.0f tick" % (p.split("_")[-1], mv, ln, t))
