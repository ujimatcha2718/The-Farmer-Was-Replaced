# ============================================================
#  The Farmer Was Replaced  サボテンの整列コード
#  （Leaderboards.Cactus：33554432 個を最速で集める）
#
#  整列条件（Wiki）
#    北と東の隣が自分以上，南と西の隣が自分以下．つまり盤面全体が
#    **東へも北へも非減少**であればよい．整列した状態で1本収穫すると
#    連鎖して全部が収穫され，同時に収穫した本数の2乗が手に入る．
#    32x32 なら 1024^2 = 1048576，係数32を掛けて 33554432 でちょうど目標に届く
#
#  方針
#    1. 各列を「北へ向かって昇順」にする
#    2. 各行を「東へ向かって昇順」にする
#    この2段階で盤面全体が2次元単調になる．根拠は古典的な補題で，
#    「全列を昇順にしたあと各行を昇順にしても列の昇順は崩れない」
#    （隣り合う2行が要素ごとに大小関係を保つなら，各行を並べ替えても
#      要素ごとの大小関係は保たれる）．n=4,8,16,32 で各300回確認済み
#
#    線1本の並べ替え（sort_line）は，逆順の隣どうしだけを交換するので
#    交換回数は転倒数（下限）に等しい．移動を減らすために次の3点を行う
#      ・3マス整列：ドローンは足元の両隣と交換できる．大きい方を前へ運んだ
#        直後に，置いていった小さい方を後ろ隣とも比べて交換する
#      ・値を覚える：線の値をリストに持つので，パスの中で最後に交換が
#        起きる位置が事前に分かる．そこで折り返す
#      ・最後の交換のあとは動かない：その場から逆向きのパスを始める
#    小さな線（n=7〜9）で，総当たりの最適手順との差は 0.1〜0.7%
#    （tools/cost_models/optimum_small.py）
#
#  並列化：線は互いに独立なので1本1機に割り当てる．ドローン枠が線の数より
#    少ない場合は，**空き枠を数えて線を均等に分担する**．枠が足りないまま
#    生成に失敗すると処理されない線が残るため，先に枠数を見て割り振る
#
#  実行方法（別のコードウィンドウから）:
#   leaderboard_run(Leaderboards.Cactus, "cactus", 256)
#   ※ "cactus" はこのコードウィンドウの名前に合わせる
#
#  ゲーム内言語の制約に合わせて，クラス・ラムダ・内包表記・三項演算子・
#  名前付き引数・int()・continue は使っていない
# ============================================================

TARGET_CACTUS = 33554432  # 「開始時の所持数＋この数」まで集めたら終了
GROW_GUARD = 200000       # 成長待ちの上限（超えたら異常として止める）
GROW_WAIT = False         # True：植え終わったら育つのを待ってから列を整列する（旧動作）
#   実測で成長には約5877 tick かかる．measure() と swap() は育つ前でも
#   使えるので，待たずに整列を始める．育つ前に swap できない仕様だった
#   場合は1回目の収穫量で検知し，自動で旧動作に戻す
DEBUG = False             # True にすると段階ごとの tick を出力ページに書き出す


