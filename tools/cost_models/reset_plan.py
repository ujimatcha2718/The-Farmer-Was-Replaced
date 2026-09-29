"""最速リセットの大まかな費用モデル（推定）．
盤面 w，機数 D，各段階を決めたとき，骨・金・物質・サボテン・かぼちゃを集める時間（秒）を概算する．
仮定（推定を多く含む）：
  ・Speed 5（3,037.5 tick/秒），Power あり（2倍）で 6,075 tick/秒．動作 200 tick．
  ・整列サボテン：D 機で列→行の整列．1本の線の費用 ≈ (0.6 n² + 3n) 動作（cactus の費用モデルの縮約．推定）．
    植え付け・耕し：マス数×2 動作 ÷ D．成長 1 秒．
  ・合体かぼちゃ：1周期 ≈ 植え付け（マス数×2÷D 動作）＋ 枯れの植え直しの待ち 約 4 回の成長（水1で平均 0.4 秒×…）．
    かぼちゃは実測の 32×32・32機で1周期 約 5.4 万 tick ≒ 9 秒（6,075 tick/秒）．ここでは マス数/D に比例させる．
  ・迷路：宝1個あたり 10 歩（32×32・32機の実測 9〜11）×1機，D 機なら担当が近くなるので 10×sqrt(32/D) 歩（推定）．
  ・恐竜：1回に尾 L のリンゴ．リンゴ1個あたりの移動 ≈ w 歩（推定）．移動の tick は 400×0.97^k（下限 29）．
"""
import math

TPS = 6075.0   # Power あり


def secs(ticks):
    return ticks / TPS


def cactus_harvest(w, D):
    n = w
    line = 0.6 * n * n + 3 * n
    lines_per_drone = math.ceil(n / min(D, n))
    act = 2 * lines_per_drone * line + 2 * n * n / min(D, n) + n
    return secs(act * 200) + 1.0 + 3.0   # 成長1秒＋配布など


def snake(w, L):
    t = 0.0
    for k in range(int(L)):
        cost = max(29.0, 400 * 0.97 ** k)
        t += w * cost
    return secs(t)


def maze(w, D, treasures):
    steps = 10 * math.sqrt(32.0 / D) * (w / 32.0) ** 0.5
    return secs(treasures * (steps * 200 + 400))


def plan(w, D, cactus_lvl, dino_lvl, maze_lvl):
    m = 2 ** (cactus_lvl - 1)
    per = (w * w) ** 2 * m
    # 必要なサボテン：恐竜と迷路の段階の費用＋リンゴ
    dino_cost = [2000, 12000, 72000, 432000, 2590000, 15600000]
    maze_cost = [0, 12000, 72000, 432000, 2590000, 15600000]
    need_c = sum(dino_cost[:dino_lvl]) + sum(maze_cost[:maze_lvl])
    L = math.ceil(math.sqrt(2e6 / 2 ** (dino_lvl - 1)))
    runs = 1
    if L > w * w - 1:
        L = w * w - 1
        runs = math.ceil(2e6 / (L * L * 2 ** (dino_lvl - 1)))
    need_c += runs * L * 2 ** dino_lvl
    n_cac = math.ceil(need_c / per)
    # 物質：金 100万 ÷ w ＋ Mazes 1 の 1000．感染サボテン1回で per/2 × 感染割合 0.8
    sub = 1e6 / w + 1000
    n_inf = math.ceil(sub / (per * 0.8 / 2))
    gold_per = w * w * 2 ** (maze_lvl - 1)
    tre = math.ceil(1e6 / gold_per)
    t_c = (n_cac + n_inf) * cactus_harvest(w, D)
    t_s = runs * snake(w, L)
    t_m = maze(w, D, tre)
    return t_c, t_s, t_m, n_cac, n_inf, runs, L, tre


for w in (12, 16, 22):
    for D in (1, 8, 16, 32):
        best = None
        for cl in range(1, 6):
            for dl in range(1, 7):
                for ml in range(1, 7):
                    r = plan(w, D, cl, dl, ml)
                    tot = r[0] + r[1] + r[2]
                    if best is None or tot < best[0]:
                        best = (tot, cl, dl, ml, r)
        tot, cl, dl, ml, r = best
        print("w=%2d D=%2d  合計 %6.0f 秒  Cactus%d Dino%d Maze%d  サボテン収穫 %d＋感染 %d 回 %5.0f秒  恐竜 %d回×尾%d %5.0f秒  宝 %d 個 %5.0f秒"
              % (w, D, tot, cl, dl, ml, r[3], r[4], r[0], r[5], r[6], r[1], r[7], r[2]))
