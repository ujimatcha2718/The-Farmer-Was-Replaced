# ============================================================
#  The Farmer Was Replaced  迷路リーダーボード用コード（A*併用版）
#  （Leaderboards.Maze：32x32迷路を300回再利用した分の金 9863168 を最速で集める）
#
#  方針
#   1. 迷路を1回だけ全探索し，木（親・方向・深さ）と隣接リストを作る．
#      探索は分岐点ごとに空きドローンへ枝を任せる並列DFSで行う
#   2. 以後は再利用だけで金を得る．再配置の上限（300回）に達したら収穫し，
#      迷路を作り直して目標額に達するまで繰り返す
#   3. 全ドローンを均等配置し，宝に一番近い担当ドローンだけが取りに行く
#   4. 経路は通常は木のLCA（安い）．壁が消えてループが見つかっている場合のみ，
#      「最大でも節約できる手数」以内の計算量に制限したA*で近道を探す
#   5. 近道（消えた壁）の発見は，時間に影響しない「待機地点へ戻る移動」の間だけ行う
#
#  実行方法（別のコードウィンドウから）:
#   leaderboard_run(Leaderboards.Maze, "maze_lb", 256)
#   ※ "maze_lb" はこのコードウィンドウの名前に合わせる
#
#  ゲーム内言語の制約に合わせて，クラス・ラムダ・内包表記・三項演算子・
#  名前付き引数・int()・continue は使っていない
# ============================================================

TARGET = 9863168     # 「開始時の所持金＋この額」まで集めたら終了
MAX_REUSE = 300      # 1つの迷路で宝を再配置できる回数の上限
DEBUG = False        # True にすると途中経過を出力ページに書き出す
MOVE_TICKS = 200     # move() 1回のtick
C_EXP_INIT = 150     # A*の1ノード展開あたりのtick（初期推定値．実行中に実測で更新）
BUDGET_SCALE = 1     # A*予算の倍率（1 = 最大節約手数と同じ時間まで計算してよい）
USE_ASTAR = False    # A*で近道を探すか．実機6回で A* は宝1個あたり 623 tick かかり，
                     # 短くなった歩数は 237 tick 分だけだった（差し引き約 386 tick の損）
START_CENTER = True  # 迷路を盤面中央から生成するか（False で (0,0) から）

DIRS = [North, East, South, West]
DX = {North: 0, East: 1, South: 0, West: -1}
DY = {North: 1, East: 0, South: -1, West: 0}
OPP = {North: South, South: North, East: West, West: East}


def sub_amount():
	return get_world_size() * 2 ** (num_unlocked(Unlocks.Mazes) - 1)


def make_step(n):
	# 方向 → セル番号(x*n+y)の増分
	return {North: 1, South: -1, East: n, West: -n}


def make_dirmap(n):
	# セル番号の増分 → 方向
	return {1: North, -1: South, n: East, -n: West}


def goto_open(tx, ty, n):
	# 壁が無い状態（迷路を作る前）に目的地へ直進する．
	# 盤面の端は反対側へ回り込むので，近いほうの向きを選ぶ
	dx = (tx - get_pos_x() + n) % n
	if dx * 2 <= n:
		d = East
		c = dx
	else:
		d = West
		c = n - dx
	for i in range(c):
		move(d)
	dy = (ty - get_pos_y() + n) % n
	if dy * 2 <= n:
		d = North
		c = dy
	else:
		d = South
		c = n - dy
	for i in range(c):
		move(d)


# ------------------------------------------------------------
# 迷路の全探索（DFS）
# ------------------------------------------------------------
#  並列探索：迷路は木なので，分岐の先の部分木どうしは交わらない．
#  よって分岐点で別ドローンに枝を任せれば，共有メモリなしで重複なく分担できる．
#  各ドローンは担当部分木の記録 rec[セル] = [親セル, 親→子の方向, 深さ] を
#  return し，生成元が wait_for で受け取って統合する．
# ------------------------------------------------------------
def open_dirs(back):
	# 来た方向以外で通れる方向 = 未探索の枝（木なので訪問済み判定は不要）
	res = []
	for d in DIRS:
		if d != back and can_move(d):
			res.append(d)
	return res


def make_explorer(cur, dep, d):
	def run():
		n = get_world_size()
		step = make_step(n)
		move(d)
		nc = cur + step[d]
		rec = dfs_branch(nc, dep + 1, OPP[d], n, step)
		rec[nc] = [cur, d, dep + 1]
		return rec
	return run


