# かぼちゃの合体の仕方（枯れたマスがあるとき）を確かめる実験（通常プレイの空いている畑で実行）
#   8x8 に植えて水を 1 にし，植え直さずに全マスが「育ち切った」か「枯れた」になるまで待つ．
#   そのときの ID ごとの範囲とマス数，枯れたマスの位置を書き出す．
#   いちばん大きい ID のまとまりの1マスで収穫し，収穫量と，収穫で消えたマス数を見る．3回くり返す．
#   出力：quick_print（出力ページ）

M = 8

def goto(tx, ty):
	while get_pos_x() < tx:
		move(East)
	while get_pos_x() > tx:
		move(West)
	while get_pos_y() < ty:
		move(North)
	while get_pos_y() > ty:
		move(South)

def trial(k):
	clear()
	for x in range(M):
		for y in range(M):
			goto(x, y)
			if get_ground_type() != Grounds.Soil:
				till()
			n = 0
			while get_water() < 0.99 and n < 6:
				use_item(Items.Water)
				n += 1
			plant(Entities.Pumpkin)
	# 全マスが育ち切るか枯れるまで待つ
	t0 = get_tick_count()
	while True:
		done = True
		for x in range(M):
			for y in range(M):
				goto(x, y)
				e = get_entity_type()
				if e == Entities.Pumpkin:
					if not can_harvest():
						done = False
		if done:
			break
		if get_tick_count() - t0 > 300000:
			break
	ids = []
	box = []
	dead = []
	for x in range(M):
		for y in range(M):
			goto(x, y)
			if get_entity_type() != Entities.Pumpkin:
				dead.append(x * 10 + y)
			else:
				m = measure()
				f = -1
				j = 0
				while j < len(ids):
					if ids[j] == m:
						f = j
					j += 1
				if f < 0:
					ids.append(m)
					box.append([x, x, y, y, 1])
				else:
					b = box[f]
					if x < b[0]:
						b[0] = x
					if x > b[1]:
						b[1] = x
					if y < b[2]:
						b[2] = y
					if y > b[3]:
						b[3] = y
					b[4] += 1
	quick_print("試行", k, "枯れたマス(x*10+y)", dead, "IDの種類", len(ids))
	best = 0
	for j in range(len(ids)):
		b = box[j]
		quick_print("  ID", j, "x", b[0], b[1], "y", b[2], b[3], "マス数", b[4])
		if b[4] > box[best][4]:
			best = j
	b = box[best]
	goto(b[0], b[2])
	p0 = num_items(Items.Pumpkin)
	harvest()
	got = num_items(Items.Pumpkin) - p0
	left = 0
	for x in range(M):
		for y in range(M):
			goto(x, y)
			if get_entity_type() == Entities.Pumpkin:
				left += 1
	quick_print("  最大のまとまり", best, "で収穫", got, "残ったかぼちゃ", left)

for k in range(3):
	trial(k)
quick_print("合計tick", get_tick_count())
