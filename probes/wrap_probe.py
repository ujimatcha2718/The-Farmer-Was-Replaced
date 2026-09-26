# 通常の帽子で盤面の端を回り込むかを確かめる実験（空いている畑で実行）
#   (0,0) から West と South へ1歩ずつ動き，戻り値・座標・かかった tick を記録する．
#   回り込むなら West で x = n-1，South で y = n-1 になる．
#   回り込まないなら座標は 0 のままで，move は False を返すはずである（推定）．
#   子ドローンでも同じかを確かめる（戻り値で受け取る）

def step(d):
	t = get_tick_count()
	r = move(d)
	return [r, get_pos_x(), get_pos_y(), get_tick_count() - t]

def child():
	a = step(West)
	b = step(South)
	return [a, b]

clear()
n = get_world_size()
quick_print("n", n, "start", get_pos_x(), get_pos_y())
quick_print("W 1歩 [戻り値, x, y, tick]", step(West))
quick_print("S 1歩 [戻り値, x, y, tick]", step(South))

clear()
h = spawn_drone(child)
if h == None:
	quick_print("子を出せなかった")
else:
	quick_print("子 W,S", wait_for(h))

# 東端と北端からも確かめる（(n-1,n-1) まで歩いてから East と North）
clear()
for i in range(n - 1):
	move(East)
	move(North)
quick_print("E 1歩 [戻り値, x, y, tick]", step(East))
quick_print("N 1歩 [戻り値, x, y, tick]", step(North))