def try_spawn(pend, cur, dep, handles):
	# 枝が2本以上残っていて空きドローンがあれば，1本を残して他を任せる．
	# 任せた本数を返す
	cnt = 0
	while len(pend) > 1 and num_drones() < max_drones():
		d = pend.pop()
		h = spawn_drone(make_explorer(cur, dep, d))
		if h == None:
			pend.append(d)
			break
		handles.append(h)
		cnt += 1
	return cnt


def dfs_branch(cur, dep, back, n, step):
	rec = {}
	handles = []
	f_cell = [cur]
	f_back = [back]
	pend = open_dirs(back)
	try_spawn(pend, cur, dep, handles)
	f_pend = [pend]
	remaining = len(pend)   # 全フレームに残っている未探索の枝の数
	while True:
		top = f_pend[len(f_pend) - 1]
		if len(top) > 0:
			d = top.pop()
			remaining -= 1
			move(d)
			nc = cur + step[d]
			rec[nc] = [cur, d, dep + 1]
			cur = nc
			dep += 1
			p = open_dirs(OPP[d])
			try_spawn(p, cur, dep, handles)
			f_cell.append(cur)
			f_back.append(OPP[d])
			f_pend.append(p)
			remaining += len(p)
		else:
			if remaining == 0:
				break  # 最後の袋小路からは戻らない（無駄な帰り道を省く）
			b = f_back.pop()
			f_pend.pop()
			f_cell.pop()
			move(b)
			cur = f_cell[len(f_cell) - 1]
			dep -= 1
			# 戻った地点で，空いたドローンに残りの枝を任せる
			remaining -= try_spawn(f_pend[len(f_pend) - 1], cur, dep, handles)
	for h in handles:
		r = wait_for(h)
		for c in r:
			rec[c] = r[c]
	return rec


def explore(n):
	step = make_step(n)
	start = get_pos_x() * n + get_pos_y()
	rec = dfs_branch(start, 0, None, n, step)
	rec[start] = [-1, None, 0]
	parent = {}
	pdir = {}
	depth = {}
	children = {}
	for c in rec:
		children[c] = []
	for c in rec:
		r = rec[c]
		parent[c] = r[0]
		pdir[c] = r[1]
		depth[c] = r[2]
		if r[0] != -1:
			children[r[0]].append(c)
	if len(rec) < n * n:
		quick_print(len(rec))  # 取りこぼしがあれば表示
	return parent, pdir, depth, children


def build_nb(parent):
	# 隣接リスト nb[セル] = {隣セル: True}．最初は木の辺だけ
	nb = {}
	for c in parent:
		nb[c] = {}
	for c in parent:
		p = parent[c]
		if p != -1:
			nb[c][p] = True
			nb[p][c] = True
	return nb


# ------------------------------------------------------------
# 木の上の経路 a → b（LCA法）．計算は経路長に比例
# ------------------------------------------------------------
def path(a, b, parent, pdir, depth):
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
	for i in range(len(down) - 1, -1, -1):
		up.append(down[i])
	return up


def walk(dirs):
	for d in dirs:
		move(d)


# ------------------------------------------------------------
# 消えた壁の発見（未確認の方向だけ can_move で調べる．1回1tick）
# ------------------------------------------------------------
def try_edge(a, b, d, nb):
	if b in nb[a]:
		return 0
	if can_move(d):
		nb[a][b] = True
		nb[b][a] = True
		return 1
	return 0


def discover(cur, nb, n):
	x = cur // n
	y = cur % n
	found = 0
	if x < n - 1:
		found += try_edge(cur, cur + n, East, nb)
	if x > 0:
		found += try_edge(cur, cur - n, West, nb)
	if y < n - 1:
		found += try_edge(cur, cur + 1, North, nb)
	if y > 0:
		found += try_edge(cur, cur - 1, South, nb)
	return found


def walk_discover(dirs, cur, nb, step, n, t):
	# 非担当の移動中だけ使う．宝が動いたら中断して判断し直す
	found = 0
	for d in dirs:
		move(d)
		cur = cur + step[d]
		found += discover(cur, nb, n)
		if measure() != t:
			break
	return found


# ------------------------------------------------------------
# 二分ヒープ（heapq が無いので自作．キーと値を並列リストで持つ）
# ------------------------------------------------------------
def hpush(hk, hv, k, v):
	hk.append(k)
	hv.append(v)
	i = len(hk) - 1
	while i > 0:
		p = (i - 1) // 2
		if hk[p] <= hk[i]:
			break
		tmp = hk[p]
		hk[p] = hk[i]
		hk[i] = tmp
		tmp = hv[p]
		hv[p] = hv[i]
		hv[i] = tmp
		i = p


