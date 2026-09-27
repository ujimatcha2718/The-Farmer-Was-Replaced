# 植えたかぼちゃが地面の水を使うかを確かめる実験（通常プレイの空いている畑で実行，4機を使う）
#   A (0,0)：水を 1 にして，かぼちゃを植え続ける（育ち切るか枯れたら収穫して植え直す）
#   B (2,0)：水を 1 にして，何も植えない（耕すだけ）
#   C (4,0)：水を 0.5 にして，かぼちゃを植え続ける
#   D (6,0)：水を 0.5 にして，何も植えない
#   各機が約2000 tick ごとに，自分のマスの水の量と，植え直した回数を書き出す（40000 tick まで）．
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

def make_cell(tag, x, level, grow):
	def run():
		goto(x, 0)
		if get_ground_type() != Grounds.Soil:
			till()
		k = 0
		while get_water() < level - 0.01 and k < 10:
			use_item(Items.Water)
			k += 1
		if grow:
			plant(Entities.Pumpkin)
		t0 = get_tick_count()
		nxt = 0
		cycles = 0
		out = []
		while get_tick_count() - t0 < 40000:
			if grow:
				e = get_entity_type()
				if e != Entities.Pumpkin or can_harvest():
					harvest()
					plant(Entities.Pumpkin)
					cycles += 1
			if get_tick_count() - t0 >= nxt:
				out.append(get_tick_count() - t0)
				out.append(get_water())
				out.append(cycles)
				nxt += 2000
		return [tag, k, out]
	return run

clear()
hs = []
hs.append(spawn_drone(make_cell("B 水1・植えない", 2, 1.0, False)))
hs.append(spawn_drone(make_cell("C 水0.5・植える", 4, 0.5, True)))
hs.append(spawn_drone(make_cell("D 水0.5・植えない", 6, 0.5, False)))
ra = make_cell("A 水1・植える", 0, 1.0, True)()
res = [ra]
for h in hs:
	res.append(wait_for(h))
for r in res:
	quick_print(r[0], "水を使った回数", r[1])
	o = r[2]
	j = 0
	while j < len(o):
		quick_print("  ", r[0], "tick", o[j], "水", o[j + 1], "植え直し", o[j + 2])
		j += 3
