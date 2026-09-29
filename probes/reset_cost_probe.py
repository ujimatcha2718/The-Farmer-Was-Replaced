# 最速リセット用：全アンロックの段階ごとの費用を，アンロック1つにつき1行で出力する
# （通常プレイで実行してよい．何も変えない）
#  出力の形：Unlocks.X 現在の段階 [段階0の費用, 段階1の費用, ...]
#  前の版は最大段階を超えると {} が返り続けて出力が長くなりすぎたので，{} で止める

for u in Unlocks:
	costs = []
	k = 0
	while k <= 40:
		c = get_cost(u, k)
		if c == None or len(c) == 0:
			k = 99
		else:
			costs.append(c)
			k += 1
	quick_print(u, num_unlocked(u), costs)
quick_print("done")
