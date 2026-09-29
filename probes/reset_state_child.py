# reset_levels_probe.py から simulate で呼ばれる．アンロックの段階を指定した状態の値を出す
# （単独で実行してもよい．何も変えない）
quick_print("L", num_unlocked(Unlocks.Expand), num_unlocked(Unlocks.Megafarm), num_unlocked(Unlocks.Carrots), num_unlocked(Unlocks.Pumpkins), num_unlocked(Unlocks.Cactus), num_unlocked(Unlocks.Dinosaurs), num_unlocked(Unlocks.Speed))
quick_print("W", get_world_size())
quick_print("D", max_drones())
quick_print("C", get_cost(Entities.Carrot), get_cost(Entities.Pumpkin), get_cost(Entities.Cactus), get_cost(Entities.Apple))
