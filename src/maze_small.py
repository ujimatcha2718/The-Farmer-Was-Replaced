# ============================================================
#  The Farmer Was Replaced  迷路リーダーボード用コード（小さな迷路を並べる版）
#  （Leaderboards.Maze：金 9863168 を最速で集める）
#
#  仕様（probes/maze_small_probe.py で実機確認）
#   ・奇妙な物質を m * 2**(段階-1) 使うと，茂みを中心に m x m の迷路ができる
#   ・宝1個の金は m*m * 2**(段階-1)．再配置（宝の上で use_item）でも収穫でも同じ
#   ・迷路は同時にいくつも置ける．measure() は自分がいる迷路の宝を返す
#
#  方針
#   1. 盤面を 8x8 の迷路16個で埋める．1迷路で宝301個（再配置300回＋最後の収穫）
#      集めると 16 x 301 x 2048 = 9863168 でちょうど目標額になる
#   2. 各迷路に2機．親が「組長」16機（親を含む）を遠い順に生成し，組長は自分の
#      茂みの位置へ歩く．迷路ができると外から入れない（推定）ので，全員が着くまで
#      迷路を作らない．着いた組長は「旗」を1機出し，機数が 2*16 に達したら全員が
#      着いた合図とする．旗は合図を見届けてから消える
#   3. 組長は迷路を作り，1機で全探索して木を得る（全マスを見たら戻らずに止める）．
#      その木を閉じ込めた相棒を生成する．集めた機体はその場に残り，新しい宝に
#      木の上で一番近い機体が取りに行く（待機地点へ戻す方式より，迷路ごとの
#      ばらつきが小さい．tools/cost_models/maze_policy.py）
#   4. 宝の出現を数え，301個目は再配置せずに収穫する．use_item が失敗したとき
#      （上限）も収穫する（予備）
#
#  実行方法（別のコードウィンドウから）:
#   leaderboard_run(Leaderboards.Maze, "maze_small", 256)
#
#  ゲーム内言語の制約に合わせて，クラス・ラムダ・内包表記・三項演算子・
#  名前付き引数・int()・continue は使っていない
# ============================================================

TARGET = 9863168     # 「開始時の所持金＋この額」まで集めたら終了
SIDE = 8             # 1つの迷路の一辺
MAX_TREASURE = 301   # 1つの迷路で集める宝の数（再配置300回＋収穫1回）
FLAG_WAIT = 600      # 旗が合図を見届けてから消えるまでの tick
DEBUG = False

DIRS = [North, East, South, West]
OPP = {North: South, South: North, East: West, West: East}


def goto_open(tx, ty, n):
	# 迷路の無い畑を目的地へ進む．盤面の端は回り込むので近いほうの向きを選ぶ
	dx = (tx - get_pos_x() + n) % n
	d = East
	c = dx
	if dx * 2 > n:
		d = West
		c = n - dx
	for i in range(c):
		move(d)
	dy = (ty - get_pos_y() + n) % n
	d = North
	c = dy
	if dy * 2 > n:
		d = South
		c = n - dy
	for i in range(c):
		move(d)


# ------------------------------------------------------------
# 迷路の全探索（組長1機）．局所番号 k = lx*m + ly
#   戻り値 adj：adj[k] = [隣の局所番号, 向き, ...] の平らなリスト
#   全マスを見たら，その場で止める（最後の袋小路から戻らない）
# ------------------------------------------------------------
def explore(m, x0, y0):
	adj = []
	seen = []
	for i in range(m * m):
		adj.append([])
		seen.append(False)
	step = {North: 1, South: -1, East: m, West: -m}
	cur = (get_pos_x() - x0) * m + get_pos_y() - y0
	seen[cur] = True
	cnt = 1
	back = []
	while cnt < m * m:
		moved = False
		for d in DIRS:
			if not moved:
				lx = cur // m
				ly = cur % m
				ok = True
				if d == North:
					ok = ly < m - 1
				elif d == South:
					ok = ly > 0
				elif d == East:
					ok = lx < m - 1
				else:
					ok = lx > 0
				if ok:
					nc = cur + step[d]
					if not seen[nc]:
						if can_move(d):
							move(d)
							adj[cur].append(nc)
							adj[cur].append(d)
							adj[nc].append(cur)
							adj[nc].append(OPP[d])
							seen[nc] = True
							cnt += 1
							back.append(OPP[d])
							cur = nc
							moved = True
		if not moved:
			d = back.pop()
			move(d)
			cur = cur + step[d]
	return adj


