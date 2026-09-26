# かぼちゃのリーダーボードの開始条件を見る（leaderboard_run(Leaderboards.Pumpkins, "pumpkin_lb_probe", 256) で実行）
#   開始時の所持品・盤面の大きさ・機数・地面を書き出してすぐ終わる（記録にはならない）
quick_print("n", get_world_size(), "max_drones", max_drones())
quick_print("かぼちゃ", num_items(Items.Pumpkin), "にんじん", num_items(Items.Carrot))
quick_print("水", num_items(Items.Water), "肥料", num_items(Items.Fertilizer))
quick_print("干し草", num_items(Items.Hay), "木", num_items(Items.Wood), "電力", num_items(Items.Power))
quick_print("足元", get_entity_type(), get_ground_type(), "水の量", get_water())
