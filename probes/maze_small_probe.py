# 小さな迷路を並べて使えるかを確かめる実験（通常プレイの空いている畑で実行）
#   奇妙な物質を「m * 2**(段階-1)」だけ使うと m x m の迷路になるか（推定）を調べる．
#   調べること
#     T1 大きさと位置：茂みの位置に対して，迷路がどの範囲にできるか（DFS で全マスを歩いて数える）
#     T2 金：宝の上で use_item したとき・収穫したときに増える金（m*m*2**(段階-1) か）
#     T3 2つの迷路を同時に作れるか：子ドローンが離れた場所に別の迷路を作り，
#        両方で measure() が自分の迷路の宝を返すか
#   出力は quick_print（出力ページ）に書く

def unit():
	return 2 ** (num_unlocked(Unlocks.Mazes) - 1)

DX = {North: 0, East: 1, South: 0, West: -1}
DY = {North: 1, East: 0, South: -1, West: 0}
OPP = {North: South, South: North, East: West, West: East}

def goto(tx, ty):
	# 壁の無い畑の上で目的地へ直進する
	while get_pos_x() < tx:
		move(East)
	while get_pos_x() > tx:
		move(West)
	while get_pos_y() < ty:
		move(North)
	while get_pos_y() > ty:
		move(South)

def make_maze(m):
	if get_entity_type() != None:
		harvest()
	if get_ground_type() != Grounds.Grassland:
		till()
	plant(Entities.Bush)
	return use_item(Items.Weird_Substance, m * unit())

def explore_all():
	# 迷路内を DFS で全部歩き，出発点に戻る．[マス数, xmin, xmax, ymin, ymax, 宝のマス数]
	x0 = get_pos_x()
	y0 = get_pos_y()
	seen = {}
	seen[x0 * 1000 + y0] = True
	back = []
	cnt = 1
	tre = 0
	if get_entity_type() == Entities.Treasure:
		tre += 1
	xmin = x0
	xmax = x0
	ymin = y0
	ymax = y0
	while True:
		x = get_pos_x()
		y = get_pos_y()
		moved = False
		for d in [North, East, South, West]:
			k = (x + DX[d]) * 1000 + y + DY[d]
			if not moved:
				if not (k in seen):
					if can_move(d):
						move(d)
						seen[k] = True
						back.append(OPP[d])
						cnt += 1
						if get_entity_type() == Entities.Treasure:
							tre += 1
						nx = get_pos_x()
						ny = get_pos_y()
						if nx < xmin:
							xmin = nx
						if nx > xmax:
							xmax = nx
						if ny < ymin:
							ymin = ny
						if ny > ymax:
							ymax = ny
						moved = True
		if not moved:
			if len(back) == 0:
				return [cnt, xmin, xmax, ymin, ymax, tre]
			move(back.pop())

def go_treasure():
	# 宝まで DFS で歩く（宝に近い方向を先に試す）
	t = measure()
	tx = t[0]
	ty = t[1]
	seen = {}
	seen[get_pos_x() * 1000 + get_pos_y()] = True
	back = []
	while get_entity_type() != Entities.Treasure:
		x = get_pos_x()
		y = get_pos_y()
		moved = False
		for d in [North, East, South, West]:
			if not moved:
				nx = x + DX[d]
				ny = y + DY[d]
				k = nx * 1000 + ny
				if not (k in seen):
					if abs(tx - nx) + abs(ty - ny) < abs(tx - x) + abs(ty - y):
						if can_move(d):
							move(d)
							seen[k] = True
							back.append(OPP[d])
							moved = True
		for d in [North, East, South, West]:
			if not moved:
				k = (x + DX[d]) * 1000 + y + DY[d]
				if not (k in seen):
					if can_move(d):
						move(d)
						seen[k] = True
						back.append(OPP[d])
						moved = True
		if not moved:
			if len(back) == 0:
				return False
			move(back.pop())
	return True

def one_test(m, bx, by, tag):
	# (bx,by) に m の迷路を作り，大きさ・位置・金を調べる
	goto(bx, by)
	ok = make_maze(m)
	quick_print(tag, "m", m, "use_item", ok, "足元", get_entity_type(), "宝", measure())
	r = explore_all()
	quick_print(tag, "マス数", r[0], "x", r[1], r[2], "y", r[3], r[4], "宝の数", r[5])
	go_treasure()
	g0 = num_items(Items.Gold)
	use_item(Items.Weird_Substance, m * unit())
	g1 = num_items(Items.Gold)
	quick_print(tag, "再配置の金", g1 - g0, "新しい宝", measure(), "足元", get_entity_type())
	go_treasure()
	harvest()
	quick_print(tag, "収穫の金", num_items(Items.Gold) - g1, "足元", get_entity_type())

clear()
quick_print("段階", num_unlocked(Unlocks.Mazes), "unit", unit(), "物質", num_items(Items.Weird_Substance))

# T1, T2：m=5 と m=8
one_test(5, 8, 8, "T5")
clear()
one_test(8, 8, 8, "T8")

# T3：2つの迷路を同時に作る
clear()
def child():
	goto(22, 22)
	make_maze(5)
	a = measure()
	r = explore_all()
	# 親の迷路ができるまで少し待ってから，もう一度自分の宝を測る
	w = 0
	while w < 300:
		w += 1
	b = measure()
	return [a, b, r]
h = spawn_drone(child)
goto(6, 6)
make_maze(5)
pa = measure()
pr = explore_all()
res = wait_for(h)
quick_print("T3 親の宝", pa, "親の迷路", pr)
quick_print("T3 子の宝", res[0], "待った後", res[1], "子の迷路", res[2])
quick_print("T3 親から見た宝（子が終わった後）", measure())
quick_print("合計tick", get_tick_count())
