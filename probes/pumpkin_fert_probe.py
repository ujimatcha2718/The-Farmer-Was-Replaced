# 肥料をかぼちゃに使ったときの効果と害を確かめる実験（通常プレイの空いている畑で実行）
#   F1 1マス：水1で植えて肥料を k 回（k=1,2,3）使い，育ち切るまでの tick と，収穫したときの
#      かぼちゃ・奇妙な物質の増え方を見る（各2回）
#   F2 6x6：水1で植え，1マスだけ肥料を1回使う．枯れを植え直して全マスがそろったら収穫し，
#      かぼちゃ・奇妙な物質の増え方を見る（肥料なしなら かぼちゃ 110,592）
#   F3 6x6：F2 と同じだが，肥料を使ったマスに奇妙な物質を1回使ってから（感染を治す）そろえて収穫
#   出力：quick_print（出力ページ）

def goto(tx, ty):
	while get_pos_x() < tx:
		move(East)
	while get_pos_x() > tx:
		move(West)
	while get_pos_y() < ty:
		move(North)
	while get_pos_y() > ty:
		move(South)

def prep_plant():
	if get_ground_type() != Grounds.Soil:
		till()
	k = 0
	while get_water() < 0.99 and k < 6:
		use_item(Items.Water)
		k += 1
	plant(Entities.Pumpkin)

def items():
	return [num_items(Items.Pumpkin), num_items(Items.Weird_Substance)]

def diff(a, b):
	return [b[0] - a[0], b[1] - a[1]]

# ---- F1 ----
clear()
goto(0, 0)
for k in range(1, 4):
	for r in range(2):
		prep_plant()
		t0 = get_tick_count()
		for i in range(k):
			use_item(Items.Fertilizer)
		t1 = get_tick_count()
		w = 0
		while get_entity_type() == Entities.Pumpkin and not can_harvest():
			w += 1
		t2 = get_tick_count()
		e = get_entity_type()
		a = items()
		harvest()
		quick_print("F1 肥料", k, "回", r, "肥料の時間", t1 - t0, "肥料後に育つまで", t2 - t1, e, "増えた[かぼちゃ,物質]", diff(a, items()))

def grow_square(s, fert, cure):
	for x in range(s):
		for y in range(s):
			goto(x, y)
			prep_plant()
			if x == 2 and y == 2:
				if fert:
					use_item(Items.Fertilizer)
				if cure:
					use_item(Items.Weird_Substance)
	t0 = get_tick_count()
	rep = 0
	while True:
		done = True
		for x in range(s):
			for y in range(s):
				goto(x, y)
				if get_entity_type() != Entities.Pumpkin:
					prep_plant()
					rep += 1
					done = False
				elif not can_harvest():
					done = False
		if done:
			break
		if get_tick_count() - t0 > 400000:
			break
	goto(0, 0)
	m0 = measure()
	goto(s - 1, s - 1)
	m1 = measure()
	a = items()
	harvest()
	return [diff(a, items()), rep, m0 == m1]

# ---- F2 ----
clear()
r = grow_square(6, True, False)
quick_print("F2 6x6（1マスに肥料） 増えた[かぼちゃ,物質]", r[0], "植え直し", r[1], "角のIDが同じ", r[2])
# ---- F3 ----
clear()
r = grow_square(6, True, True)
quick_print("F3 6x6（肥料→奇妙な物質で治す） 増えた[かぼちゃ,物質]", r[0], "植え直し", r[1], "角のIDが同じ", r[2])
# 比較：肥料なし
clear()
r = grow_square(6, False, False)
quick_print("F0 6x6（肥料なし） 増えた[かぼちゃ,物質]", r[0], "植え直し", r[1], "角のIDが同じ", r[2])
quick_print("合計tick", get_tick_count())