def bfs_tree(adj, root, m):
	# 木を root から張る：parent, pdir（親→子の向き）, depth
	parent = []
	pdir = []
	depth = []
	for i in range(m * m):
		parent.append(-1)
		pdir.append(None)
		depth.append(-1)
	depth[root] = 0
	q = [root]
	h = 0
	while h < len(q):
		c = q[h]
		h += 1
		a = adj[c]
		j = 0
		while j < len(a):
			nc = a[j]
			if depth[nc] < 0:
				depth[nc] = depth[c] + 1
				parent[nc] = c
				pdir[nc] = a[j + 1]
				q.append(nc)
			j += 2
	return [parent, pdir, depth]


def tdist(a, b, tree):
	# 木の上の距離（深さをそろえてから共通の祖先まで上る）
	parent = tree[0]
	depth = tree[2]
	d = 0
	while depth[a] > depth[b]:
		a = parent[a]
		d += 1
	while depth[b] > depth[a]:
		b = parent[b]
		d += 1
	while a != b:
		a = parent[a]
		b = parent[b]
		d += 2
	return d


def nearest(pos, tk, tree):
	# 宝に一番近い機体（同じなら番号の小さい方）
	best = 0
	bd = tdist(pos[0], tk, tree)
	for i in range(1, len(pos)):
		d = tdist(pos[i], tk, tree)
		if d < bd:
			bd = d
			best = i
	return best


def path(a, b, tree):
	parent = tree[0]
	pdir = tree[1]
	depth = tree[2]
	up = []
	down = []
	while depth[a] > depth[b]:
		up.append(OPP[pdir[a]])
		a = parent[a]
	while depth[b] > depth[a]:
		down.append(pdir[b])
		b = parent[b]
	while a != b:
		up.append(OPP[pdir[a]])
		a = parent[a]
		down.append(pdir[b])
		b = parent[b]
	i = len(down) - 1
	while i >= 0:
		up.append(down[i])
		i -= 1
	return up


# ------------------------------------------------------------
# 宝を集める（1迷路に k 機．idx は自分の番号）
#   担当の決め方：集めた機体はその場に残り，新しい宝に（木の上で）一番近い
#   機体が取りに行く．全機が同じ宝の列を見ているので，互いの位置 pos を
#   通信なしで同じように更新できる（待っている機体は measure() を見続けるので
#   宝の移動を見逃さない．取りに行った機体の移動中は，宝は動かない）
#   cnt : これまでに現れた宝の数（最初の宝を1とする），last : いまの宝
# ------------------------------------------------------------
def collect(idx, m, x0, y0, tree, pos, sub, cnt, last):
	lk = (last[0] - x0) * m + last[1] - y0
	own = nearest(pos, lk, tree)
	stuck = 0
	while True:
		t = measure()
		if t == None:
			return cnt   # 迷路が消えた（他の機体が最後の宝を収穫した）
		if t != last:
			pos[own] = lk      # 前の宝は own が集め，そこに残っている
			cnt += 1
			last = t
			lk = (t[0] - x0) * m + t[1] - y0
			own = nearest(pos, lk, tree)
			stuck = 0
		if own == idx:
			cur = (get_pos_x() - x0) * m + get_pos_y() - y0
			for d in path(cur, lk, tree):
				move(d)
			if cnt >= MAX_TREASURE:
				harvest()
				return cnt
			if not use_item(Items.Weird_Substance, sub):
				harvest()      # 再配置できなかった（上限）→ 収穫して終わる
				return cnt
			stuck += 1
			if stuck >= 3:
				harvest()      # 再配置したのに宝が動かない（予備）
				return cnt


def make_partner(idx, m, x0, y0, tree, pos, sub, cnt, last):
	def run():
		p = []
		for v in pos:
			p.append(v)        # 念のため自分用に写す
		collect(idx, m, x0, y0, tree, p, sub, cnt, last)
	return run


