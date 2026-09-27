# ============================================================
#  The Farmer Was Replaced  かぼちゃ（Leaderboards.Pumpkins：200000000 個を最速で集める）
#
#  仕様（CLAUDE.md 5b 節．実機の小実験で確認）
#   ・耕した土に植える（にんじん512個）．成長は一様分布 [約1500, 約23000] tick，水の量 w で 1/(1+4w) 倍
#   ・育ち切った時点で約22%が枯れる（Entities.Dead_Pumpkin）．上から植え直せる
#   ・育ち切った生きたかぼちゃが正方形にそろうと合体する．n×n の収穫は 1マスあたり min(n,6)×512 個
#   ・先にできた塊が大きな正方形から一部はみ出していると，その正方形はできない（merge probe2）．
#     盤面の一部ずつ植え直し続けると小さな塊が固まって大きくならない（シミュレータ）
#   ・measure() はかぼちゃの ID（合体したマスは同じ ID）
#   ・水は時間とともに溜まる（LB で1タンク／約237 tick）．1タンクで地面の水 +0.25．植えても減らない
#
#  方針：盤面全体を1つのかぼちゃ（32×32，1回 3,145,728 個）にそろえて収穫することを64回くり返す
#   32機がそれぞれ1列を受け持つ．1回ぶん（1周期）の流れ：
#    A 列の端から端へ，全マスに（水を入れて）植える
#    B 逆向きに戻りながら各マスを調べる．枯れていれば植え直す．育ち切っていれば済みにする
#    C 済みでないマスだけを，端から端へ往復しながら調べ直す（全部済みになるまで）
#    D 列0の機体は，足元と西隣（回り込みで列31）の ID が同じになったら盤面全体が1つに
#      まとまったと分かるので収穫する．他の機体は収穫まで東隣の列を往復し，枯れを植え直して
#      遅い列を手伝う（収穫は全マスが生きて育ち切れば起きるので，手伝っても害はない）
#   収穫があったこと（かぼちゃの所持数が増えたこと）を見たら，どの段階にいても次の周期を始める
#   （B・C の途中で収穫されると，済みにしたマスが空いているのに気づかず止まる．シミュレータで発生）
#   目標額に届いたら全機が止まる
#
#  実行方法（別のコードウィンドウから）:
#   leaderboard_run(Leaderboards.Pumpkins, "pumpkin", 256)
#
#  ゲーム内言語の制約に合わせて，クラス・ラムダ・内包表記・三項演算子・
#  名前付き引数・int()・continue は使っていない
# ============================================================

TARGET = 200000000   # 「開始時の所持数＋この数」まで集めたら終了
WATER_TARGET = 1.0   # 地面の水をこの量まで上げる（溜まっているぶんだけ）
WATER_PER_PLANT = 2  # 1回植えるときに使う水の上限（タンク）．少しずつ全マスに行き渡らせる
HELP = True          # 自分の列が済んだら，収穫まで東隣の列を往復して枯れを植え直す（列0の機体は除く）
FERT_AFTER = 30000   # 周期の始めからこの tick を過ぎても育っていない未完のマスには肥料を使う．
                     # 肥料を使うとすぐ育ち切るが，そのマスの収穫の半分（1,536個）が奇妙な物質になる
                     # （fert probe：合体したかぼちゃでも減るのはそのマスの分だけ）．LB では肥料は
                     # 約8,600 tick に1個しか溜まらないので，周期の終わりに残った遅いマスにだけ使う
WATER_RESERVE = 32   # 所持がこの数以上のときだけ水を使う．32機が同時に使っても
                     # 足りなくならないので「水が足りない」警告が出ない
DEBUG = False


def plant_here():
	if get_ground_type() != Grounds.Soil:
		till()
	k = 0
	while k < WATER_PER_PLANT and get_water() < WATER_TARGET - 0.1:
		if num_items(Items.Water) < WATER_RESERVE:
			k = WATER_PER_PLANT
		else:
			use_item(Items.Water)
			k += 1
	plant(Entities.Pumpkin)


def step_to(y, ty):
	# 列の中で y から ty へ動く（端で回り込まない）．戻り値：新しい y
	while y < ty:
		move(North)
		y += 1
	while y > ty:
		move(South)
		y -= 1
	return y


