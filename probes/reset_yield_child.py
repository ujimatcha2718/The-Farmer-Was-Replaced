# reset_yield_probe.py から simulate で呼ばれる（1×1 の盤面で1本ずつ育てて収穫し，増えた数を出す）
def gain(item, entity, soil):
	if soil:
		if get_ground_type() != Grounds.Soil:
			till()
	else:
		if get_ground_type() == Grounds.Soil:
			till()
	if get_entity_type() != entity:
		if entity != Entities.Grass:
			plant(entity)
	while not can_harvest():
		if get_entity_type() != entity:
			plant(entity)
	a = num_items(item)
	harvest()
	return num_items(item) - a

t0 = get_tick_count()
h = gain(Items.Hay, Entities.Grass, False)
b = gain(Items.Wood, Entities.Bush, False)
t = gain(Items.Wood, Entities.Tree, False)
c = gain(Items.Carrot, Entities.Carrot, True)
p = gain(Items.Pumpkin, Entities.Pumpkin, True)
k = gain(Items.Cactus, Entities.Cactus, True)
quick_print("Y hay", h, "bush", b, "tree", t, "carrot", c, "pumpkin", p, "cactus", k, "ticks", get_tick_count() - t0)
