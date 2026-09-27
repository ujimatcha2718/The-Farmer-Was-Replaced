# かぼちゃの合体の規則をくわしく確かめる実験（通常プレイの空いている畑で実行）
#   L1：先に中央の 2x2（(3,3)〜(4,4)）を合体させてから，8x8 の残りを植え，枯れを植え直して全マスを
#       生かす．最後に 8x8 が1つにまとまるか（先にできた塊を中に含む大きな正方形になるか）
#   L2：先に (5,5)〜(6,6) の 2x2 を合体させてから，6x6（(0,0)〜(5,5)）の残りだけを植えて全部生かす．
#       2x2 は 6x6 の角からはみ出している．6x6 がまとまるか（はみ出した塊があると大きくならないか）
#   L3：8x8 に全部植えて全部生かしたあと，さらに待って塊がどうなるかを2回見る（時間で大きくなるか）
#   水は各マス 1 にする．出力：quick_print（出力ページ）

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

def grow_all(cells):
	# cells（x*100+y のリスト）を植え，枯れを植え直して，全部が育ち切るまで待つ
	for c in cells:
		goto(c // 100, c % 100)
		prep_plant()
	t0 = get_tick_count()
	while True:
		done = True
		for c in cells:
			goto(c // 100, c % 100)
			e = get_entity_type()
			if e != Entities.Pumpkin:
				prep_plant()
				done = False
			elif not can_harvest():
				done = False
		if done:
			return get_tick_count() - t0
		if get_tick_count() - t0 > 400000:
			return -1

def square(x0, y0, s):
	r = []
	for x in range(x0, x0 + s):
		for y in range(y0, y0 + s):
			r.append(x * 100 + y)
	return r

def report(tag, x0, y0, s):
	ids = []
	box = []
	for x in range(x0, x0 + s):
		for y in range(y0, y0 + s):
			goto(x, y)
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
	quick_print(tag, "IDの種類", len(ids))
	for j in range(len(ids)):
		b = box[j]
		if b[4] > 1:
			quick_print("  ", tag, "x", b[0], b[1], "y", b[2], b[3], "マス数", b[4])

def wait_ticks(k):
	t = get_tick_count()
	w = 0
	while get_tick_count() - t < k:
		w += 1

# ---- L1 ----
clear()
t = grow_all(square(3, 3, 2))
report("L1 先の2x2", 3, 3, 2)
rest = []
for c in square(0, 0, 8):
	x = c // 100
	y = c % 100
	if not (x >= 3 and x <= 4 and y >= 3 and y <= 4):
		rest.append(c)
t = grow_all(rest)
report("L1 8x8 全部生かした直後", 0, 0, 8)
wait_ticks(5000)
report("L1 さらに5000 tick後", 0, 0, 8)

# ---- L2 ----
clear()
t = grow_all(square(5, 5, 2))
report("L2 先の2x2", 5, 5, 2)
rest = []
for c in square(0, 0, 6):
	x = c // 100
	y = c % 100
	if not (x == 5 and y == 5):
		rest.append(c)
t = grow_all(rest)
report("L2 7x7 の範囲（6x6 と はみ出した2x2）", 0, 0, 7)
wait_ticks(5000)
report("L2 さらに5000 tick後", 0, 0, 7)

# ---- L3 ----
clear()
t = grow_all(square(0, 0, 8))
report("L3 8x8 全部生かした直後", 0, 0, 8)
wait_ticks(5000)
report("L3 さらに5000 tick後", 0, 0, 8)
quick_print("合計tick", get_tick_count())
