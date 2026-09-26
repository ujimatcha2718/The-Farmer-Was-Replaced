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
#    線1本の並べ替えは swap が隣とだけなので，必要な交換回数は転倒数に
#    等しい．その回数で済む双方向バブル（カクテルソート）を使う
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
PROBE = 8                 # 手伝い先を探すとき，まず何歩ぶん探るか
PROBE_MIN = 4             # 探りでこの回数以上交換が起きた線だけ手伝う
HELP_PASSES = 4           # 手伝いは片道パスをこの回数だけ行って離れる
HELP_MISS = 2             # 空振りが連続でこの数に達したら手伝いをやめる
DEBUG = False             # True にすると段階ごとの tick を出力ページに書き出す

OPP = {North: South, South: North, East: West, West: East}


# ------------------------------------------------------------
# 線1本を昇順に並べ替える（双方向バブル＝カクテルソート）
#   n    : 線の長さ
#   fwd  : この向きへ大きくなるように並べる．back はその逆
#   ドローンは線の始点（fwd 側から見て手前）にいること
#   戻り値：終了時のドローンの位置（始点を0とする）
#
#   交換の直後に fwd へ動くと，ドローンは「いま押し出した大きい方」の上に
#   乗る．よって自分の下のサイズ cur を持ち歩けばよく，measure() は
#   1歩につき隣の1回で足りる
# ------------------------------------------------------------
def cocktail(n, pos, fwd, back):
	# pos : 開始時のドローンの位置（始点を0とする）．
	#       始点(0)なら前向きから，終点(n-1)なら後向きから始める．
	#       植え付け直後は終点にいるので，戻り歩をそのまま1パス目に使える
	lo = 0       # ここより手前は確定済み
	hi = n - 1   # ここより奥は確定済み
	while lo < hi:
		if pos < hi:
			# --- 前向き：大きい方を fwd 側へ運ぶ ---
			# 最後に交換した位置より奥は確定するので，そこまで hi を詰める
			last = -1
			cur = measure()
			for i in range(hi - pos):
				nxt = measure(fwd)
				if cur > nxt:
					swap(fwd)
					last = pos
				else:
					cur = nxt
				move(fwd)
				pos += 1
			if last < 0:
				return pos     # 交換が無かった＝整列済み
			hi = last
		if lo < hi and pos > lo:
			# --- 後向き：小さい方を back 側へ運ぶ ---
			last = -1
			cur = measure()
			for i in range(pos - lo):
				nxt = measure(back)
				if cur < nxt:
					swap(back)
					last = pos
				else:
					cur = nxt
				move(back)
				pos -= 1
			if last < 0:
				return pos
			lo = last
	return pos


# ------------------------------------------------------------
# 1パスぶんの走査．戻り値は交換した回数
#   pass_up : d 方向へ k 歩．大きい方を d 側へ運ぶ
#   pass_dn : d 方向へ k 歩．小さい方を d 側へ運ぶ
# ------------------------------------------------------------
def pass_up(k, d):
	c = 0
	cur = measure()
	for i in range(k):
		nxt = measure(d)
		if cur > nxt:
			swap(d)
			c += 1
		else:
			cur = nxt
		move(d)
	return c


def pass_dn(k, d):
	c = 0
	cur = measure()
	for i in range(k):
		nxt = measure(d)
		if cur < nxt:
			swap(d)
			c += 1
		else:
			cur = nxt
		move(d)
	return c


# ------------------------------------------------------------
# 線の中での自分の位置（始点を0とする）
# ------------------------------------------------------------
def line_pos(fwd):
	if fwd == North:
		return get_pos_y()
	return get_pos_x()


# ------------------------------------------------------------
# 整列を確定させる：交換が起きない「全体1パス」が出るまで往復する
#   戻り値は交換した総回数（0 なら来た時点で既に整列していた）
#
#   交換は「隣り合う逆順の対」に対してだけ行う．この操作は転倒数を1減らし
#   新たな転倒を作らないので，何機が同時に触っても線は壊れない．
#   よって「全体を1パス通して交換が0」は整列の証明になり，その後も崩れない．
#   担当機が範囲を詰める最適化をしていると補助機の介入で前提が崩れるため，
#   最後にこの確認を必ず通す
# ------------------------------------------------------------
def finish_count(n, pos, fwd, back):
	total = 0
	# まず近い端へ寄せる（この移動も交換を伴う有効なパスにする）
	if pos > 0 and pos * 2 <= n - 1:
		total += pass_dn(pos, back)
		pos = 0
	elif pos < n - 1:
		total += pass_up(n - 1 - pos, fwd)
		pos = n - 1
	while True:
		if pos == 0:
			c = pass_up(n - 1, fwd)
			pos = n - 1
		else:
			c = pass_dn(n - 1, back)
			pos = 0
		total += c
		if c == 0:
			return total


# ------------------------------------------------------------
# 自分の担当を終えたあと，まだ整列していない線を手伝う
#   隣の線へ1本ずつ移り，交換が起きる線があれば整列に加勢する．
#   整列済みの線を連続 HELP_MISS 本引いたら切り上げる（正しさは各担当機が
#   保証しているので，手伝いは打ち切っても問題ない）
# ------------------------------------------------------------
def help_loop(n, fwd, back, step):
	sd = step
	miss = 0
	while miss < HELP_MISS:
		if not move(sd):
			sd = OPP[sd]          # 盤の端に来たら逆向きへ
			if not move(sd):
				return
		# まず PROBE 歩だけ探る．整列済みならここで交換が起きないので
		# 1,600 tick 程度で見切れる（全体パスだと6,400かかる）
		pos = line_pos(fwd)
		if pos * 2 <= n - 1:
			k = PROBE
			if pos + k > n - 1:
				k = n - 1 - pos
			c = pass_up(k, fwd)
		else:
			k = PROBE
			if k > pos:
				k = pos
			c = pass_dn(k, back)
		if c >= PROBE_MIN:
			# 残り仕事が多い線と判断．決めた回数だけ加勢して離れる．
			# 「交換0の全体パス」による確定は担当機に任せる．
			# 補助機が確定までやると，その全体パス（6,400）が
			# 線の終了時刻を押し下げてしまう
			q = 0
			up = True
			while q < HELP_PASSES:
				pos = line_pos(fwd)
				if up:
					cc = pass_up(n - 1 - pos, fwd)
					up = False
				else:
					cc = pass_dn(pos, back)
					up = True
				if cc == 0:
					q = HELP_PASSES     # もう仕事が無い
				q += 1
			miss = 0
		else:
			miss += 1

