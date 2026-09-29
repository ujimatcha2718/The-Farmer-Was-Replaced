# 最速リセット用：仕組みの確認（通常プレイで実行．Simulation が要る）
# 子 rp_a.py rp_b.py rp_c.py rp_d.py をその名前で保存しておくこと．出力は十数行
#   A1：にんじん畑で (0,0) と (4,4) に物質を使ったとき，どのマスが感染したか（4方向か8方向か，端で回り込むか）
#   A2：6x6 の合体かぼちゃの (2,2) に物質を使ったときの，かぼちゃと物質の量
#   B ：4x4 の整列したサボテン．健康なときと (1,1) に物質を使ったときの，サボテンと物質の量
#   C ：Dinosaurs 1,2 段階で 4x4 を埋めたときの骨の量
#   D ：Fertilizer 1〜4 段階で 8000 tick に届く肥料の数．ひまわりの Power（1段階のときだけ）
BIG = 1000000

def base():
	d = {}
	d[Unlocks.Plant] = 1
	d[Unlocks.Senses] = 1
	d[Unlocks.Carrots] = 1
	return d

def items():
	d = {}
	d[Items.Hay] = BIG
	d[Items.Wood] = BIG
	d[Items.Carrot] = BIG
	d[Items.Pumpkin] = BIG
	d[Items.Cactus] = BIG
	d[Items.Weird_Substance] = 1000
	return d

u = base()
u[Unlocks.Expand] = 5
u[Unlocks.Carrots] = 3
u[Unlocks.Pumpkins] = 3
quick_print("A secs", simulate("rp_a", u, items(), {}, 0, 64))

u = base()
u[Unlocks.Expand] = 5
u[Unlocks.Cactus] = 2
quick_print("B secs", simulate("rp_b", u, items(), {}, 0, 64))

for k in range(1, 3):
	u = base()
	u[Unlocks.Expand] = 3
	u[Unlocks.Cactus] = 1
	u[Unlocks.Hats] = 1
	u[Unlocks.Dinosaurs] = k
	quick_print("C secs", simulate("rp_c", u, items(), {}, 0, 64))

for k in range(1, 5):
	u = base()
	u[Unlocks.Expand] = 4
	u[Unlocks.Sunflowers] = 1
	u[Unlocks.Watering] = 1
	u[Unlocks.Fertilizer] = k
	quick_print("D secs", simulate("rp_d", u, items(), {}, 0, 64))
quick_print("done")
