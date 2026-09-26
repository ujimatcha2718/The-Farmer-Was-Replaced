# かぼちゃの実験 その2（通常プレイの空いている畑で実行．32x32・32機を想定）
#   G1 成長時間の分布（水なし）：32機がそれぞれ1マスに植え，育ち切るか枯れるまでの tick を測る．2回（64本）
#   G2 成長時間の分布（水あり）：同じことを，水の量を 0.9 以上に保ちながら．1回（32本）
#   M1 合体の仕方：12x12 に植え（6x6 の区画が4つ並ぶ形），枯れを植え直して全マスが育ち切るまで待ち，
#      ID の種類と，それぞれの範囲（x,y の最小・最大）とマス数を書き出す．(0,0) で収穫し，収穫量と残ったマス数を見る
#   出力：quick_print（出力ページ）

LIMIT = 300000

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
	e = get_entity_type()
	if e == None:
		return "none"
	if e != Entities.Pumpkin:
		return "dead"
	if can_harvest():
		return "ok"
	return "grow"

def make_grower(x, y, wet):
	def run():
		goto(x, y)
		prep()
		if wet:
			k = 0
			while get_water() < 0.95 and k < 8:
				use_item(Items.Water)
				k += 1
		plant(Entities.Pumpkin)
		t0 = get_tick_count()
		while True:
			s = state()
			if s != "grow":
				r = [get_tick_count() - t0, s]
				harvest()
				return r
			if wet:
				if get_water() < 0.9:
					use_item(Items.Water)
			if get_tick_count() - t0 > LIMIT:
				return [get_tick_count() - t0, "timeout"]
	return run

def batch(y, wet, tag):
	hs = []
	for x in range(1, 32):
		h = spawn_drone(make_grower(x, y, wet))
		if h != None:
			hs.append(h)
	r0 = make_grower(0, y, wet)()
	res = [r0]
	for h in hs:
		res.append(wait_for(h))
	ok = []
	dead = []
	for r in res:
		if r[1] == "ok":
			ok.append(r[0])
		else:
			dead.append(r[0])
	quick_print(tag, "育ち切った", len(ok), "枯れた/その他", len(dead))
	quick_print(tag, "育ち切った tick", ok)
	quick_print(tag, "枯れた tick", dead)

clear()
batch(0, False, "G1a")
batch(1, False, "G1b")
batch(2, True, "G2")

# ---- M1：合体の仕方 ----
clear()
N = 12
for x in range(N):
	for y in range(N):
		goto(x, y)
		prep()
		plant(Entities.Pumpkin)
t0 = get_tick_count()
replant = 0
while True:
	allok = True
	for x in range(N):
		for y in range(N):
			goto(x, y)
			s = state()
			if s == "dead" or s == "none":
				plant(Entities.Pumpkin)
				replant += 1
				allok = False
			elif s == "grow":
				allok = False
	if allok:
		break
	if get_tick_count() - t0 > LIMIT * 3:
		break
# ID ごとの範囲を集める
ids = []
box = []
for x in range(N):
	for y in range(N):
		goto(x, y)
		m = measure()
		j = 0
		found = -1
		while j < len(ids):
			if ids[j] == m:
				found = j
			j += 1
		if found < 0:
			ids.append(m)
			box.append([x, x, y, y, 1])
		else:
			b = box[found]
			if x < b[0]:
				b[0] = x
			if x > b[1]:
				b[1] = x
			if y < b[2]:
				b[2] = y
			if y > b[3]:
				b[3] = y
			b[4] += 1
quick_print("M1 植え直し", replant, "tick", get_tick_count() - t0, "IDの種類", len(ids))
for j in range(len(ids)):
	quick_print("M1 ID", ids[j], "x", box[j][0], box[j][1], "y", box[j][2], box[j][3], "マス数", box[j][4])
goto(0, 0)
p0 = num_items(Items.Pumpkin)
harvest()
got = num_items(Items.Pumpkin) - p0
left = 0
for x in range(N):
	for y in range(N):
		goto(x, y)
		if get_entity_type() == Entities.Pumpkin:
			left += 1
quick_print("M1 (0,0) で収穫", got, "残ったかぼちゃのマス", left)
quick_print("合計tick", get_tick_count())
