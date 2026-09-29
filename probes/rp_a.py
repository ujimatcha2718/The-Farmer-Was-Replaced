# reset_mech_probe.py から simulate で呼ばれる．感染の反転の範囲と，合体かぼちゃの物質
def goto(tx, ty):
	while get_pos_x() < tx:
		move(East)
	while get_pos_x() > tx:
		move(West)
	while get_pos_y() < ty:
		move(North)
	while get_pos_y() > ty:
		move(South)

def soil():
	if get_ground_type() != Grounds.Soil:
		till()

n = get_world_size()
# A1：全マスににんじん．(0,0) と (4,4) に物質を1回ずつ使い，収穫で物質が出たマスを出す
clear()
for x in range(n):
	for y in range(n):
		goto(x, y)
		soil()
		plant(Entities.Carrot)
for x in range(n):
	for y in range(n):
		goto(x, y)
		while not can_harvest():
			a = 1
goto(0, 0)
use_item(Items.Weird_Substance)
goto(4, 4)
use_item(Items.Weird_Substance)
hit = []
for x in range(n):
	for y in range(n):
		goto(x, y)
		w0 = num_items(Items.Weird_Substance)
		c0 = num_items(Items.Carrot)
		harvest()
		dw = num_items(Items.Weird_Substance) - w0
		if dw > 0:
			hit.append([x, y, dw, num_items(Items.Carrot) - c0])
quick_print("A1 n", n, "infected cells [x,y,substance,carrot]", hit)

# A2：6x6 の合体かぼちゃ．全マスがそろったら (2,2) に物質を1回使い，(0,0) で収穫
clear()
for x in range(6):
	for y in range(6):
		goto(x, y)
		soil()
		plant(Entities.Pumpkin)
done = False
while not done:
	done = True
	for x in range(6):
		for y in range(6):
			goto(x, y)
			if get_entity_type() != Entities.Pumpkin:
				plant(Entities.Pumpkin)
				done = False
			elif not can_harvest():
				done = False
goto(0, 0)
m0 = measure()
goto(5, 5)
m1 = measure()
goto(2, 2)
use_item(Items.Weird_Substance)
goto(0, 0)
w0 = num_items(Items.Weird_Substance)
p0 = num_items(Items.Pumpkin)
harvest()
quick_print("A2 merged", m0 == m1, "pumpkin", num_items(Items.Pumpkin) - p0, "substance", num_items(Items.Weird_Substance) - w0)
