# 最速リセット用：アンロックの段階ごとに，盤面の大きさ・機数・植える費用を調べる
# 通常プレイで実行する（Simulation のアンロックが要る）．reset_state_child.py を同じ名前で保存しておくこと
# 出力の読み方：M ＝ どの段階を指定したか．続く L/W/D/C は子（simulate の中）の出力
#   L：Expand Megafarm Carrots Pumpkins Cactus Dinosaurs Speed の段階
#   W：盤面の一辺　D：max_drones()　C：にんじん・かぼちゃ・サボテン・リンゴを植える費用
# 子の出力が出ない場合（simulate の中の quick_print が見えない場合）は，その旨を知らせてほしい

def run(name, u, k):
	d = {}
	d[u] = k
	quick_print("M", name, k)
	s = simulate("reset_state_child", d, {}, {}, 0, 64)
	quick_print("secs", s)

for k in range(0, 10):
	run("Expand", Unlocks.Expand, k)
for k in range(0, 6):
	run("Megafarm", Unlocks.Megafarm, k)
for k in range(0, 4):
	run("Carrots", Unlocks.Carrots, k)
for k in range(0, 4):
	run("Pumpkins", Unlocks.Pumpkins, k)
for k in range(0, 4):
	run("Cactus", Unlocks.Cactus, k)
for k in range(0, 4):
	run("Dinosaurs", Unlocks.Dinosaurs, k)
quick_print("done")