# ------------------------------------------------------------
# 線1本を昇順に並べ替える
#   n     : 線の長さ
#   a     : 線の値のリスト（始点を0とする）．交換に合わせて書き換える
#   pos   : 開始時のドローンの位置（始点を0とする）
#   fwd   : この向きへ大きくなるように並べる．back はその逆
#   known : False なら a は pos 以外が未知．1パス目で measure しながら埋める
#           （1パス目は必ず前向きで，pos=0 から始めること）
#   戻り値：終了時のドローンの位置
#
#   前向きのパスでは，足元の値 a[pos] が「ここまでの最大」になっている．
#   a[pos] > a[pos+1] なら swap(fwd) で最大を前へ送り，置いていった
#   小さい方が後ろ隣 a[pos-1] より小さければ swap(back) で1つ戻す．
#   この2回の交換はどちらも逆順の組を1つ直すので，交換回数は増えない．
#   後ろ向きのパスはこの逆（最小を後ろへ運び，大きい方を1つ前へ送る）
#
#   lo より手前・hi より奥は確定済み．前向きのパスで最後に交換した位置が
#   次の hi になる（そこより奥は昇順で，手前のどれ以上でもある）
# ------------------------------------------------------------
def sort_line(n, a, pos, fwd, back, known):
	lo = 0
	hi = n - 1
	up = pos < hi
	while lo < hi:
		if up:
			# --- 前向き：最大を fwd 側へ運ぶ ---
			if known:
				# このパスで最後に交換が起きる位置を求める
				m = a[pos]
				last = -1
				p = pos
				while p < hi:
					v = a[p + 1]
					if m > v:
						last = p
					else:
						m = v
					p += 1
				if last < 0:
					return pos     # 交換が無い＝整列済み
			else:
				last = hi - 1      # 値が未知：端の1つ手前まで進む
			found = -1
			while True:
				if not known:
					a[pos + 1] = measure(fwd)
				c = a[pos]
				v = a[pos + 1]
				if c > v:
					swap(fwd)
					a[pos + 1] = c
					found = pos
					a[pos] = v
					if pos > lo:
						u = a[pos - 1]
						if u > v:
							swap(back)
							a[pos] = u
							a[pos - 1] = v
				if pos >= last:
					break          # 最後の交換位置では動かずに折り返す
				move(fwd)
				pos += 1
			known = True
			if found < 0:
				return pos
			hi = found
		else:
			# --- 後向き：最小を back 側へ運ぶ ---
			m = a[pos]
			last = -1
			p = pos
			while p > lo:
				v = a[p - 1]
				if m < v:
					last = p
				else:
					m = v
				p -= 1
			if last < 0:
				return pos
			while True:
				c = a[pos]
				v = a[pos - 1]
				if c < v:
					swap(back)
					a[pos - 1] = c
					a[pos] = v
					if pos < hi:
						u = a[pos + 1]
						if u < v:
							swap(fwd)
							a[pos] = u
							a[pos + 1] = v
				if pos <= last:
					break
				move(back)
				pos -= 1
			lo = last
		up = not up
	return pos


# ------------------------------------------------------------
# 1本の線を耕して植え，値をリストに記録する
#   ドローンは線の始点にいる．終了時は線の終点（fwd 側の端）にいる
#   育つのを待たない場合は，植えながら前向きの1パスを兼ねる：
#   植えたマスが1つ手前より小さければ swap(back) で入れ替え，
#   大きい方を持ったまま次へ進む
#   戻り値：値のリスト（失敗したら空のリスト）
# ------------------------------------------------------------
def plant_line(n, fwd, back, wait):
	a = []
	for i in range(n):
		if get_ground_type() != Grounds.Soil:
			till()
		plant(Entities.Cactus)
		v = measure()
		a.append(v)
		if not wait:
			if i > 0:
				c = a[i - 1]
				if c > v:
					swap(back)
					a[i - 1] = v
					a[i] = c
		if i < n - 1:
			move(fwd)
	# いまいるのは最後に植えたマス．成長時間は一定なので，ここが育てば
	# より早く植えた他のマスはすべて育っている
	if not wait:
		return a
	w = 0
	while not can_harvest():
		w += 1
		if w > GROW_GUARD:
			print("cactus not growing")
			return []
	return a


# ------------------------------------------------------------
# k 本の線を受け持つ仕事の本体
#   step : 次の線の始点へ移る向き
#   mode : 0 = 整列だけ，1 = 植えて整列，2 = 植えて育つのを待ってから整列
# ------------------------------------------------------------
def run_block(n, k, fwd, back, step, mode):
	j = 0
	while j < k:
		if mode > 0:
			a = plant_line(n, fwd, back, mode == 2)
			if len(a) < n:
				return
			# 植え終わった位置（線の終点）から後向きに始める
			p = sort_line(n, a, n - 1, fwd, back, True)
		else:
			a = []
			for i in range(n):
				a.append(0)
			a[0] = measure()
			p = sort_line(n, a, 0, fwd, back, False)
		j += 1
		if j < k:
			for i in range(p):
				move(back)      # 線の始点へ戻る
			move(step)          # 次の線へ


def make_worker(n, d, k, fwd, back, step, dmove, mode):
	def run():
		for i in range(d):
			move(dmove)     # 自分の担当ブロックの先頭まで自力で移動する
		run_block(n, k, fwd, back, step, mode)
	return run


