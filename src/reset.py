# ============================================================
#  The Farmer Was Replaced  最速リセット（Leaderboards.Fastest_Reset）
#  1マスの農地から Unlocks.Leaderboard（骨 2,000,000 ＋ 金 1,000,000）まで自動で進める
#
#  方針（CLAUDE.md 5c 節．仕組みは実機の probe で確かめた）
#   ・決まった順番でアンロックを買う（SEQ）．費用は get_cost で読み，足りない品目を集める
#   ・品目ごとの集め方
#       干し草：草を収穫　木：市松に木，残りは茂み　にんじん：畑に植える（干し草と木を使う）
#       かぼちゃ：盤面全体を1つに合体させて収穫　サボテン：全マスを整列して連鎖収穫（n⁴ 個）
#       奇妙な物質：整列したサボテンを物質で感染させて収穫（取り分の半分が物質になる）
#       金：盤面いっぱいの迷路を1機で探索し，宝を再配置しながら集める
#       骨：恐竜で盤面を折り返して周り，尾を伸ばす（骨 ＝ 尾² × 2^(段階−1)）
#       Power：ひまわりを花びらの多い順に収穫（1本で8）．Power があると2倍速
#   ・複数機のときは列（または行）を分担する
#
#  実行方法（別のコードウィンドウから）:
#   leaderboard_run(Leaderboards.Fastest_Reset, "reset", 256)
#   試すとき：simulate("reset", {}, {}, {}, -1, 1000)
#
#  ゲーム内言語の制約に合わせて，クラス・ラムダ・内包表記・三項演算子・
#  名前付き引数・int()・continue・min/max/abs は使っていない
# ============================================================

DEBUG = True
POW_LOW = 30          # 1機あたりの Power がこれを下回ったらひまわりで補う
WATER_KEEP = 4        # 水はこの数より多く持っているときだけ使う

SEQ = [
	Unlocks.Speed, Unlocks.Expand, Unlocks.Plant, Unlocks.Expand, Unlocks.Speed, Unlocks.Carrots,
	Unlocks.Expand, Unlocks.Trees, Unlocks.Expand, Unlocks.Watering, Unlocks.Speed, Unlocks.Grass,
	Unlocks.Grass, Unlocks.Trees, Unlocks.Carrots, Unlocks.Sunflowers, Unlocks.Carrots, Unlocks.Speed,
	Unlocks.Speed, Unlocks.Hats, Unlocks.Pumpkins, Unlocks.Trees, Unlocks.Grass, Unlocks.Expand,
	Unlocks.Pumpkins, Unlocks.Watering, Unlocks.Expand, Unlocks.Cactus, Unlocks.Fertilizer,
	Unlocks.Mazes, Unlocks.Mazes, Unlocks.Mazes, Unlocks.Megafarm, Unlocks.Megafarm, Unlocks.Megafarm,
	Unlocks.Pumpkins, Unlocks.Carrots, Unlocks.Trees, Unlocks.Expand, Unlocks.Cactus, Unlocks.Mazes,
	Unlocks.Megafarm, Unlocks.Dinosaurs, Unlocks.Dinosaurs, Unlocks.Dinosaurs, Unlocks.Dinosaurs,
	Unlocks.Mazes, Unlocks.Dinosaurs, Unlocks.Leaderboard
]
START = 0             # SEQ のこの番号から始める（試験用．通常は 0）
STOP = 999            # SEQ のこの番号の手前で止める（試験用）

DIRS = [North, East, South, West]
DXS = [0, 1, 0, -1]
DYS = [1, 0, -1, 0]

def mv(d):
	return move(d)


def goto(tx, ty):
	n = get_world_size()
	if n < 2:
		return
	dx = (tx - get_pos_x()) % n
	if dx * 2 <= n:
		for i in range(dx):
			mv(East)
	else:
		for i in range(n - dx):
			mv(West)
	dy = (ty - get_pos_y()) % n
	if dy * 2 <= n:
		for i in range(dy):
			mv(North)
	else:
		for i in range(n - dy):
			mv(South)


