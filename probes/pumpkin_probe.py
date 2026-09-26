# かぼちゃの仕様を確かめる実験（通常プレイの空いている畑で実行．32x32 を想定）
#   T1 成長時間（水はそのまま）・1x1 の収穫量・植えるときのにんじんの消費・枯れ（6回）
#   T2 水を満たしたときの成長時間（3回）
#   T3 肥料を1回使ったときの成長時間（3回）
#   T4 枯れる割合（8x8 に64本植えて，育ち切るまで待って数える）
#   T5 合体の収穫量（2x2 と 6x6．枯れたマスは植え直し，全マスのIDがそろったら収穫）
#   出力：quick_print（出力ページ）
#   枯れたかぼちゃは「get_entity_type() がかぼちゃでない（かつ空でない）」で判定する

LIMIT = 200000       # 1回の待ちの上限 tick（超えたら打ち切る）

def goto(tx, ty):
	while get_pos_x() < tx:
		move(East)
	while get_pos_x() > tx:
		move(West)
	while get_pos_y() < ty:
		move(North)
	while get_pos_y() > ty:
		move(South)

def prep():
	if get_ground_type() != Grounds.Soil:
		till()

def state():
	# "ok" 育ち切った / "dead" 枯れた / "grow" 育っている / "none" 何も無い
	e = get_entity_type()
	if e == None:
		return "none"
	if e != Entities.Pumpkin:
		return "dead"
	if can_harvest():
		return "ok"
	return "grow"

def wait_one():
	# 足元のかぼちゃが育ち切るか枯れるまで待つ．[tick, 状態, 待ち始めの水, 見た目の種類]
	t0 = get_tick_count()
	w0 = get_water()
	while True:
		s = state()
		if s != "grow":
			return [get_tick_count() - t0, s, w0, get_entity_type()]
		if get_tick_count() - t0 > LIMIT:
			return [get_tick_count() - t0, "timeout", w0, get_entity_type()]

clear()
quick_print("所持 にんじん", num_items(Items.Carrot), "水", num_items(Items.Water), "肥料", num_items(Items.Fertilizer), "かぼちゃ", num_items(Items.Pumpkin))

# ---- T1：水はそのまま，1マスで6回 ----
goto(0, 0)
prep()
for i in range(6):
	c0 = num_items(Items.Carrot)
	ok = plant(Entities.Pumpkin)
	c1 = num_items(Items.Carrot)
	r = wait_one()
	p0 = num_items(Items.Pumpkin)
	harvest()
	quick_print("T1", i, "plant", ok, "にんじん", c1 - c0, "成長", r[0], r[1], "水", r[2], r[3], "収穫", num_items(Items.Pumpkin) - p0)

# ---- T2：水を満たして3回 ----
goto(2, 0)
prep()
for i in range(3):
	k = 0
	while get_water() < 0.95 and k < 20:
		use_item(Items.Water)
		k += 1
	plant(Entities.Pumpkin)
	r = wait_one()
	harvest()
	quick_print("T2 水", i, "水を使った回数", k, "成長", r[0], r[1], "水", r[2])

# ---- T3：肥料を1回使って3回 ----
goto(4, 0)
prep()
for i in range(3):
	plant(Entities.Pumpkin)
	w = get_water()
	use_item(Items.Fertilizer)
	r = wait_one()
	harvest()
	quick_print("T3 肥料", i, "成長", r[0], r[1], "水", w)

# ---- T4：8x8 に64本植えて，枯れる割合 ----
for x in range(8):
	for y in range(8):
		goto(8 + x, 8 + y)
		prep()
		plant(Entities.Pumpkin)
t0 = get_tick_count()
while get_tick_count() - t0 < 30000:
	w = 0
ok = 0
dead = 0
grow = 0
none = 0
for x in range(8):
	for y in range(8):
		goto(8 + x, 8 + y)
		s = state()
		if s == "ok":
			ok += 1
		elif s == "dead":
			dead += 1
		elif s == "grow":
			grow += 1
		else:
			none += 1
quick_print("T4 64本 育ち切った", ok, "枯れた", dead, "育っている", grow, "空", none)
clear()

# ---- T5：合体の収穫量 ----
def merged(x0, y0, n):
	# n x n を植え，枯れたマスを植え直して，全マスが育ち切りIDがそろったら収穫する
	for x in range(n):
		for y in range(n):
			goto(x0 + x, y0 + y)
			prep()
			plant(Entities.Pumpkin)
	t0 = get_tick_count()
	replant = 0
	while True:
		allok = True
		first = None
		same = True
		for x in range(n):
			for y in range(n):
				goto(x0 + x, y0 + y)
				s = state()
				if s == "dead" or s == "none":
					plant(Entities.Pumpkin)
					replant += 1
					allok = False
				elif s == "grow":
					allok = False
				else:
					m = measure()
					if first == None:
						first = m
					elif m != first:
						same = False
		if allok and same:
			goto(x0, y0)
			p0 = num_items(Items.Pumpkin)
			harvest()
			return [num_items(Items.Pumpkin) - p0, replant, get_tick_count() - t0, first]
		if get_tick_count() - t0 > LIMIT * 5:
			return [-1, replant, get_tick_count() - t0, first]

r = merged(0, 0, 2)
quick_print("T5 2x2 収穫", r[0], "植え直し", r[1], "tick", r[2], "ID", r[3])
r = merged(10, 10, 6)
quick_print("T5 6x6 収穫", r[0], "植え直し", r[1], "tick", r[2], "ID", r[3])
quick_print("合計tick", get_tick_count())
