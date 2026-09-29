# reset_yield_probe.py から simulate で呼ばれる（盤面の大きさと機数を1行で出す）
quick_print("S Expand", num_unlocked(Unlocks.Expand), "Megafarm", num_unlocked(Unlocks.Megafarm), "size", get_world_size(), "drones", max_drones())
