# 8x8 の迷路で，再配置のたびに壁がどれくらい消えるかを確かめる実験（通常プレイの空いている畑で実行）
#   迷路を作った直後は木なので通路（開いている辺）は 63 本のはず．再配置を 300 回まで繰り返し，
#   途中で全マスを歩いて通路の数を数え直す．増えたぶんが消えた壁の数である．
#   あわせて，木の経路（最初の通路だけ）と，その時点で分かっている通路での最短経路の長さの平均を出す
#   （近道を使うと宝1個あたり何歩減るかの目安）．
#   出力：quick_print（出力ページ）

M = 8

DX = {North: 0, East: 1, South: 0, West: -1}
DY = {North: 1, East: 0, South: -1, West: 0}
OPP = {North: South, South: North, East: West, West: East}

def unit():
	return 2 ** (num_unlocked(Unlocks.Mazes) - 1)

def goto(tx, ty):
	while get_pos_x() < tx:
		move(East)
	while get_pos_x() > tx:
		move(West)
	while get_pos_y() < ty:
		move(North)
	while get_pos_y() > ty:
		move(South)

def key(x, y):
	return x * 100 + y

def count_edges(adj):
	# 迷路内を DFS で全部歩き，各マスで4方向の can_move を調べて adj を更新する．
	# 出発点に戻る．戻り値：開いている辺の数
	seen = {}
	back = []
	x = get_pos_x()
	y = get_pos_y()
	seen[key(x, y)] = True
	while True:
		x = get_pos_x()
		y = get_pos_y()
		k = key(x, y)
		if not (k in adj):
			adj[k] = {}
		for d in [North, East, South, West]:
			if can_move(d):
				adj[k][key(x + DX[d], y + DY[d])] = d
		moved = False
		for d in [North, East, South, West]:
			if not moved:
				nk = key(x + DX[d], y + DY[d])
				if nk in adj[k]:
					if not (nk in seen):
						seen[nk] = True
						move(d)
						back.append(OPP[d])
						moved = True
		if not moved:
			if len(back) == 0:
				e = 0
				for a in adj:
					for b in adj[a]:
						e += 1
				return e // 2
			move(back.pop())

def bfs_path(adj, s, t):
	# adj 上の最短経路（向きのリスト）
	prev = {}
	prev[s] = None
	q = [s]
	h = 0
	while h < len(q):
		c = q[h]
		h += 1
		if c == t:
			out = []
			while prev[c] != None:
				p = prev[c]
				out.append(adj[p][c])
				c = p
			res = []
			i = len(out) - 1
			while i >= 0:
				res.append(out[i])
				i -= 1
			return res
		for nb in adj[c]:
			if not (nb in prev):
				prev[nb] = c
				q.append(nb)
	return None

def copy_adj(adj):
	c = {}
	for a in adj:
		c[a] = {}
		for b in adj[a]:
			c[a][b] = adj[a][b]
	return c

clear()
goto(8, 8)
if get_entity_type() != None:
	harvest()
plant(Entities.Bush)
sub = M * unit()
quick_print("use_item", use_item(Items.Weird_Substance, sub))
adj = {}
e0 = count_edges(adj)
tree = copy_adj(adj)
quick_print("reloc", 0, "edges", e0)

checks = [10, 25, 50, 100, 150, 200, 250, 299]
ci = 0
sum_tree = 0
sum_best = 0
n = 0
r = 0
while r < 299:
	t = measure()
	s = key(get_pos_x(), get_pos_y())
	tk = key(t[0], t[1])
	pt = bfs_path(tree, s, tk)
	pb = bfs_path(adj, s, tk)
	sum_tree += len(pt)
	sum_best += len(pb)
	n += 1
	for d in pb:
		move(d)
	use_item(Items.Weird_Substance, sub)
	r += 1
	if ci < len(checks):
		if r == checks[ci]:
			e = count_edges(adj)
			quick_print("reloc", r, "edges", e, "avg tree", sum_tree / n, "avg best", sum_best / n)
			ci += 1
t = measure()
pb = bfs_path(adj, key(get_pos_x(), get_pos_y()), key(t[0], t[1]))
for d in pb:
	move(d)
harvest()
quick_print("done tick", get_tick_count())