# ------------------------------------------------------------
# n 本の線を，空き枠＋親自身で分担する
#   ppos : 親がいる線の番号（親は線の始点にいること）
#   ・親も1ブロックを受け持つ．枠が32・線が32本のとき親を数えないと
#     子は31機しか出せず，どれか1機が2本を受け持って2倍の時間がかかる
#   ・親は自分のいる線を含むブロックを受け持ち，移動しない．
#     各ドローンは親の位置から自分の担当位置まで自力で移動する
#   ・遠いブロックの担当から先に生成する．q 番目を生成するのにかかる時間と，
#     そのドローンが担当位置まで歩く時間が打ち消し合うので，どのドローンも
#     ほぼ同時に作業を始められる
#   戻り値：親の終了位置の線の番号
# ------------------------------------------------------------
def spawn_blocks(n, fwd, back, step, stepback, mode, ppos):
	w = max_drones() - num_drones() + 1   # 空き枠＋親
	if w > n:
		w = n
	if w < 1:
		w = 1

	# まず各ブロックの先頭位置と本数を決める
	offs = []
	ks = []
	i = 0
	j = 0
	b0 = 0
	while i < n:
		k = (n - i) // (w - j)            # 残りの線を残りの働き手で均等に割る
		if k < 1:
			k = 1
		if i <= ppos:
			if ppos < i + k:
				b0 = j                    # 親のいる線を含むブロック
		offs.append(i)
		ks.append(k)
		i += k
		j += 1

	# 両端から，遠い方を先に生成する
	handles = []
	lq = 0
	rq = len(offs) - 1
	while lq < b0 or rq > b0:
		q = rq
		if lq < b0:
			if rq <= b0:
				q = lq
			elif ppos - offs[lq] > offs[rq] - ppos:
				q = lq
		if q == lq:
			lq += 1
		else:
			rq -= 1
		d = offs[q] - ppos
		dm = step
		if d < 0:
			d = -d
			dm = stepback
		h = spawn_drone(make_worker(n, d, ks[q], fwd, back, step, dm, mode))
		while h == None:
			# 念のための保険：出ているぶんを待ってから作り直す
			for hh in handles:
				wait_for(hh)
			handles = []
			h = spawn_drone(make_worker(n, d, ks[q], fwd, back, step, dm, mode))
		handles.append(h)

	# 親は自分のいる線を含むブロックを受け持つ（1本ずつなら移動は0）
	for i in range(ppos - offs[b0]):
		move(stepback)
	run_block(n, ks[b0], fwd, back, step, mode)
	for h in handles:
		wait_for(h)


# ------------------------------------------------------------
# 1本1機で分担できるときの速い版
#   列を終えたドローンが消えて空いた枠に，行を受け持つドローンを先に出して
#   おき，担当の行の始点で待たせる．全列が終わったら親が最後の1機を出し，
#   機数が total に達したのを合図に全員が行の整列を始める．
#   行の段階の生成待ちと移動（約 6400 tick）が律速から外れる
#
#   終わった列の本数 k は機数から逆算する．配り役が生成に失敗して列の
#   ドローンが f 機少ないときは k が f 多く出るが，そのぶん生きている列の
#   ドローンも f 機少ないので，機数は下の式と同じく base + n - 2 を超えない
#   合図が早すぎないこと：列が k 本（k>=1）終わった時点で行の担当は
#   多くても k-1 機しか出さない．よって機数は
#     base + (n-1-k) + (k-1) = base + n - 2 < total = base + n - 1
#   に留まり，最後の1機を出したときに初めて total に達する．
#   全列が終わってから出す2機（親に近い行）は待たずに始める
# ------------------------------------------------------------
def col_worker(n, d, dm, mode):
	def run():
		for i in range(d):
			move(dm)
		run_block(n, 1, North, South, East, mode)
	return run


# 列の配り方（盤面の端で回り込むことを使う．実機で確認済み）
#   親は列0．まず「東の配り役」を1機出し，配り役は列1へ動いて列 2..m を
#   遠い順に生成してから列1を受け持つ．親は西へ回り込んで列 n-1..n-L を
#   遠い順に生成してから列0を受け持つ．2機が並行して配るので，最後の
#   ドローンが作業を始めるのは 32x32 で 3600 tick（親1機で配ると 6400）．
#   これは最短である（tools/cost_models/spawn_tree.py の動的計画法）
#   配り役が生成に失敗したときは，残りの列（1..d+1）を自分で順に受け持つ
def col_leader(n, m, mode):
	def run():
		move(East)
		d = m - 1
		while d > 0:
			h = spawn_drone(col_worker(n, d, East, mode))
			if h == None:
				run_block(n, d + 1, North, South, East, mode)
				return
			d -= 1
		run_block(n, 1, North, South, East, mode)
	return run


def row_worker(n, d, dm, total):
	def run():
		for i in range(d):
			move(dm)
		w = 0
		while num_drones() < total:
			w += 1         # 全列の整列が終わるのを待つ
		run_block(n, 1, East, West, North, 0)
	return run


