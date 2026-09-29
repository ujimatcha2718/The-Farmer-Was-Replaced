# reset_mech_probe.py から simulate で呼ばれる．4x4 で恐竜の尾を伸ばし，骨の量を見る（lab の閉路）
LOOP = [East, North, North, East, South, South, East, North, North, North, West, West, West, South, South, South]
clear()
b0 = num_items(Items.Bone)
c0 = num_items(Items.Cactus)
change_hat(Hats.Dinosaur_Hat)
steps = 0
ok = True
while ok:
	for d in LOOP:
		if ok:
			if move(d):
				steps += 1
			else:
				ok = False
change_hat(Hats.Straw_Hat)
quick_print("C Dinosaurs", num_unlocked(Unlocks.Dinosaurs), "size", get_world_size(), "steps", steps, "bones", num_items(Items.Bone) - b0, "cactus used", c0 - num_items(Items.Cactus))