def check_here():
	# 足元を調べる．育ち切っていれば True．枯れていたり空なら植え直して False
	e = get_entity_type()
	if e == Entities.Pumpkin:
		if can_harvest():
			return True
		return False
	plant_here()
	return False


def reverse(lst):
	out = []
	i = len(lst) - 1
	while i >= 0:
		out.append(lst[i])
		i -= 1
	return out


def tend(n, x, goal):
	# 収穫があったかどうかは，かぼちゃの所持数が周期の始めより増えたかで知る（全機に見える）
	y = 0
	cycles = 0
	while num_items(Items.Pumpkin) < goal:
		p0 = num_items(Items.Pumpkin)
		t0 = get_tick_count()
		# 端にいなければ近い方の端へ（収穫で途中から始め直すとき）
		if y != 0 and y != n - 1:
			if y * 2 < n:
				y = step_to(y, 0)
			else:
				y = step_to(y, n - 1)
		# --- A：いまいる端から反対の端まで植える ---
		a = 0
		b = n - 1
		dy = 1
		if y != 0:
			a = n - 1
			b = 0
			dy = -1
		k = a
		while True:
			if get_entity_type() != Entities.Pumpkin:
				plant_here()
			if k == b:
				break
			k += dy
			y = step_to(y, k)
		# --- B：戻りながら調べる（todo は戻る向きの順に並ぶ）---
		todo = []
		k = b
		fresh = True
		while fresh:
			if not check_here():
				todo.append(k)
			if k == a:
				break
			k -= dy
			y = step_to(y, k)
			if num_items(Items.Pumpkin) != p0:
				fresh = False
		# --- C：済みでないマスだけを，いまいる側から往復しながら調べる ---
		while fresh and len(todo) > 0:
			first = todo[0]
			last = todo[len(todo) - 1]
			order = todo
			if abs(y - last) < abs(y - first):
				order = reverse(todo)
			nt = []
			for k in order:
				if fresh:
					y = step_to(y, k)
					if not check_here():
						if get_entity_type() == Entities.Pumpkin:
							if get_tick_count() - t0 > FERT_AFTER:
								if num_items(Items.Fertilizer) >= 1:
									use_item(Items.Fertilizer)
						nt.append(k)
					if num_items(Items.Pumpkin) != p0:
						fresh = False
			todo = nt
		# --- D：収穫を待つ ---
		if fresh and HELP and x != 0:
			# 東隣の列を往復して，枯れや空きを植え直す（持ち主の列の遅れを手伝う）
			move(East)
			hd = 1
			if y * 2 >= n:
				hd = -1
			while num_items(Items.Pumpkin) == p0:
				if get_entity_type() != Entities.Pumpkin:
					plant_here()
				if y + hd < 0 or y + hd >= n:
					hd = -hd
				if hd > 0:
					move(North)
				else:
					move(South)
				y += hd
			move(West)
		elif fresh:
			if y * 2 < n:
				y = step_to(y, 0)
			else:
				y = step_to(y, n - 1)
		while num_items(Items.Pumpkin) == p0:
			if x == 0:
				m = measure()
				if m != None and m == measure(West):
					harvest()
		cycles += 1
	return cycles


def worker(dx, dm, n, goal, x):
	def run():
		for i in range(dx):
			move(dm)
		return tend(n, x, goal)
	return run


# 列の配り方（サボテンと同じ．盤面の端で回り込む）：
#   親は列0．東の配り役が列1から列 2..m を遠い順に生成し，親は西へ回り込んで列 n-1..n-L を生成する
def leader(n, m, goal):
	def run():
		move(East)
		d = m - 1
		while d > 0:
			spawn_drone(worker(d, East, n, goal, 1 + d))
			d -= 1
		return tend(n, 1, goal)
	return run


def main():
	clear()
	n = get_world_size()
	goal = num_items(Items.Pumpkin) + TARGET
	L = (n - 1) // 2
	hs = []
	h = spawn_drone(leader(n, n - 1 - L, goal))
	if h != None:
		hs.append(h)
	d = L
	while d > 0:
		h = spawn_drone(worker(d, West, n, goal, n - d))
		if h != None:
			hs.append(h)
		d -= 1
	c = tend(n, 0, goal)
	for h in hs:
		wait_for(h)
	if DEBUG:
		quick_print("cycles", c)
	quick_print(get_tick_count())


main()