def make_flag(total):
	def run():
		w = 0
		while num_drones() < total:
			w += 1
		t0 = get_tick_count()
		while get_tick_count() - t0 < FLAG_WAIT:
			w += 1
	return run


def leader(bx, by, m, k, total, sub):
	n = get_world_size()
	goto_open(bx, by, n)
	if get_entity_type() != None:
		harvest()
	if get_ground_type() != Grounds.Grassland:
		till()
	plant(Entities.Bush)
	h = spawn_drone(make_flag(total))
	while h == None:
		h = spawn_drone(make_flag(total))
	# 全組長が着くまで待つ（機数が total に達したら全員が着いている）
	w = 0
	while num_drones() < total:
		w += 1
	if not use_item(Items.Weird_Substance, sub):
		print("maze failed")
		return
	x0 = bx - m // 2
	y0 = by - m // 2
	last = measure()
	adj = explore(m, x0, y0)
	root = (bx - x0) * m + by - y0
	tree = bfs_tree(adj, root, m)
	if DEBUG:
		if bx == m // 2:
			if by == m // 2:
				quick_print("explored", get_tick_count())
	# 相棒は組長の今の位置に生成する．最初は全員が同じ位置にいる
	here = (get_pos_x() - x0) * m + get_pos_y() - y0
	pos = []
	for i in range(k):
		pos.append(here)
	for i in range(1, k):
		h = spawn_drone(make_partner(i, m, x0, y0, tree, pos, sub, 1, last))
		while h == None:
			h = spawn_drone(make_partner(i, m, x0, y0, tree, pos, sub, 1, last))
	c = collect(0, m, x0, y0, tree, pos, sub, 1, last)
	if DEBUG:
		quick_print("maze", bx, by, "count", c, "end", get_tick_count())


def make_leader(bx, by, m, k, total, sub):
	def run():
		leader(bx, by, m, k, total, sub)
	return run


def main():
	clear()
	n = get_world_size()
	m = SIDE
	u = 2 ** (num_unlocked(Unlocks.Mazes) - 1)
	sub = m * u
	K = n // m                 # 1辺に並ぶ迷路の数
	M = K * K
	base = num_drones()
	D = max_drones() - base + 1
	k = D // M                 # 1迷路あたりの機数
	if k < 2:
		print("need", 2 * M, "drones")
		return
	total = base + 2 * M - 1   # 組長 M 機（親を含む）＋旗 M 機
	goal = num_items(Items.Gold) + TARGET
	if DEBUG:
		quick_print("n", n, "m", m, "mazes", M, "per maze", k, "WS", num_items(Items.Weird_Substance), "need", M * MAX_TREASURE * sub)

	while num_items(Items.Gold) < goal:
		# 組長の担当（茂みの位置）．親は (m//2, m//2) を受け持つ
		bxs = []
		bys = []
		ds = []
		for i in range(K):
			for j in range(K):
				if i + j > 0:
					bx = i * m + m // 2
					by = j * m + m // 2
					dx = bx
					if dx * 2 > n:
						dx = n - dx
					dy = by
					if dy * 2 > n:
						dy = n - dy
					bxs.append(bx)
					bys.append(by)
					ds.append(dx + dy)
		# 遠い順に生成する（単純な選択）
		handles = []
		used = []
		for i in range(len(ds)):
			used.append(False)
		for r in range(len(ds)):
			bi = -1
			for i in range(len(ds)):
				if not used[i]:
					if bi < 0 or ds[i] > ds[bi]:
						bi = i
			used[bi] = True
			h = spawn_drone(make_leader(bxs[bi], bys[bi], m, k, total, sub))
			while h == None:
				h = spawn_drone(make_leader(bxs[bi], bys[bi], m, k, total, sub))
			handles.append(h)
		leader(m // 2, m // 2, m, k, total, sub)
		for h in handles:
			wait_for(h)
		if DEBUG:
			quick_print("round", num_items(Items.Gold), get_tick_count())
		if num_items(Items.Gold) < goal:
			clear()

	quick_print(get_tick_count())


main()
