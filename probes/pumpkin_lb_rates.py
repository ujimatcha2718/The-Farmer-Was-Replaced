# かぼちゃのリーダーボードで，水と肥料が時間とともにどれだけ溜まるか，地面の水がどれだけ減るかを測る
#   leaderboard_run(Leaderboards.Pumpkins, "pumpkin_lb_rates", 256) で実行（記録にはならない）
#   R1 所持数の推移：約5000 tick ごとに 60000 tick まで（何もしないで待つ）
#   R2 地面の水の減り方：(1,0) に溜まった水を全部使って水の量を上げ，約2000 tick ごとに get_water() を見る
#   出力：quick_print（出力ページ）

def wait_ticks(k):
	t = get_tick_count()
	w = 0
	while get_tick_count() - t < k:
		w += 1

quick_print("start tick", get_tick_count(), "水", num_items(Items.Water), "肥料", num_items(Items.Fertilizer))
t0 = get_tick_count()
for i in range(12):
	wait_ticks(5000)
	quick_print("R1", get_tick_count() - t0, "水", num_items(Items.Water), "肥料", num_items(Items.Fertilizer))

move(East)
w0 = get_water()
k = 0
while num_items(Items.Water) >= 1 and get_water() < 0.99 and k < 10:
	use_item(Items.Water)
	k += 1
quick_print("R2 水を使った回数", k, "前", w0, "後", get_water(), "残りの水", num_items(Items.Water))
t0 = get_tick_count()
for i in range(15):
	wait_ticks(2000)
	quick_print("R2", get_tick_count() - t0, "地面の水", get_water())
quick_print("end tick", get_tick_count())
