# 何をすると大きさが変わるのかを確かめる実験（空いている畑で実行）
#   1回目の実験では (0,0) で 5 → （育ち切って収穫）→ 1 と変わった．
#   2回目の実験では，すぐの植え直しでも往復をはさんでも変わらなかった．
#   そこで「育ち切ってからの収穫」「時間の経過」「clear()」「耕し直し」
#   「別のマスでの収穫」のどれで変わるかを1つずつ調べる．
#   各テストは (前の値, 後の値) を記録する．前後の値は未成熟で植えて測って
#   すぐ収穫して調べる（2回目の実験から，これだけでは値は変わらない）

def base():
	# 未成熟で植えて測り，すぐ収穫する
	plant(Entities.Cactus)
	v = measure()
	harvest()
	return v

def wait_ticks(k):
	t = get_tick_count()
	w = 0
	while get_tick_count() - t < k:
		w += 1

def wait_grown():
	w = 0
	while not can_harvest():
		w += 1

clear()
till()
move(East)
till()
move(West)

# T1：育ち切ってから収穫すると変わるか（4回）
r = []
for i in range(4):
	b = base()
	plant(Entities.Cactus)
	wait_grown()
	harvest()
	a = base()
	r.append(b)
	r.append(a)
quick_print("T1 育ち切ってから収穫 (前,後)x4", r)

# T2：時間がたつだけで変わるか（7000 tick 待つ，3回）
r = []
for i in range(3):
	b = base()
	wait_ticks(7000)
	a = base()
	r.append(b)
	r.append(a)
quick_print("T2 7000tick待つ (前,後)x3", r)

# T3：耕し直し（草地に戻して再び畑に）で変わるか
b = base()
till()
till()
a = base()
quick_print("T3 耕し直し (前,後)", b, a, get_ground_type())

# T4：別のマスで育ち切ったものを収穫すると変わるか
b = base()
move(East)
plant(Entities.Cactus)
wait_grown()
harvest()
move(West)
a = base()
quick_print("T4 隣で収穫 (前,後)", b, a)

# T5：clear() で変わるか
b = base()
clear()
if get_ground_type() != Grounds.Soil:
	till()
a = base()
quick_print("T5 clear (前,後)", b, a)
quick_print("合計tick", get_tick_count())
