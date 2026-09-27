# ============================================================
#  The Farmer Was Replaced  かぼちゃ（Leaderboards.Pumpkins：200000000 個を最速で集める）
#
#  仕様（CLAUDE.md 5b 節．実機の小実験で確認）
#   ・耕した土に植える（にんじん512個）．成長は一様分布 [約1500, 約23000] tick，水の量 w で 1/(1+4w) 倍
#   ・育ち切った時点で約22%が枯れる（Entities.Dead_Pumpkin）．上から植え直せる
#   ・育ち切った生きたかぼちゃが正方形にそろうと合体する．n×n の収穫は 1マスあたり min(n,6)×512 個
#     （n>=6 ならどの大きさでも1マスあたり 3072 個）．枯れたマスがあると小さな塊にしかならない
#   ・measure() はかぼちゃの ID を返す（合体したマスは同じ ID）
#   ・水は時間とともに溜まる（LB で1タンク／約237 tick）．1タンクで地面の水 +0.25．植えても減らない
#
#  方針
#   32機がそれぞれ1列を受け持ち，列を往復し続ける．各マスで
#    ・空き・草・枯れ → （草地なら耕し）水を目標まで入れて植える
#    ・育ち切ったかぼちゃ → ID を記録し，列の中で同じ ID が MIN_SIDE マス以上続いていれば収穫
#      （縦に6マス同じ ID なら，そのかぼちゃは 6×6 以上なので，1マスあたりの収穫量は最大）
#      同じ ID のまま STALE tick たっても大きくならない塊は，小さくても収穫する（保険）
#   目標額に届いたら全機が止まる
#
#  実行方法（別のコードウィンドウから）:
#   leaderboard_run(Leaderboards.Pumpkins, "pumpkin", 256)
#
#  ゲーム内言語の制約に合わせて，クラス・ラムダ・内包表記・三項演算子・
#  名前付き引数・int()・continue は使っていない
# ============================================================

TARGET = 200000000   # 「開始時の所持数＋この数」まで集めたら終了
MIN_SIDE = 6         # 縦にこのマス数だけ同じ ID が続いたら収穫する
WATER_TARGET = 1.0   # 植えるときに地面の水をこの量まで上げる（溜まっているぶんだけ）
STALE = 60000        # 育ち切ってからこの tick たっても MIN_SIDE にならない塊は，小さくても収穫する
                     # （合体の細かい規則は不明なので，小さな塊が固まって止まらないための保険）
DEBUG = False


def plant_here():
	if get_ground_type() != Grounds.Soil:
		till()
	k = 0
	while k < 4 and get_water() < WATER_TARGET - 0.1:
		if num_items(Items.Water) < 1:
			k = 4
		else:
			use_item(Items.Water)
			k += 1
	plant(Entities.Pumpkin)


def run_of(ids, y, m, n):
	# 列の記録 ids で，y を含み ID が m のマスが縦に何マス続くか
	r = 1
	k = y - 1
	while k >= 0 and ids[k] == m:
		r += 1
		k -= 1
	k = y + 1
	while k < n and ids[k] == m:
		r += 1
		k += 1
	return r


def tend(n, goal):
	# 自分の列を往復し続ける（ドローンは列の y=0 にいること）
	ids = []
	since = []           # そのマスで今の ID を最初に見た tick
	for i in range(n):
		ids.append(None)
		since.append(0)
	y = 0
	d = North
	harvested = 0
	while num_items(Items.Pumpkin) < goal:
		e = get_entity_type()
		if e == Entities.Pumpkin:
			if can_harvest():
				m = measure()
				if ids[y] != m:
					since[y] = get_tick_count()
				ids[y] = m
				if run_of(ids, y, m, n) >= MIN_SIDE or get_tick_count() - since[y] > STALE:
					harvest()
					harvested += 1
					ids[y] = None
					plant_here()
			else:
				ids[y] = None
		else:
			ids[y] = None
			plant_here()
		if y == n - 1:
			d = South
		elif y == 0:
			d = North
		move(d)
		if d == North:
			y += 1
		else:
			y -= 1
	return harvested


def worker(dx, dm, n, goal):
	def run():
		for i in range(dx):
			move(dm)
		return tend(n, goal)
	return run


# 列の配り方（サボテンと同じ．盤面の端で回り込む）：
#   親は列0．東の配り役が列1から列 2..m を遠い順に生成し，親は西へ回り込んで列 n-1..n-L を生成する
def leader(n, m, goal):
	def run():
		move(East)
		d = m - 1
		hs = []
		while d > 0:
			h = spawn_drone(worker(d, East, n, goal))
			if h != None:
				hs.append(h)
			d -= 1
		return tend(n, goal)
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
		h = spawn_drone(worker(d, West, n, goal))
		if h != None:
			hs.append(h)
		d -= 1
	c = tend(n, goal)
	for h in hs:
		wait_for(h)
	if DEBUG:
		quick_print("parent harvests", c)
	quick_print(get_tick_count())


main()
