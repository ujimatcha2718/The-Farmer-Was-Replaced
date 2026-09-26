# ============================================================
#  The Farmer Was Replaced  スネーク（恐竜の帽子）自動攻略コード
#  （Leaderboards.Dinosaur：33488928 骨を最速で集める）
#
#  前の版は盤面の端で反対側へ回り込めることを前提にしていた．実機では
#  回り込めず，北へ飛ぶ近道で最上行まで進んだところで詰まっていた．
#  この版は**端の回り込みを一切使わない**．
#
#  経路：折り返し経路（n が偶数．32×32 のリーダーボードはこちら）
#    列 x=0 を帰り道として残し，全マスを1度ずつ通って出発点に戻る
#      (0,0) →East→ (n-1,0) →North→ 行1を西へ→ 行2を東へ→ …
#      → 行 n-1 の終わり(1,n-1) →West→ (0,n-1) →South→ (0,0)
#    マス (x,y) のこの経路上の順番は
#      y=0      : ord = x
#      x=0(y≥1) : ord = n*n - y
#      それ以外 : b = n + (y-1)*(n-1) として
#                 y が奇数 → ord = b + (n-1-x)，  偶数 → ord = b + (x-1)
#    この式が全単射であること，経路が盤面から出ないこと，閉じていることは
#    n = 4,6,8,10,16,32 で確認済み．
#
#  近道：北へ1マス動くと，経路上では
#      y が奇数 → 2x-1 個先，  y が偶数 → 2n-1-2x 個先
#    へ飛ぶ（行の残りを飛ばすことに相当）．前進量が 1 のときは近道ではなく
#    経路どおりの1手である．体は常に「尾から頭まで」の経路上の区間に収まる
#    ので，前進量が頭から尾までの距離より小さければ行き先は必ず空いている．
#
#  段取り
#    前半：体が短いあいだは北への近道でリンゴへ急ぐ（move が 400 tick と高い）
#    中間：経路どおりに進んで (0,0) へ戻す．飛ばしたマスを尾が通り過ぎるので
#          体が経路上の連続した区間に戻り，以後は詰まらない
#    後半：1周ずつ回る．1歩あたりの処理を最小にする
#
#  実行方法（別のコードウィンドウから）:
#   leaderboard_run(Leaderboards.Dinosaur, "snake", 256)
#   ※ "snake" はこのコードウィンドウの名前に合わせる
#
#  ゲーム内言語の制約に合わせて，クラス・ラムダ・内包表記・三項演算子・
#  名前付き引数・int()・continue は使っていない
# ============================================================

TARGET_BONES = 33488928  # 「開始時の所持骨＋この数」まで集めたら終了
CUT_LEN = 240            # 体がこの長さになるまで近道を使う（以降は周回のみ）
#   実機の tick 実測3点（120→6.32M, 240→5.78M, 360→6.12M）から校正した値．
#   move() のコストは 1 まで下がらず約 22 tick で下限に達し，ソース1行あたり
#   約 1.79 tick かかる．つまり「1歩 ≒ 12.3行」であり，近道を1歩ぶん延ばす
#   のに 12.3 行より多く計算を使うと損になる．実測の限界交換比は
#   180→240 が 6.4 行/歩，240→360 が 16.9 行/歩なので 240 前後が最適である
SAFE_MARGIN = 2          # 近道の安全余裕．尾の管理が1手ずれても耐えるため
CLEAR_FARM = True        # 走行前に農地を空にする（作物があるとリンゴの場所が減る）
DEBUG = False            # True にすると1回ごとの結果を出力ページに書き出す


# ------------------------------------------------------------
# 出発点 (0,0) へ移動する（帽子をかぶる前に呼ぶ．尾は無い）
# ------------------------------------------------------------
def goto_origin():
	while get_pos_x() > 0:
		if not move(West):
			return
	while get_pos_y() > 0:
		if not move(South):
			return


# ------------------------------------------------------------
# 折り返し経路上の順番
# ------------------------------------------------------------
def ordv(x, y, n):
	if y == 0:
		return x
	if x == 0:
		return n * n - y
	b = n + (y - 1) * (n - 1)
	if y % 2 == 1:
		return b + n - 1 - x
	return b + x - 1


# ------------------------------------------------------------
# 折り返し経路で次に進む向き
# ------------------------------------------------------------
def cyc_dir(x, y, rowe, n):
	if x == 0 and y > 0:
		return South      # 帰り道の列を南下する
	if rowe:
		if x < n - 1:
			return East
		return North
	if x > 1:
		return West
	if y < n - 1:
		return North
	return West           # (1,n-1) から帰り道の列へ入る


# ------------------------------------------------------------
# (0,0) から1周する．進めなくなったら False（＝盤面が埋まった）
# ------------------------------------------------------------
def lap(n):
	# 中間で体は経路上の連続した区間に戻っているので，進めなくなるのは
	# 盤面が埋まったときだけである．よって1手ごとに成否を見る必要がなく，
	# 1行進んだかを y 座標で確かめれば足りる（1歩あたりの処理を1行減らす）
	for i in range(n - 1):
		move(East)
	d = West
	for k in range(n - 1):
		y0 = get_pos_y()
		move(North)
		for i in range(n - 2):
			move(d)
		if get_pos_y() == y0:
			return False       # 1行も進めなかった＝盤面が埋まった
		if d == West:
			d = East
		else:
			d = West
	move(West)
	for i in range(n - 1):
		move(South)
	return True