def fast_round(n, mode):
	base = num_drones()          # 親（と，いれば他のドローン）
	total = base + n - 1

	# --- 列：東は配り役，西は親が回り込んで遠い列から生成する ---
	L = (n - 1) // 2             # 親が配る西側の列数
	h = spawn_drone(col_leader(n, n - 1 - L, mode))
	if h == None:
		return False
	d = L
	while d > 0:
		h = spawn_drone(col_worker(n, d, West, mode))
		if h == None:
			return False
		d -= 1
	run_block(n, 1, North, South, East, mode)
	p = get_pos_y()              # 親は (0,p) にいる．行 p を受け持つ

	# 最後に出す1機は親の隣の行．残りは遠い行から順に先に出す
	last = p + 1
	if last >= n:
		last = p - 1
	rows = []
	lq = 0
	rq = n - 1
	while lq <= rq:
		if p - lq >= rq - p:
			r = lq
			lq += 1
		else:
			r = rq
			rq -= 1
		if r != p:
			if r != last:
				rows.append(r)

	handles = []
	r = 0
	while r < n - 2:
		# 終わった列の本数 k = base + (n-1) + r - 機数
		k = base + n - 1 + r - num_drones()
		while r < k - 1:
			d = rows[r] - p
			dm = North
			if d < 0:
				d = -d
				dm = South
			t = total
			if k >= n - 1:
				t = 0              # 全列が終わってから出す機体は待たない
			h = spawn_drone(row_worker(n, d, dm, t))
			while h == None:
				h = spawn_drone(row_worker(n, d, dm, t))
			handles.append(h)
			r += 1
	# ここに来たときには全列が終わっている（r = n-2 の生成には k = n-1 が要る）
	d = last - p
	dm = North
	if d < 0:
		d = -d
		dm = South
	h = spawn_drone(row_worker(n, d, dm, 0))
	while h == None:
		h = spawn_drone(row_worker(n, d, dm, 0))
	handles.append(h)
	if DEBUG:
		quick_print(1, get_tick_count())

	# --- 行：親は行 p を受け持つ ---
	run_block(n, 1, East, West, North, 0)
	for h in handles:
		wait_for(h)
	return True


# ------------------------------------------------------------
# 1回分：植えて整列して収穫する
# ------------------------------------------------------------
def one_round(n, wait):
	clear()      # 農地を空にし，ドローンを (0,0) へ戻す
	mode = 1
	if wait:
		mode = 2

	fast = False
	if n > 2:
		if max_drones() - num_drones() + 1 >= n:
			fast = True
	if fast:
		fast_round(n, mode)
	else:
		# --- 列：耕す→植える（前向き1パスを兼ねる）→列を北へ昇順 ---
		spawn_blocks(n, North, South, East, West, mode, get_pos_x())
		# 親は列0のどこかにいる．(0,0) へ戻らず，いまいる行から行の段階を始める
		# （担当が複数本のときは，列の終点側にいるので始点の列0へ戻る）
		while get_pos_x() > 0:
			move(West)
		if DEBUG:
			quick_print(1, get_tick_count())

		# --- 行：行を東へ昇順 ---
		spawn_blocks(n, East, West, North, South, 0, get_pos_y())
	if DEBUG:
		quick_print(2, get_tick_count())

	# --- 収穫（整列しているので，どのマスからでも連鎖して全部取れる）---
	# 育ち切っていないと連鎖しないので，念のため足元が育つのを確かめる
	# （植え終わりから整列の終わりまで10万 tick 以上あるので，通常は待たない）
	w = 0
	while not can_harvest():
		w += 1
		if w > GROW_GUARD:
			return
	harvest()


# ------------------------------------------------------------
# メイン
# ------------------------------------------------------------
def main():
	n = get_world_size()
	if DEBUG:
		quick_print(0, n, max_drones())
	# 目標は「開始時の所持数からの増分」で判定する．
	# リーダーボードは所持数0から始まるので TARGET_CACTUS とそのまま一致する
	target = num_items(Items.Cactus) + TARGET_CACTUS

	wait = GROW_WAIT
	while num_items(Items.Cactus) < target:
		before = num_items(Items.Cactus)
		one_round(n, wait)
		if DEBUG:
			quick_print(3, num_items(Items.Cactus) - before, get_tick_count())
		if not wait and num_items(Items.Cactus) - before < n * n * n * n:
			# 育つ前の swap が効かない等で整列できなかった → 旧動作に戻す
			print("sort before growth failed")
			wait = True
		elif num_items(Items.Cactus) <= before:
			print("no cactus gained")
			return

	quick_print(get_tick_count())


main()
