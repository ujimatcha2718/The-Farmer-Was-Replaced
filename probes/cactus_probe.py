# サボテンの植え直しが使えるかを確かめる小さな実験
#   1) 植えた直後に measure() が値を返すか
#   2) 育ち切るまで何 tick かかるか
#   3) 育つ前に harvest() すると消えるか（植え直せるか）
# 空いている畑の上で実行すること
clear()
till()
plant(Entities.Cactus)
t1 = get_tick_count()
quick_print("measure直後", measure(), "can_harvest", can_harvest(), "植付から", get_tick_count() - t1)
w = 0
while not can_harvest():
	w += 1
quick_print("育ち切るまで", get_tick_count() - t1, "measure", measure())
harvest()                        # 育ったものを片付ける
# 未成熟で収穫すると消えて植え直せるか
plant(Entities.Cactus)
a = measure()
harvest()                        # 育つ前に収穫
quick_print("未成熟収穫後の measure", measure(), "（None なら消えている）")
ok = plant(Entities.Cactus)
quick_print("植え直し", ok, "前の値", a, "新しい値", measure(), "地面", get_ground_type())