# ------------------------------------------------------------
# 偶数盤面：近道つき前半 →（0,0）へ戻す → 周回
# ------------------------------------------------------------
def run_even(n):
	N = n * n
	nm1 = n - 1
	n2m1 = 2 * n - 1
	N2 = 2 * N
	cut = CUT_LEN
	if cut > N // 2:
		cut = N // 2

	x = 0
	y = 0
	rowe = True    # いまの行が東向きか（行0は東向き）
	h = 0          # 経路上の順番
	a = 0          # 目標リンゴの経路上の順番

	# 体の履歴を辞書のリングバッファで持つ（経路上の順番だけ覚えればよい）
	q = {}
	q[0] = 0
	qh = 1
	qt = 0

	grow = False   # 次の move で尾が伸びる（リンゴの上にいる）
	known = False  # リンゴの位置を知っているか
	idle = 0

	m = measure()
	if m != None:
		ax, ay = m
		a = ordv(ax, ay, n)
		known = True

	# ---------- 前半：北へ飛ぶ近道 ----------
	while qh - qt <= cut:
		t = q[qt]
		d_tail = (t - h) % N   # 経路上で尾までの距離＝前方に続く空きの長さ
		if d_tail == 0:
			d_tail = N         # 体が頭だけのとき
		# 進む向き（経路の構造から直接決める．関数呼び出しを省く）
		if x == 0 and y > 0:
			d = South          # 帰り道の列
		elif rowe:
			if x < nm1:
				d = East
			else:
				d = North
		elif x > 1:
			d = West
		elif y < nm1:
			d = North
		else:
			d = West           # (1,n-1) から帰り道の列へ

		dc = 1
		if known and y < nm1 and x > 0:
			if rowe:
				jump = n2m1 - 2 * x
			else:
				jump = 2 * x - 1
			# 前進量が 1 なら経路どおりの1手なので近道にならない
			if jump > 1 and jump + SAFE_MARGIN < d_tail and jump <= (a - h) % N:
				d = North
				dc = jump

		if not move(d):
			break              # 起こらないはずだが，起きたら中間に任せる
		if d == East:
			x += 1
		elif d == West:
			x -= 1
		elif d == North:
			y += 1
			rowe = not rowe
		else:
			y -= 1
			rowe = not rowe
		h = (h + dc) % N

		q[qh] = h
		qh += 1
		if grow:
			grow = False       # 尾を縮めない＝ここで実際に 1 伸びる
		else:
			q.pop(qt)
			qt += 1

		m = measure()
		if m != None:
			ax, ay = m
			a = ordv(ax, ay, n)
			known = True
			grow = True
		elif not known:
			# リンゴの位置が取れないまま盤面2周ぶん進んだら近道はあきらめる
			idle += 1
			if idle > N2:
				break

	if DEBUG:
		# 1, 前半の歩数, 体の長さ, 累計tick
		quick_print(1, qh - 1, qh - qt, get_tick_count())

	# ---------- 中間：経路どおりに (0,0) へ戻す ----------
	# 近道で飛ばしたマスを尾が通り過ぎるまで（体の長さの2倍で十分）進み，
	# かつ (0,0) に戻ったところで後半の1周ループに渡す
	need = 2 * (qh - qt)
	steps = 0
	guard = 3 * N
	while steps < need or x != 0 or y != 0:
		d = cyc_dir(x, y, rowe, n)
		if not move(d):
			return 1
		if d == North:
			y += 1
			rowe = not rowe
		elif d == East:
			x += 1
		elif d == West:
			x -= 1
		else:
			y -= 1
			rowe = not rowe
		steps += 1
		if steps > guard:
			return 1

	if DEBUG:
		# 2, 中間の歩数, 累計tick
		quick_print(2, steps, get_tick_count())

	# ---------- 後半：1周ずつ回る ----------
	laps = 0
	while lap(n):
		laps += 1
	return laps + 1


# ------------------------------------------------------------
# 奇数盤面：回り込みなしでは全マスを通る閉路が作れないので，
# 回り込みを使う経路（East を n-1 回 → North を 1 回）で周回する
# ------------------------------------------------------------
def run_odd(n):
	print("odd world: needs edge wrap")
	laps = 0
	while True:
		for k in range(n):
			for i in range(n - 1):
				if not move(East):
					return laps
			if not move(North):
				return laps
		laps += 1
		if laps > n * n:
			return laps


# ------------------------------------------------------------
# 1回分の走行：帽子をかぶり，盤面が埋まるまで進めて帽子を脱ぐ
# ------------------------------------------------------------
def snake_run():
	n = get_world_size()
	if num_items(Items.Cactus) < 1:
		print("no Cactus")     # リンゴはサボテンを消費して出現する
		return 0
	if CLEAR_FARM:
		clear()          # 農地を空にし，ドローンを (0,0) に戻す
	else:
		goto_origin()
	change_hat(Hats.Dinosaur_Hat)
	if n % 2 == 0:
		r = run_even(n)
	else:
		r = run_odd(n)
	change_hat(Hats.Straw_Hat)   # 帽子を脱ぐと尾が骨になる
	return r


# ------------------------------------------------------------
# メイン
# ------------------------------------------------------------
def main():
	# 目標は「開始時の所持数からの増分」で判定する．
	# リーダーボードは所持数0から始まるので TARGET_BONES とそのまま一致する
	target = num_items(Items.Bone) + TARGET_BONES

	while num_items(Items.Bone) < target:
		before = num_items(Items.Bone)
		r = snake_run()
		if DEBUG:
			quick_print(r, num_items(Items.Bone) - before, get_tick_count())
		if num_items(Items.Bone) <= before:
			print("no bones gained")
			return

	quick_print(get_tick_count())


main()