def hpop(hk, hv):
	top = hv[0]
	lk = hk.pop()
	lv = hv.pop()
	size = len(hk)
	if size > 0:
		hk[0] = lk
		hv[0] = lv
		i = 0
		while True:
			c = 2 * i + 1
			if c >= size:
				break
			r = c + 1
			if r < size and hk[r] < hk[c]:
				c = r
			if hk[i] <= hk[c]:
				break
			tmp = hk[i]
			hk[i] = hk[c]
			hk[c] = tmp
			tmp = hv[i]
			hv[i] = hv[c]
			hv[c] = tmp
			i = c
	return top


# ------------------------------------------------------------
# A*（ヒューリスティック = マンハッタン距離．許容的かつ無矛盾）
#  budget を超えて展開したら打ち切る．戻り値は [経路 or None, 展開数]
# ------------------------------------------------------------
def astar(s, t, nb, n, dirmap, budget):
	tx = t // n
	ty = t % n
	g = {s: 0}
	came = {s: -1}
	closed = {}
	hk = []
	hv = []
	hpush(hk, hv, (abs(s // n - tx) + abs(s % n - ty)) * 4096, s)
	exp = 0
	while len(hv) > 0:
		c = hpop(hk, hv)
		if not (c in closed):
			if c == t:
				rev = []
				while came[c] != -1:
					p = came[c]
					rev.append(dirmap[c - p])
					c = p
				out = []
				for i in range(len(rev) - 1, -1, -1):
					out.append(rev[i])
				return [out, exp]
			closed[c] = True
			exp += 1
			if exp > budget:
				return [None, exp]
			ng = g[c] + 1
			for m in nb[c]:
				if not (m in g) or ng < g[m]:
					g[m] = ng
					came[m] = c
					# f が小さい順，同点なら g が大きい（ゴールに近い）順
					hpush(hk, hv, (ng + abs(m // n - tx) + abs(m % n - ty)) * 4096 - ng, m)
	return [None, exp]


# ------------------------------------------------------------
# 待機地点と担当範囲
# ------------------------------------------------------------
def make_stations(n, D):
	a = 1
	while (a + 1) * (a + 1) <= D:
		a += 1
	while D % a != 0:
		a -= 1
	b = D // a
	st = []
	for i in range(a):
		for j in range(b):
			sx = (2 * i + 1) * n // (2 * a)
			sy = (2 * j + 1) * n // (2 * b)
			st.append(sx * n + sy)
	return st


def assign_owner(stations, parent, children):
	owner = {}
	queue = []
	for i in range(len(stations)):
		s = stations[i]
		if not (s in owner):
			owner[s] = i
			queue.append(s)
	head = 0
	while head < len(queue):
		c = queue[head]
		head += 1
		o = owner[c]
		for m in children[c]:
			if not (m in owner):
				owner[m] = o
				queue.append(m)
		p = parent[c]
		if p != -1 and not (p in owner):
			owner[p] = o
			queue.append(p)
	return owner


# ------------------------------------------------------------
# 各ドローンの仕事
# ------------------------------------------------------------
def worker(idx, home, parent, pdir, depth, nb, owner, per, target, g_start, stt):
	# stt（DEBUG 用の集計．呼び出し元へ返す）：
	#   [0 集めた宝, 1 歩いた歩数, 2 木の経路の長さの合計, 3 A*の回数, 4 A*のtick,
	#    5 A*で短くなった歩数, 6 経路計算のtick（A*を除く）,
	#    8 見つけた近道の数]（7 は未使用）
	n = get_world_size()
	sub = sub_amount()
	step = make_step(n)
	dirmap = make_dirmap(n)
	extra = 0            # 見つけた「木以外の辺」（消えた壁）の数
	c_exp = C_EXP_INIT   # A* 1展開あたりのtick（実測で更新）
	while True:
		if num_items(Items.Gold) >= target:
			return
		t = measure()
		if t == None:
			return       # 迷路が消えた（誰かが収穫した）→ 呼び出し元が作り直す
		tx, ty = t
		tk = tx * n + ty
		cur = get_pos_x() * n + get_pos_y()
		if owner[tk] == idx:
			t_seen = get_tick_count()
			plan = path(cur, tk, parent, pdir, depth)
			L = len(plan)
			if DEBUG:
				stt[6] += get_tick_count() - t_seen
				stt[2] += L
			h = abs(cur // n - tx) + abs(cur % n - ty)
			# 近道の可能性があり（ループ既知），かつ節約余地がある場合だけA*
			if USE_ASTAR and extra > 0 and L - h >= 2:
				budget = (L - h) * MOVE_TICKS * BUDGET_SCALE // c_exp
				t0 = get_tick_count()
				res = astar(cur, tk, nb, n, dirmap, budget)
				used = get_tick_count() - t0
				if res[1] > 0:
					c_exp = (c_exp * 3 + used / res[1]) / 4
				if DEBUG:
					stt[3] += 1
					stt[4] += used
				if res[0] != None and len(res[0]) < L:
					if DEBUG:
						stt[5] += L - len(res[0])
					plan = res[0]
			if DEBUG:
				stt[0] += 1
				stt[1] += len(plan)
			walk(plan)
			gold = num_items(Items.Gold)
			if gold + per >= target:
				harvest()   # 最後の1個 → 目標達成
				return
			# この迷路で何回集めたか（金は全ドローン共通なので数えられる）
			if (gold - g_start) / per >= MAX_REUSE - 0.5:
				harvest()   # 再配置の上限 → 収穫して迷路を作り直す
				return
			if num_items(Items.Weird_Substance) < sub:
				harvest()   # 物質切れ
				return
			use_item(Items.Weird_Substance, sub)
			if measure() == t:
				harvest()   # 宝が動かなかった（上限判定の予備）
				return
		elif cur != home:
			f = walk_discover(path(cur, home, parent, pdir, depth), cur, nb, step, n, t)
			extra += f
			if DEBUG:
				stt[8] += f


# spawn_drone へ引数を渡すためのクロージャ
def make_worker(idx, home, parent, pdir, depth, nb, owner, per, target, g_start):
	def run():
		stt = [0, 0, 0, 0, 0, 0, 0, 0, 0]
		worker(idx, home, parent, pdir, depth, nb, owner, per, target, g_start, stt)
		return stt
	return run


# ------------------------------------------------------------
# メイン
# ------------------------------------------------------------
def build_maze(n, sub):
	# 茂みを植えて迷路にする．成功したら True
	if get_entity_type() != None:
		harvest()
	if get_ground_type() != Grounds.Grassland:
		till()   # 畑（Soil）だと茂みを植えられないので草地に戻す
	if not plant(Entities.Bush):
		print("plant failed")
		return False
	use_item(Items.Weird_Substance, sub)
	e = get_entity_type()
	if e != Entities.Hedge and e != Entities.Treasure:
		print("maze not created")
		return False
	return True


def main():
	clear()
	n = get_world_size()
	sub = sub_amount()
	per = 0   # 宝1個あたりの金（1つ目の迷路で実測し，以後は使い回す）

	# 目標は「開始時の所持金からの増分」で判定する．
	# リーダーボードは所持金0から始まるので，TARGET とそのまま一致する
	goal = num_items(Items.Gold) + TARGET

	# 目標額に達するまで，迷路を作り直しながら収穫を繰り返す
	while num_items(Items.Gold) < goal:
		if num_items(Items.Weird_Substance) < sub:
			print("need", sub, "Weird_Substance")  # 煙で表示（見える）
			return

		# --- 迷路を作る ---
		if START_CENTER:
			# 起点を中央にすると，並列探索の律速となる「最深の枝」が短くなる（推定）
			goto_open(n // 2, n // 2, n)
		if not build_maze(n, sub):
			return
		if DEBUG:
			quick_print("maze built", get_tick_count())

		# --- 地図を作る ---
		parent, pdir, depth, children = explore(n)
		nb = build_nb(parent)
		quick_print(get_tick_count())  # 探索完了時のtick

		# --- 1個目は親ドローンが回収．ここで1回あたりの金を実測 ---
		g_start = num_items(Items.Gold)
		t = measure()
		tk = t[0] * n + t[1]
		walk(path(get_pos_x() * n + get_pos_y(), tk, parent, pdir, depth))
		use_item(Items.Weird_Substance, sub)
		if per <= 0:
			per = num_items(Items.Gold) - g_start
			if per <= 0:
				per = sub * n  # 推定値
			if DEBUG:
				quick_print("gold per treasure", per)

		# --- ドローンを配置して，この迷路を使い切るまで回収させる ---
		D = max_drones() - num_drones() + 1
		stations = make_stations(n, D)
		owner = assign_owner(stations, parent, children)

		handles = []
		for i in range(1, D):
			h = spawn_drone(make_worker(i, stations[i], parent, pdir, depth, nb, owner, per, goal, g_start))
			if h != None:
				handles.append(h)
		tot = [0, 0, 0, 0, 0, 0, 0, 0, 0]
		worker(0, stations[0], parent, pdir, depth, nb, owner, per, goal, g_start, tot)
		for h in handles:
			r = wait_for(h)   # 全員が戻るまで待ってから次の迷路へ
			if DEBUG:
				for i in range(9):
					tot[i] += r[i]
		if DEBUG:
			# 宝の数, 歩数, 木の経路長, A*回数, A*tick, A*短縮歩数, 経路計算tick, 待ち(未使用), 近道
			quick_print("stats", tot)

	quick_print(get_tick_count())  # 終了時のtick


main()