def lvl(u):
	return num_unlocked(u)


def mul(u):
	k = num_unlocked(u)
	if k < 1:
		return 1
	return 2 ** (k - 1)


def drones():
	n = get_world_size()
	d = max_drones()
	if d > n:
		d = n
	return d


# ------------------------------------------------------------
# 並列：job(i, D) が返す関数を，i 列目（または行）から始めて D 本おきに担当させる
# ------------------------------------------------------------
def par(job, D, dirn):
	hs = []
	left = []
	i = D - 1
	while i >= 1:
		h = spawn_drone(shifted(job, i, D, dirn))
		if h == None:
			left.append(i)
		else:
			hs.append(h)
		i -= 1
	out = []
	out.append(job(0, D)())
	for i in left:
		sx = get_pos_x()
		sy = get_pos_y()
		for k in range(i):
			mv(dirn)
		out.append(job(i, D)())
		goto(sx, sy)
	for h in hs:
		out.append(wait_for(h))
	return out


def shifted(job, i, D, dirn):
	def run():
		for k in range(i):
			mv(dirn)
		return job(i, D)()
	return run


# ------------------------------------------------------------
# 1マスの作業
# ------------------------------------------------------------
def water():
	if get_water() < 0.5:
		if num_items(Items.Water) > WATER_KEEP:
			use_item(Items.Water)


def job_hay(wat):
	if get_ground_type() == Grounds.Soil:
		till()
	if can_harvest():
		harvest()


def job_wood(wat):
	e = get_entity_type()
	if e == Entities.Tree or e == Entities.Bush:
		if not can_harvest():
			return
		harvest()
	elif e != None:
		harvest()
	if (get_pos_x() + get_pos_y()) % 2 == 0 and num_unlocked(Unlocks.Trees) > 0:
		plant(Entities.Tree)
	else:
		plant(Entities.Bush)
	if wat:
		water()


def job_carrot(wat):
	if get_ground_type() != Grounds.Soil:
		till()
	e = get_entity_type()
	if e == Entities.Carrot:
		if not can_harvest():
			return
		harvest()
	elif e != None:
		harvest()
	plant(Entities.Carrot)
	if wat:
		water()


def do_job(kind, wat):
	if kind == 0:
		job_hay(wat)
	elif kind == 1:
		job_wood(wat)
	else:
		job_carrot(wat)


# 列を回り続けて item が target に届いたら止まる
def cols_job(kind, item, target):
	def mk(i, D):
		def run():
			n = get_world_size()
			wat = num_unlocked(Unlocks.Watering) > 0
			cols = []
			c = i
			while c < n:
				cols.append(c)
				c += D
			while num_items(item) < target:
				for c in cols:
					goto(c, get_pos_y())
					for y in range(n):
						do_job(kind, wat)
						mv(North)
					if num_items(item) >= target:
						return 0
			return 0
		return run
	return mk


def farm_cols(kind, item, target):
	goto(0, 0)
	par(cols_job(kind, item, target), drones(), East)


# ------------------------------------------------------------
# かぼちゃ：盤面全体を合体させて (0,0) で収穫
# ------------------------------------------------------------
def pump_job(first):
	def mk(i, D):
		def run():
			n = get_world_size()
			wat = num_unlocked(Unlocks.Watering) > 0
			bad = 0
			c = i
			while c < n:
				goto(c, 0)
				for y in range(n):
					if first and get_ground_type() != Grounds.Soil:
						till()
					e = get_entity_type()
					if e != Entities.Pumpkin:
						if e != None:
							harvest()
						plant(Entities.Pumpkin)
						bad += 1
						if wat:
							water()
					elif not can_harvest():
						bad += 1
					mv(North)
				c += D
			return bad
		return run
	return mk


def pumpkin_cycle():
	D = drones()
	goto(0, 0)
	par(pump_job(True), D, East)
	k = 0
	while k < 60:
		goto(0, 0)
		res = par(pump_job(False), D, East)
		s = 0
		for r in res:
			s += r
		if s == 0:
			k = 99
		k += 1
	goto(0, 0)
	harvest()


