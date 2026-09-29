# reset_mech_probe.py から simulate で呼ばれる．肥料の届く速さ（Speed 0 で 8,000 tick ＝ 約20秒）と，ひまわりの Power
t0 = get_tick_count()
f0 = num_items(Items.Fertilizer)
w0 = num_items(Items.Water)
while get_tick_count() - t0 < 8000:
	a = 1
quick_print("D Fertilizer", num_unlocked(Unlocks.Fertilizer), "Watering", num_unlocked(Unlocks.Watering), "in 8000 ticks: fertilizer", num_items(Items.Fertilizer) - f0, "water", num_items(Items.Water) - w0)

def goto(tx, ty):
	while get_pos_x() < tx:
		move(East)
	while get_pos_x() > tx:
		move(West)
	while get_pos_y() < ty:
		move(North)
	while get_pos_y() > ty:
		move(South)

if num_unlocked(Unlocks.Fertilizer) == 1:
	n = get_world_size()
	clear()
	for x in range(n):
		for y in range(n):
			goto(x, y)
			till()
			plant(Entities.Sunflower)
	best = 0
	bx = 0
	by = 0
	for x in range(n):
		for y in range(n):
			goto(x, y)
			while not can_harvest():
				a = 1
			if measure() > best:
				best = measure()
				bx = x
				by = y
	# 先に最多のものを収穫（8倍になるはず），次に最多でないものを収穫（通常の量）
	goto(bx, by)
	p0 = num_items(Items.Power)
	harvest()
	p1 = num_items(Items.Power)
	lx = 0
	ly = 0
	if bx == 0 and by == 0:
		lx = 1
	goto(lx, ly)
	low = measure()
	harvest()
	p2 = num_items(Items.Power)
	quick_print("D sunflowers", n * n, "petals max", best, "power", p1 - p0, "petals other", low, "power", p2 - p1)
