# 植え直しで大きさが変わるかを確かめる実験（空いている畑で実行）
#   A: 同じマスですぐ植え直す（15回）
#   B: 同じマスで，収穫と植え付けのあいだに隣へ往復してから植え直す（10回）
#   C: 隣のマスですぐ植え直す（10回）
#   D: 各命令の tick
clear()
till()
move(East)
till()
move(West)

a = []
for i in range(15):
	plant(Entities.Cactus)
	a.append(measure())
	harvest()
quick_print("A 同じマス即植え直し", a)

b = []
for i in range(10):
	plant(Entities.Cactus)
	b.append(measure())
	harvest()
	move(East)
	move(West)
quick_print("B 往復をはさむ", b)

move(East)
c = []
for i in range(10):
	plant(Entities.Cactus)
	c.append(measure())
	harvest()
quick_print("C 隣のマス", c)

t0 = get_tick_count()
plant(Entities.Cactus)
t1 = get_tick_count()
v = measure()
t2 = get_tick_count()
harvest()
t3 = get_tick_count()
quick_print("D tick plant", t1 - t0, "measure", t2 - t1, "harvest(未成熟)", t3 - t2)