def pump_yield():
	n = get_world_size()
	if n >= 6:
		return 6 * n * n * mul(Unlocks.Pumpkins)
	return n * n * n * mul(Unlocks.Pumpkins)


# ------------------------------------------------------------
# サボテン：植えて列・行を整列し，(0,0) で連鎖収穫
# ------------------------------------------------------------
def sort_line(a, fwd, back):
	# ドローンは線の添字 0 にいる．a は値．隣どうしの交換で昇順にする
	n = len(a)
	p = 0
	lo = 0
	hi = n - 1
	while lo < hi:
		while p < lo:
			mv(fwd)
			p += 1
		while p > lo:
			mv(back)
			p -= 1
		last = lo
		i = lo
		while i < hi:
			if a[i] > a[i + 1]:
				swap(fwd)
				t = a[i]
				a[i] = a[i + 1]
				a[i + 1] = t
				last = i
			mv(fwd)
			p += 1
			i += 1
		hi = last
		if lo < hi:
			while p > hi:
				mv(back)
				p -= 1
			last = hi
			i = hi
			while i > lo:
				if a[i - 1] > a[i]:
					swap(back)
					t = a[i]
					a[i] = a[i - 1]
					a[i - 1] = t
					last = i
				mv(back)
				p -= 1
				i -= 1
			lo = last
	while p > 0:
		mv(back)
		p -= 1


def cac_col_job(i, D):
	def run():
		n = get_world_size()
		c = i
		while c < n:
			goto(c, 0)
			a = []
			for y in range(n):
				if get_ground_type() != Grounds.Soil:
					till()
				e = get_entity_type()
				if e != None:
					harvest()
				plant(Entities.Cactus)
				a.append(measure())
				mv(North)
			sort_line(a, North, South)
			c += D
		return 0
	return run


def cac_row_job(i, D):
	def run():
		n = get_world_size()
		r = i
		while r < n:
			goto(0, r)
			a = []
			for x in range(n):
				a.append(measure())
				mv(East)
			sort_line(a, East, West)
			r += D
		return 0
	return run


def infect_job(i, D):
	def run():
		n = get_world_size()
		c = i
		while c < n:
			goto(c, 0)
			for y in range(n):
				if (c + 2 * y) % 5 == 0:
					use_item(Items.Weird_Substance)
				mv(North)
			c += D
		return 0
	return run


def cactus_round(mode):
	# mode 0：普通．1：肥料で1マスだけ感染．2：物質で全体を感染
	D = drones()
	goto(0, 0)
	par(cac_col_job, D, East)
	goto(0, 0)
	par(cac_row_job, D, North)
	goto(0, 0)
	if mode == 1:
		while num_items(Items.Fertilizer) < 1:
			do_nothing()
		use_item(Items.Fertilizer)
	elif mode == 2:
		par(infect_job, D, East)
		goto(0, 0)
	while not can_harvest():
		do_nothing()
	harvest()


def do_nothing():
	a = 0


# ------------------------------------------------------------
# Power：ひまわりを花びらの多い順に収穫する
# ------------------------------------------------------------
def sun_job(i, D):
	def run():
		n = get_world_size()
		c = i
		while c < n:
			goto(c, 0)
			for y in range(n):
				if get_ground_type() != Grounds.Soil:
					till()
				e = get_entity_type()
				if e != None:
					harvest()
				plant(Entities.Sunflower)
				mv(North)
			c += D
		return 0
	return run


