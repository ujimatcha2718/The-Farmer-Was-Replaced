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
#      ばらつきが小さい．tools/cost_models/maze_policy.py）．待っている機体は動かない
#      （反対側の待機地点へ歩かせる案は遅くなった．tools/cost_models/maze_idle2.py）
#   4. 再配置のたびに壁がときどき消える（8x8 で299回に25枚．probes/maze_walls_probe.py）．
#      歩きながら足元の壁を can_move で調べ，見つけた近道を使う（担当の判定は木の距離のまま）
#   5. 宝の出現を数え，301個目は再配置せずに収穫する．use_item が失敗したとき
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
SAME_CELL_WAIT = 250 # 宝が足元に出たとき，再配置の前に待つ tick
SHORTCUT = True      # 再配置で消えた壁（近道）を歩きながら見つけて使うか
RECHECK = 30         # 同じマスの壁を調べ直すまでの再配置の回数
ROW_CHUNK = 2        # 待っている間に1回で進める表作り（BFS）のマス数．
                     # 大きくすると measure() を見る間隔が延び，宝が1歩先で集められた
                     # ときの再配置（約200 tick で次へ変わる）を見逃して2機の記録が
                     # 食い違う（8 でシミュレータで起きた）．2 なら間隔は約70 tick（推定）
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
	return [parent, pdir, depth, q]


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


def decide(idx, pos, lk, mylen, tree):
	# 宝に一番近い機体（同じなら番号の小さい方）．自分の距離は，自分の経路の長さ
	# mylen をそのまま使う（木の上の距離なので，他の機体が tdist で求める値と一致する）
	best = -1
	bd = 0
	for i in range(len(pos)):
		d = mylen
		if i != idx:
			d = tdist(pos[i], lk, tree)
		if best < 0 or d < bd:
			bd = d
			best = i
	return best


def decide_row(pos, dist):
	# 表があるとき：距離は表を引くだけ（木の上の距離なので decide と同じ結果になる）
	best = 0
	bd = dist[pos[0]]
	for i in range(1, len(pos)):
		if dist[pos[i]] < bd:
			bd = dist[pos[i]]
			best = i
	return best


def drop_pair(lst, v):
	# [隣, 向き, ...] から隣が v の組を除いた新しいリスト
	out = []
	j = 0
	while j < len(lst):
		if lst[j] != v:
			out.append(lst[j])
			out.append(lst[j + 1])
		j += 2
	return out


def wall_dirs(c, adj, m):
	# c から見て迷路の中にあり，木の辺ではない方向（壁があるはずの方向）[隣, 向き, ...]
	lx = c // m
	ly = c % m
	w = []
	for d in DIRS:
		ok = True
		nb = c
		if d == North:
			ok = ly < m - 1
			nb = c + 1
		elif d == South:
			ok = ly > 0
			nb = c - 1
		elif d == East:
			ok = lx < m - 1
			nb = c + m
		else:
			ok = lx > 0
			nb = c - m
		if ok:
			a = adj[c]
			j = 0
			while j < len(a):
				if a[j] == nb:
					ok = False
				j += 2
		if ok:
			w.append(nb)
			w.append(d)
	return w


def discover(cur, walls, ext, adj, m):
	# 足元の壁を can_move で調べ，消えていれば近道として覚える
	if walls[cur] == None:
		walls[cur] = wall_dirs(cur, adj, m)
	wl = walls[cur]
	j = 0
	while j < len(wl):
		if can_move(wl[j + 1]):
			nb = wl[j]
			d = wl[j + 1]
			ext[cur].append(nb)
			ext[cur].append(d)
			ext[nb].append(cur)
			ext[nb].append(OPP[d])
			walls[cur] = drop_pair(walls[cur], nb)
			if walls[nb] != None:
				walls[nb] = drop_pair(walls[nb], cur)
			wl = walls[cur]
		else:
			j += 2


# ------------------------------------------------------------
# 宝の位置ごとの表（木の上）：dist[x] = x から宝までの距離，nh[x] = 宝へ向かう次の向き
#   1つ作るのに木の BFS 1回（約 2000 tick，推定）．待っている間に少しずつ作り（row_steps），
#   できた表は使い回す．宝の位置は64通りなので，途中からはほぼ表を引くだけになる
# ------------------------------------------------------------
def row_start(t, m):
	dist = []
	nh = []
	for i in range(m * m):
		dist.append(-1)
		nh.append(None)
	dist[t] = 0
	return [t, dist, nh, [t], 0]


def row_steps(st, adj, k):
	# BFS を最大 k マスぶん進める．終わったら True
	dist = st[1]
	nh = st[2]
	q = st[3]
	h = st[4]
	while h < len(q) and k > 0:
		c = q[h]
		h += 1
		a = adj[c]
		j = 0
		while j < len(a):
			nb = a[j]
			if dist[nb] < 0:
				dist[nb] = dist[c] + 1
				nh[nb] = OPP[a[j + 1]]
				q.append(nb)
			j += 2
		k -= 1
	st[4] = h
	return h >= len(q)