# ------------------------------------------------------------
# 1本の線を耕して植え，育つのを待つ
#   ドローンは線の始点にいる．終了時は線の終点（fwd 側の端）にいる
# ------------------------------------------------------------
def plant_line(n, fwd):
	for i in range(n):
		if get_ground_type() != Grounds.Soil:
			till()
		plant(Entities.Cactus)
		if i < n - 1:
			move(fwd)
	# いまいるのは最後に植えたマス．成長時間は一定なので，ここが育てば
	# より早く植えた他のマスはすべて育っている
	w = 0
	while not can_harvest():
		w += 1
		if w > GROW_GUARD:
			print("cactus not growing")
			return False
	return True


# ------------------------------------------------------------
# k 本の線を受け持つ仕事の本体
#   step : 次の線の始点へ移る向き
#   do_plant : 植え付けも行うか
# ------------------------------------------------------------
def run_block(n, k, fwd, back, step, do_plant):
	j = 0
	while j < k:
		if do_plant:
			if not plant_line(n, fwd):
				return
			# 植え終わった位置（線の終点）から後向きに始める．
			# 始点へ戻る歩がそのまま1パス目になる
			p = cocktail(n, n - 1, fwd, back)
		else:
			p = cocktail(n, 0, fwd, back)
		# 補助機が入っている可能性があるので整列を確定させる
		finish_count(n, p, fwd, back)
		j += 1
		if j < k:
			p = line_pos(fwd)
			for i in range(p):
				move(back)      # 線の始点へ戻る
			move(step)          # 次の線へ
	# 自分の担当が終わったので，残っている線を手伝う
	help_loop(n, fwd, back, step)


def make_worker(n, off, k, fwd, back, step, do_plant):
	def run():
		for i in range(off):
			move(step)      # 自分の担当ブロックの先頭まで自力で移動する
		run_block(n, k, fwd, back, step, do_plant)
	return run


# ------------------------------------------------------------
# n 本の線を，空き枠＋親自身で分担する
#   ・親も1ブロックを受け持つ．枠が32・線が32本のとき親を数えないと
#     子は31機しか出せず，どれか1機が2本を受け持って2倍の時間がかかる
#   ・親は移動しない．各ドローンが自分の担当位置まで自力で移動するので，
#     親の往復（生成のための片道と戻り）が critical path から消える
# ------------------------------------------------------------
def spawn_blocks(n, fwd, back, step, do_plant):
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
	while i < n:
		k = (n - i) // (w - j)            # 残りの線を残りの働き手で均等に割る
		if k < 1:
			k = 1
		offs.append(i)
		ks.append(k)
		i += k
		j += 1

	# 遠いブロックを担当するドローンから先に生成する．
	# q 番目を生成するのにかかる時間と，そのドローンが担当位置まで歩く
	# 時間が打ち消し合うので，どのドローンもほぼ同時に作業を始められる
	# （最後に生成すると「生成待ち＋長い移動」が重なって最も遅くなる）
	handles = []
	q = len(offs) - 1
	while q > 0:
		h = spawn_drone(make_worker(n, offs[q], ks[q], fwd, back, step, do_plant))
		while h == None:
			# 念のための保険：出ているぶんを待ってから作り直す
			for hh in handles:
				wait_for(hh)
			handles = []
			h = spawn_drone(make_worker(n, offs[q], ks[q], fwd, back, step, do_plant))
		handles.append(h)
		q -= 1

	# 親は移動距離ゼロの先頭ブロックを受け持つ
	run_block(n, ks[0], fwd, back, step, do_plant)
	for h in handles:
		wait_for(h)


# ------------------------------------------------------------
# 1回分：植えて整列して収穫する
# ------------------------------------------------------------
def one_round(n):
	clear()      # 農地を空にし，ドローンを (0,0) へ戻す

	# --- 列：耕す→植える→育成待ち→列を北へ昇順 ---
	spawn_blocks(n, North, South, East, True)
	while get_pos_y() > 0:
		move(South)         # 親を (0,0) へ戻す（自分の担当列の途中にいる）
	while get_pos_x() > 0:
		move(West)
	if DEBUG:
		quick_print(1, get_tick_count())

	# --- 行：行を東へ昇順 ---
	spawn_blocks(n, East, West, North, False)
	while get_pos_x() > 0:
		move(West)          # 親を (0,0) へ戻す（自分の担当行の途中にいる）
	while get_pos_y() > 0:
		move(South)
	if DEBUG:
		quick_print(2, get_tick_count())

	# --- 収穫（整列しているので連鎖して全部取れる）---
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

	while num_items(Items.Cactus) < target:
		before = num_items(Items.Cactus)
		one_round(n)
		if DEBUG:
			quick_print(3, num_items(Items.Cactus) - before, get_tick_count())
		if num_items(Items.Cactus) <= before:
			print("no cactus gained")
			return

	quick_print(get_tick_count())


main()