def power_round():
	n = get_world_size()
	if n * n < 12:
		return
	sc = get_cost(Entities.Sunflower)
	for it in sc:
		if num_items(it) < n * n * sc[it] * 2:
			return
	if num_items(Items.Carrot) < n * n * 2:
		return
	goto(0, 0)
	par(sun_job, drones(), East)
	goto(0, 0)
	b = []
	for v in range(16):
		b.append([])
	for x in range(n):
		goto(x, 0)
		for y in range(n):
			while not can_harvest():
				do_nothing()
			p = measure()
			if p != None:
				b[p].append(x * n + y)
			mv(North)
	left = n * n
	v = 15
	while v >= 0:
		for k in b[v]:
			if left > 10:
				goto(k // n, k % n)
				harvest()
				left -= 1
		v -= 1


def maybe_power():
	if num_unlocked(Unlocks.Sunflowers) < 1:
		return
	if num_items(Items.Power) < POW_LOW * drones():
		power_round()


# ------------------------------------------------------------
# 金：盤面いっぱいの迷路．1機で全探索して木を覚え，宝を再配置しながら取る
# ------------------------------------------------------------
def explore(n, x0, y0, b):
	# 今いるマスから DFS（迷路は x0..x0+b-1, y0..y0+b-1）．pa ＝ 親セル，pd ＝ 親から来た向き，dep ＝ 深さ
	start = get_pos_x() * n + get_pos_y()
	pa = {}
	pd = {}
	dep = {}
	nx_ = {}
	pa[start] = -1
	pd[start] = -1
	dep[start] = 0
	nx_[start] = 0
	st = [start]
	while len(st) > 0:
		cur = st[len(st) - 1]
		k = nx_[cur]
		if k >= 4:
			st.pop()
			if len(st) > 0:
				mv(DIRS[(pd[cur] + 2) % 4])
		else:
			nx_[cur] = k + 1
			cx = cur // n
			cy = cur % n
			tx = cx + DXS[k]
			ty = cy + DYS[k]
			if tx >= x0 and ty >= y0 and tx < x0 + b and ty < y0 + b:
				t = tx * n + ty
				if not (t in pa):
					if mv(DIRS[k]):
						pa[t] = cur
						pd[t] = k
						dep[t] = dep[cur] + 1
						nx_[t] = 0
						st.append(t)
	return [pa, pd, dep]


def walk_tree(tr, frm, to):
	pa = tr[0]
	pd = tr[1]
	dep = tr[2]
	up = []
	down = []
	a = frm
	b = to
	while dep[a] > dep[b]:
		up.append((pd[a] + 2) % 4)
		a = pa[a]
	while dep[b] > dep[a]:
		down.append(pd[b])
		b = pa[b]
	while a != b:
		up.append((pd[a] + 2) % 4)
		a = pa[a]
		down.append(pd[b])
		b = pa[b]
	for d in up:
		mv(DIRS[d])
	i = len(down) - 1
	while i >= 0:
		mv(DIRS[down[i]])
		i -= 1


def maze_block(x0, y0, b, target, want):
	# 盤面の b×b の区画 (x0,y0) に迷路を作り，金が target に届くまで宝を取る．物質が尽きたら止まる
	# 迷路ができると外から通れないので，全機が自分の区画の中心に着くまで待ってから作る：
	# 機数が want に達する（全機を生成し終える）まで待ち，さらに盤面を1周する時間だけ till で待つ
	def run():
		n = get_world_size()
		amt = b * mul(Unlocks.Mazes)
		cx = x0 + b // 2
		cy = y0 + b // 2
		goto(cx, cy)
		k = 0
		while num_drones() < want and k < 3000:
			k += 1
		for i in range(2 * (n // 2 + 1)):
			till()
		while num_items(Items.Gold) < target and num_items(Items.Weird_Substance) >= amt:
			goto(cx, cy)
			if get_entity_type() != None:
				harvest()
			if get_ground_type() == Grounds.Soil:
				till()
			plant(Entities.Bush)
			if not use_item(Items.Weird_Substance, amt):
				return 0
			tr = explore(n, x0, y0, b)
			reuse = 0
			going = True
			while going:
				t = measure()
				if t == None:
					going = False
				else:
					tx, ty = t
					walk_tree(tr, get_pos_x() * n + get_pos_y(), tx * n + ty)
					if num_items(Items.Gold) < target and reuse < 299 and num_items(Items.Weird_Substance) >= amt:
						if use_item(Items.Weird_Substance, amt):
							reuse += 1
						else:
							harvest()
							going = False
					else:
						harvest()
						going = False
		return 0
	return run


def farm_gold(target):
	if DEBUG:
		quick_print("gold start", num_items(Items.Gold), target)
	n = get_world_size()
	D = max_drones()
	# 区画の一辺 b：区画の数 (n//b)² が機数を超えない最小の b（3 以上）
	b = 3
	while (n // b) * (n // b) > D:
		b += 1
	if b > n:
		b = n
	k = n // b
	while num_items(Items.Gold) < target:
		short = target - num_items(Items.Gold)
		gain = b * b * mul(Unlocks.Mazes)
		sub = (short // gain + 2 * k * k) * b * mul(Unlocks.Mazes)
		need(Items.Weird_Substance, sub)
		clear()
		goto(0, 0)
		hs = []
		for i in range(k):
			for j in range(k):
				if i + j > 0:
					h = spawn_drone(maze_block(i * b, j * b, b, target, k * k))
					if h != None:
						hs.append(h)
		maze_block(0, 0, b, target, k * k)()
		for h in hs:
			wait_for(h)


# ------------------------------------------------------------
# 骨：恐竜で (0,0) から折り返しの閉路を回り，尾を伸ばす
# ------------------------------------------------------------
def ordv(x, y, n):
	# 折り返し閉路（行0を東へ，行1..n-1 を折り返し，列0を南へ戻る）の上の順番
	if y == 0:
		return x
	if x == 0:
		return n * n - y
	b = n + (y - 1) * (n - 1)
	if y % 2 == 1:
		return b + n - 1 - x
	return b + x - 1


def cyc_dir(x, y, rowe, n):
	if x == 0 and y > 0:
		return South
	if rowe:
		if x < n - 1:
			return East
		return North
	if x > 1:
		return West
	if y < n - 1:
		return North
	return West


def snake_run(n, c0, cost, L):
	# src/snake.py の走り方（前半は北への近道，中間で閉路に戻し，後半は周回）．尾が L に届いたら止まる
	N = n * n
	nm1 = n - 1
	n2m1 = 2 * n - 1
	cut = N // 2
	if cut > 240:
		cut = 240
	x = 0
	y = 0
	rowe = True
	h = 0
	a = 0
	q = {}
	q[0] = 0
	qh = 1
	qt = 0
	known = False
	cc = num_items(Items.Cactus)
	m = measure()
	if m != None:
		ax, ay = m
		a = ordv(ax, ay, n)
		known = True
	steps = 0
	while qh - qt <= cut:
		t = q[qt]
		d_tail = (t - h) % N
		if d_tail == 0:
			d_tail = N
		if x == 0 and y > 0:
			d = South
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
			d = West
		dc = 1
		if known and y < nm1 and x > 0:
			if rowe:
				jump = n2m1 - 2 * x
			else:
				jump = 2 * x - 1
			if jump > 1 and jump + 2 < d_tail and jump <= (a - h) % N:
				d = North
				dc = jump
		if not move(d):
			return
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
		# リンゴを食べると次のリンゴが出てサボテンが減る．それで食べたかを知る（食べた1歩は尾が縮まない）
		c2 = num_items(Items.Cactus)
		if c2 < cc:
			cc = c2
			m = measure()
			if m != None:
				ax, ay = m
				a = ordv(ax, ay, n)
				known = True
			if (c0 - c2) // cost - 1 >= L:
				return
		else:
			q.pop(qt)
			qt += 1
		steps += 1
	# 中間：経路どおりに (0,0) へ戻す
	need2 = 2 * (qh - qt)
	steps = 0
	while steps < need2 or x != 0 or y != 0:
		d = cyc_dir(x, y, rowe, n)
		if not move(d):
			return
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
		if steps > 3 * N:
			return
		if steps % 16 == 0:
			if (c0 - num_items(Items.Cactus)) // cost - 1 >= L:
				return
	# 後半：1周ずつ回る．1行ごとに尾の長さを確かめる
	while True:
		for i in range(n - 1):
			move(East)
		d = West
		for k in range(n - 1):
			if not move(North):
				return
			for i in range(n - 2):
				move(d)
			if d == West:
				d = East
			else:
				d = West
			if (c0 - num_items(Items.Cactus)) // cost - 1 >= L or num_items(Items.Cactus) < cost:
				return
		move(West)
		for i in range(n - 1):
			move(South)


def farm_bones(target):
	if DEBUG:
		quick_print("bones start", num_items(Items.Bone), target)
	n = get_world_size()
	m = mul(Unlocks.Dinosaurs)
	cost = 2 * m
	while num_items(Items.Bone) < target:
		short = target - num_items(Items.Bone)
		L = 1
		while L * L * m < short and L < n * n - 2:
			L += 1
		need(Items.Cactus, (L + 2) * cost)
		maybe_power()
		clear()
		goto(0, 0)
		c0 = num_items(Items.Cactus)
		change_hat(Hats.Dinosaur_Hat)
		snake_run(n, c0, cost, L)
		change_hat(Hats.Straw_Hat)
		if DEBUG:
			quick_print("bones run", L, num_items(Items.Bone))
		clear()


# ------------------------------------------------------------
# 必要な数を集める
# ------------------------------------------------------------
def need(item, T):
	while num_items(item) < T:
		n = get_world_size()
		if item == Items.Hay:
			farm_cols(0, item, T)
		elif item == Items.Wood:
			farm_cols(1, item, T)
		elif item == Items.Carrot:
			short = T - num_items(item) + n * n * mul(Unlocks.Carrots)
			need(Items.Hay, num_items(Items.Hay) + short)
			need(Items.Wood, num_items(Items.Wood) + short)
			maybe_power()
			farm_cols(2, item, T)
		elif item == Items.Pumpkin:
			short = T - num_items(item)
			cyc = short // pump_yield() + 1
			need(Items.Carrot, num_items(Items.Carrot) + cyc * n * n * mul(Unlocks.Pumpkins) * 2)
			maybe_power()
			k = 0
			while k < cyc and num_items(item) < T:
				if num_items(Items.Carrot) < n * n * mul(Unlocks.Pumpkins) * 2:
					need(Items.Carrot, n * n * mul(Unlocks.Pumpkins) * 3)
				pumpkin_cycle()
				k += 1
		elif item == Items.Cactus:
			cac_round(0, item, T)
		elif item == Items.Weird_Substance:
			if num_items(item) < n * n // 5 + 2:
				cac_round(1, item, T)
			else:
				cac_round(2, item, T)
		elif item == Items.Gold:
			farm_gold(T)
		elif item == Items.Bone:
			farm_bones(T)
		else:
			return


def cac_round(mode, item, T):
	n = get_world_size()
	pc = n * n * 2 * mul(Unlocks.Cactus)
	if num_items(Items.Pumpkin) < pc:
		need(Items.Pumpkin, pc * 2)
	maybe_power()
	cactus_round(mode)


TIER = {}


def tier(it):
	if it == Items.Gold:
		return 7
	if it == Items.Bone:
		return 6
	if it == Items.Weird_Substance:
		return 5
	if it == Items.Cactus:
		return 4
	if it == Items.Pumpkin:
		return 3
	if it == Items.Carrot:
		return 2
	return 1


def buy(u):
	tries = 0
	while tries < 20:
		cost = get_cost(u)
		for t in [7, 6, 5, 4, 3, 2, 1]:
			for it in cost:
				if tier(it) == t:
					need(it, cost[it])
		if unlock(u):
			return True
		tries += 1
	return False


def main():
	k = START
	while k < len(SEQ) and k < STOP:
		u = SEQ[k]
		buy(u)
		if DEBUG:
			quick_print(k, u, num_unlocked(u), get_world_size(), max_drones())
		k += 1
	quick_print("done")


main()