def walk_row(cur, lk, row, walls, ext, chk, cnt, step, adj, m):
	# 表を使って cur から lk へ歩く．戻り値：歩いた歩数
	#   ・足元の壁は，前に調べてから RECHECK 回以上再配置があったマスだけ調べる
	#   ・足元に覚えた近道があり，その先の方が宝に（木の上で）近ければ跳ぶ
	dist = row[0]
	nh = row[1]
	n = 0
	while cur != lk:
		if chk[cur] <= cnt:
			discover(cur, walls, ext, adj, m)
			chk[cur] = cnt + RECHECK
		d = nh[cur]
		nb = cur + step[d]
		e = ext[cur]
		if len(e) > 0:
			best = dist[nb]
			j = 0
			while j < len(e):
				if dist[e[j]] < best:
					best = dist[e[j]]
					nb = e[j]
					d = e[j + 1]
				j += 2
		move(d)
		cur = nb
		n += 1
	return n


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
#   通信なしで同じように更新できる（待っている機体は動かず measure() を見続けるので
#   宝の移動を見逃さない．取りに行った機体の移動中は，宝は動かない）
#   cnt : これまでに現れた宝の数（最初の宝を1とする），last : いまの宝
#   walked : DEBUG 用．取りに行った歩数を足していく
# ------------------------------------------------------------
def collect(idx, m, x0, y0, tree, adj, pos, sub, cnt, last, walked):
	n = m * m
	rows = []                # rows[t] = [dist, nh]（宝の位置 t ごとの表．まだなら None）
	ext = []                 # 自分が見つけた近道 ext[c] = [隣, 向き, ...]
	walls = []               # walls[c] = まだ壁がある（はずの）方向．初めて調べるときに作る
	chk = []                 # chk[c]：宝の数がこれになったら c の壁を調べ直す
	for i in range(n):
		rows.append(None)
		ext.append([])
		walls.append(None)
		chk.append(0)
	step = {North: 1, South: -1, East: m, West: -m}
	bst = None               # 待っている間に作っている表（BFS の途中）
	nxt = 0                  # 次に表を作る宝の位置の候補
	lk = (last[0] - x0) * m + last[1] - y0
	plan = []
	if SHORTCUT:
		own = -1
	else:
		plan = path(pos[idx], lk, tree)
		own = decide(idx, pos, lk, len(plan), tree)
	t_seen = get_tick_count()
	stuck = 0
	first = True
	while True:
		t = measure()
		if t == None:
			return cnt   # 迷路が消えた（他の機体が最後の宝を収穫した）
		if t != last or first:
			if not first:
				pos[own] = lk      # 前の宝は own が集め，そこに残っている
				cnt += 1
				last = t
				lk = (t[0] - x0) * m + t[1] - y0
			first = False
			if rows[lk] != None:
				own = decide_row(pos, rows[lk][0])
				plan = []
			else:
				plan = path(pos[idx], lk, tree)
				own = decide(idx, pos, lk, len(plan), tree)
			t_seen = get_tick_count()
			stuck = 0
		if own == idx:
			cur = pos[idx]
			if cur == lk:
				# 宝が足元に出た．すぐ再配置すると，直前に再配置した機体がこの宝を
				# 見る前に次の宝へ変わり，宝の数と位置の記録が食い違うおそれがある
				# （use_item の効果が 200 tick の始めに出る場合．シミュレータで発生．
				# 実機は不明）．少し待つ
				w = 0
				while get_tick_count() - t_seen < SAME_CELL_WAIT:
					w += 1
			if SHORTCUT and rows[lk] != None:
				nstep = walk_row(cur, lk, rows[lk], walls, ext, chk, cnt, step, adj, m)
			else:
				if len(plan) == 0:
					plan = path(cur, lk, tree)
				nstep = len(plan)
				for d in plan:
					move(d)
			if DEBUG:
				walked[0] += nstep
			plan = []
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
		elif SHORTCUT:
			# 待っている間に表を少しずつ作る（ROW_CHUNK マスずつ．宝が動いたらすぐ判断できるように）
			if bst == None:
				while nxt < n and rows[nxt] != None:
					nxt += 1
				if nxt < n:
					bst = row_start(nxt, m)
			if bst != None:
				if row_steps(bst, adj, ROW_CHUNK):
					rows[bst[0]] = [bst[1], bst[2]]
					bst = None


def make_partner(idx, m, x0, y0, tree, adj, pos, sub, cnt, last):
	def run():
		p = []
		for v in pos:
			p.append(v)        # 念のため自分用に写す
		wk = [0]
		collect(idx, m, x0, y0, tree, adj, p, sub, cnt, last, wk)
		return wk[0]
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
	hs = []
	for i in range(1, k):
		h = spawn_drone(make_partner(i, m, x0, y0, tree, adj, pos, sub, 1, last))
		while h == None:
			h = spawn_drone(make_partner(i, m, x0, y0, tree, adj, pos, sub, 1, last))
		hs.append(h)
	wk = [0]
	c = collect(0, m, x0, y0, tree, adj, pos, sub, 1, last, wk)
	if DEBUG:
		for h in hs:
			wk[0] += wait_for(h)
		# 取りに行った歩数の合計（待っている機体の移動は含まない）
		quick_print("maze", bx, by, "count", c, "steps", wk[0], "end", get_tick_count())


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
