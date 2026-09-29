# reset_mech_probe.py から simulate で呼ばれる．4x4 の整列したサボテン：健康なときと，(1,1) に物質を使ったとき
def goto(tx, ty):
	while get_pos_x() < tx:
		move(East)
	while get_pos_x() > tx:
		move(West)
	while get_pos_y() < ty:
		move(North)
	while get_pos_y() > ty:
		move(South)

def grow_sorted(k):
	for x in range(k):
		for y in range(k):
			goto(x, y)
			if get_ground_type() != Grounds.Soil:
				till()
			plant(Entities.Cactus)
	changed = True
	while changed:
		changed = False
		for x in range(k):
			for y in range(k):
				goto(x, y)
				if x < k - 1 and measure(East) < measure():
					swap(East)
					changed = True
				if y < k - 1 and measure(North) < measure():
					swap(North)
					changed = True
	for x in range(k):
		for y in range(k):
			goto(x, y)
			while not can_harvest():
				a = 1

def take():
	goto(0, 0)
	c0 = num_items(Items.Cactus)
	w0 = num_items(Items.Weird_Substance)
	harvest()
	return [num_items(Items.Cactus) - c0, num_items(Items.Weird_Substance) - w0]

clear()
grow_sorted(4)
quick_print("B healthy 4x4 [cactus,substance]", take())
grow_sorted(4)
goto(1, 1)
use_item(Items.Weird_Substance)
quick_print("B infected (1,1) 4x4 [cactus,substance]", take())
