# 最速リセット用：全アンロックの段階と費用を出力する（通常プレイで実行してよい．何も変えない）
#  1) 各アンロックの現在の段階と，次の段階の費用（get_cost(u)）
#  2) 段階を指定した費用 get_cost(u, k)（k = 0..30．None になったら止める）
#     ※ 2) は第2引数が使えないとエラーで止まるが，1) の出力はそれまでに出ている
#  Unlocks を for で回せないとエラーで止まる．その場合はエラーの文を知らせてほしい

quick_print("=== 1: current level and next cost ===")
for u in Unlocks:
	quick_print(u, num_unlocked(u), get_cost(u))

quick_print("=== 2: cost by level ===")
for u in Unlocks:
	k = 0
	while k <= 30:
		c = get_cost(u, k)
		if c == None:
			k = 99
		else:
			quick_print(u, k, c)
			k += 1
quick_print("=== done ===")
