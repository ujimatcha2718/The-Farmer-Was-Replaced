# 最速リセット用：段階ごとの収穫量・1秒あたりの tick・盤面の大きさ・機数を調べる
# 通常プレイで実行する（Simulation が要る）．reset_yield_child.py と reset_size_child.py をその名前で保存しておくこと
# 出力は1回の simulate につき2行：子の行（Y ... または S ...）と，M 名前 段階 秒数
#   Y 行：草・茂み・木・にんじん・かぼちゃ・サボテンを1本ずつ育てて収穫したときに増えた数と，かかった tick
#   S 行：Expand・Megafarm の段階，盤面の一辺，max_drones()

ITEMS = {Items.Hay: 100000, Items.Wood: 100000, Items.Carrot: 100000, Items.Pumpkin: 100000}

def base():
	d = {}
	d[Unlocks.Plant] = 1
	d[Unlocks.Carrots] = 1
	d[Unlocks.Trees] = 1
	d[Unlocks.Pumpkins] = 1
	d[Unlocks.Cactus] = 1
	return d

def run(child, name, u, k):
	d = base()
	d[u] = k
	s = simulate(child, d, ITEMS, {}, 0, 64)
	quick_print("M", name, k, "secs", s)

for k in range(0, 6):
	run("reset_yield_child", "Speed", Unlocks.Speed, k)
for k in range(0, 4):
	run("reset_yield_child", "Grass", Unlocks.Grass, k)
for k in range(1, 5):
	run("reset_yield_child", "Trees", Unlocks.Trees, k)
for k in range(1, 5):
	run("reset_yield_child", "Carrots", Unlocks.Carrots, k)
for k in range(1, 5):
	run("reset_yield_child", "Pumpkins", Unlocks.Pumpkins, k)
for k in range(1, 5):
	run("reset_yield_child", "Cactus", Unlocks.Cactus, k)
for k in range(0, 10):
	run("reset_size_child", "Expand", Unlocks.Expand, k)
for k in range(0, 6):
	run("reset_size_child", "Megafarm", Unlocks.Megafarm, k)
quick_print("done")
