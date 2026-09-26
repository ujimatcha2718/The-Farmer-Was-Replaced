# ============================================================
#  The Farmer Was Replaced（農家はreplace()されました）
#  迷路自動攻略コード
#   - 解法: measure() で宝の座標を取得し，宝に近づく方向を優先する深さ優先探索(DFS)
#   - 訪問済みマスを記録するので，迷路再利用で壁が消えてループができても無限周回しない
#   - REUSE_MAZE = True で同じ迷路を再利用（最大300回），False で毎回新規生成
# ============================================================

REUSE_MAZE = False   # 迷路を再利用するか
TARGET_GOLD = 100000 # この金額に達したら終了

# 方向ごとの座標変化と逆方向
DX = {North: 0, East: 1, South: 0, West: -1}
DY = {North: 1, East: 0, South: -1, West: 0}
OPPOSITE = {North: South, South: North, East: West, West: East}


def substance_amount():
	# ゲーム内ヒントに記載の式（アンロック段階に応じた最大サイズの迷路）
	return get_world_size() * 2 ** (num_unlocked(Unlocks.Mazes) - 1)


def make_maze():
	# ドローンの足元に茂みを植え，奇妙な物質で迷路化する
	if get_entity_type() != Entities.Bush:
		harvest()
		plant(Entities.Bush)
	return use_item(Items.Weird_Substance, substance_amount())


def key(x, y):
	# 座標を整数1個に変換（dictのキー用）
	return x * 1000 + y


def ordered_dirs(x, y, tx, ty):
	# 宝に近づく方向を先に試す（ヒューリスティック）
	first = []
	rest = []
	for d in [North, East, South, West]:
		nx = x + DX[d]
		ny = y + DY[d]
		if abs(tx - nx) + abs(ty - ny) < abs(tx - x) + abs(ty - y):
			first.append(d)
		else:
			rest.append(d)
	return first + rest


def go_to_treasure():
	# 現在地から宝までDFSで移動する．到達したらTrueを返す
	tx, ty = measure()
	visited = {}
	visited[key(get_pos_x(), get_pos_y())] = True
	path = []  # 来た方向の履歴（戻るときに逆向きに進む）

	while get_entity_type() != Entities.Treasure:
		x = get_pos_x()
		y = get_pos_y()
		moved = False
		for d in ordered_dirs(x, y, tx, ty):
			k = key(x + DX[d], y + DY[d])
			if not (k in visited) and can_move(d):
				move(d)
				visited[k] = True
				path.append(d)
				moved = True
				break
		if not moved:
			if len(path) == 0:
				return False  # 探索し尽くした（通常は起こらない）
			move(OPPOSITE[path.pop()])
	return True


def run():
	clear()
	while num_items(Items.Gold) < TARGET_GOLD:
		if num_items(Items.Weird_Substance) < substance_amount():
			print("Weird_Substance is not enough")
			return
		make_maze()

		if not REUSE_MAZE:
			go_to_treasure()
			harvest()
		else:
			reuse_count = 0
			while True:
				go_to_treasure()
				before = measure()
				# 上限・物質不足なら収穫して終了
				if reuse_count >= 300 or num_items(Items.Weird_Substance) < substance_amount():
					harvest()
					break
				use_item(Items.Weird_Substance, substance_amount())
				reuse_count += 1
				# 宝が動かなかった（再配置の上限に達した）場合は収穫
				if measure() == before:
					harvest()
					break


run()
