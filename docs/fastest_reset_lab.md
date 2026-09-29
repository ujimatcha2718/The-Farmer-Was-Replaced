# 最速リセット：lab の実装・奇妙な物質・金と骨の速さ・Power（調査 2026-09-29）

`docs/fastest_reset_wiki.md` の続きである．lab のリポジトリ（https://github.com/LucasCerattoRS/the-farmer-was-replaced-lab ，`git clone --depth 1` で取得．最新コミット daeba76，2026-09-27）と，wiki（https://thefarmerwasreplaced.wiki.gg/wiki/ページ名?action=raw ）と，Steam の議論・公式リーダーボードを読んだ．
数値は原文から写し，出典を付ける．原文に無い値は「不明」，こちらで計算した値や推し量った値は「推定」と書く．

---

## 0. 要点

1. **lab の `leaderboard_run.py` は1機・盤面 4×4 のまま最後まで進む**（Expand を3回しか買わない．Megafarm・Sunflowers も買わない）．骨は 4×4 を回る固定の閉路で1回 450 個（推定），金は 4×4 の迷路で宝1個 16 個しか取れず，奇妙な物質は肥料をかけたかぼちゃからしか得ない．関数名どおり「Slowest Reset」で，速さの参考にはならない．参考になるのは作りの部品（`unlock_tech`，`sow_tile` など）だけである．
2. **奇妙な物質は，感染した植物の収穫で「その植物の収穫量の半分」が物質になる**．感染は肥料をかけるか，**物質を植物に使うと「そのマスと隣のマスの感染が反転する」**ことで起こる（wiki：Fertilizer）．健康な畑の真ん中に物質を1個使えば，最大5マスが感染する（推定）．1マスの収穫量が大きい畑（合体かぼちゃ，整列したサボテン）では，**使った物質の何倍もの物質が返ってくる**（推定．実機未確認）．肥料（10秒に1個）に頼らずに物質を増やせる見込みがある．
3. 迷路1回の物質は **一辺 × 2^(Mazes の段階 − 1)**，宝1個の金は **面積 × 2^(段階 − 1)**．金／物質 ＝ 一辺なので，**物質が足りない最速リセットでは大きな迷路ほど物質の効率が良い**（推定．式は wiki とこちらの実測）．
4. **Steam の公式リーダーボード**（Fastest Reset，3,782件）の1位は 1,460,604，10位は 2,087,375．単位はミリ秒とみられ（推定），1位は **約24分21秒**，10位は約34分47秒．上位1%は約50分，上位10%は約75分，中央値は約20時間．YouTube には「WORLD RECORD FULL RESET (28:03)」（Josh）がある．
5. **Power**：ひまわりを収穫すると得られ，持っている間はドローンが2倍速で動く．消費は1機あたり 30 動作（6,000 tick）ごとに1．1回の収穫で得られる基本量は wiki に無い（不明）．10本以上あるときに花びらが最多のものを収穫すると8倍になる．Speed 5 では Power 1 で約 0.99 秒，Speed 0 では 7.5 秒の節約になる（推定）．

---

## 1. lab の `farms/leaderboards/leaderboard_run.py`

出典：https://github.com/LucasCerattoRS/the-farmer-was-replaced-lab/blob/main/farms/leaderboards/leaderboard_run.py （244行）．

### 1.1 import するファイル
- **`import` は1つも無い**．1ファイルで完結している．使っている `pet_the_piggy()` は組み込み関数である（`farms/lib/__builtins__.py` 763行）．
- 同じディレクトリの関連ファイル：
  - `fastest_reset.py`：ほぼ同じ内容の古い版．lab のガイド（guides/leaderboard-strategies）によれば，`leaderboard_run.py` はこれに2点を直した版である．(a) 恐竜の前に (0,0) へ戻る，(b) 迷路の探索を「生け垣の上にいる間」ではなく「宝に着くまで」で回す．
  - `launcher.py`：lab の文書では `leaderboard_run(Leaderboards.Fastest_Reset, "leaderboard_run", 1000)` の1行とされている．ただしリポジトリのファイルは **0 バイト**だった．
  - `bone_collector.py`（恐竜リーダーボード用）と `power_collector.py`（ひまわりリーダーボード用）は最速リセットでは使わない（1.5 節）．

### 1.2 大域変数
- `ws = get_world_size()`，`rws = range(ws)`．Expand を買うたびに `unlock_tech` の中で読み直す．
- 迷路用：右手・左手・反対向きの表（`rightOf`，`leftOf`，`oppositeOf`），今の向き `currentDirection`，目標の金 `l`，1回に使う物質の量 `substance`．
- 恐竜用：`dinLoop` ＝ 16 手の移動列（E,N,N,E,S,S,E,N,N,N,W,W,W,S,S,S）．(0,0) から始めると **4×4 の全16マスを1回ずつ通って (0,0) に戻る閉路**になる（こちらで手で追って確かめた）．**盤面が 4×4 のときしか使えない**．

### 1.3 各関数の手順

**`slowest_automation()`（本体）**
1. `get_time()` で開始時刻を取る．
2. `unlock_tech()` を32回，決まった順番で呼ぶ（順番と費用は `docs/fastest_reset_wiki.md` 3 節の表）．Speed 5回，Fertilizer 4回，Carrots・Watering・Trees・Expand 3回，Pumpkins・Grass・Cactus・Dinosaurs 2回，Plant・Mazes・Leaderboard 1回．
3. 経過秒を 日・時・分・秒 に直し，`do_a_flip()`（1秒）のあと `quick_print` で出す．
- 最後の行で「Speed と Plant がどちらも 0 のときだけ実行する」安全装置を掛けている．

**`unlock_tech(tech)`**
1. `get_cost(tech)` の品目ごとに `farm_item(品目, 必要数)` を呼ぶ．
2. `unlock(tech)` が失敗したら，同じ関数を再帰で呼び直す．
3. **毎回 `pet_the_piggy()` を呼ぶ**．lab の measured-numbers では `pet_the_piggy` は **1秒**かかる（Speed の影響なし）．32回で約32秒を無駄にしている（推定）．
4. Expand なら `ws` と `rws` を読み直す．

**`farm_item(item, num)`**：所持数が `num` に届くまで，品目ごとの関数を繰り返す．

| 品目 | 呼ぶ関数 | 内容 |
|---|---|---|
| 干し草 | `farm_grass()` | 盤面全体を東へ・北へと回り，各マスで `sow_tile(True, False, 草)`．水は使わない |
| 木 | Trees があれば `farm_trees()`，なければ `farm_bushes()` | 茂みは**今いる1マスだけ**．木は盤面を回り，`(x+y)%2==0` の市松のマスだけに植える（木は隣に木があると成長が遅いため）．水を使う |
| にんじん | `farm_carrots(不足数)` | 先に `get_resources_for(にんじん, 不足数 // 2^(Carrots−1))` で干し草と木をそろえ，盤面全体に水ありで植える |
| かぼちゃ **と奇妙な物質** | `farm_pumpkins(不足数)` | 下記．物質はかぼちゃの副産物としてしか得ない |
| サボテン | `farm_cactus(不足数)` | かぼちゃをそろえて盤面全体に植える．**整列はしない**．育ったものを1本ずつ収穫する（1本あたり 1² ＝ 1 × 段階の倍率，推定） |
| 骨 | `farm_bones(式)` | 下記 |
| 金 | `farm_gold(num)` | 下記 |

- 盤面の回り方はどれも「各マスで作業 → `move(East)`，1行ごとに `move(North)`」である．端で反対側へ回り込むことを前提にしている．
- Expand を買う前（1×1）は `move` が失敗するだけ（1 tick）で，同じマスで作業を繰り返す．

**`farm_pumpkins(num)`**
1. `get_resources_for(かぼちゃ, num // (2 × 2^(Pumpkins−1)))` でにんじんをそろえる．
2. 盤面全体で `sow_tile(x==0 and y==0, True, かぼちゃ)`．収穫するのは (0,0) で育ち切っているときだけで，合体した大かぼちゃは (0,0) の収穫でまとめて取れる．ほかのマスは，かぼちゃ以外（枯れたかぼちゃなど）があるときだけ収穫して植え直す．
3. **各マスで，肥料を持っていれば `use_item(Items.Fertilizer)` を1回使う**．肥料をかけたかぼちゃは感染し，収穫量の半分が奇妙な物質になる（2 節）．
- つまり物質の供給は肥料の届く速さ（Fertilizer 4 段階で 10秒に8個，推定）で頭打ちになる．

**`farm_cactus(num)`**：`get_resources_for(サボテン, num // 2^(Cactus−1))` のあと，盤面全体で `sow_tile(True, True, サボテン)`．

**`farm_bones(num)`**
- 呼び出し側の引数は `((不足の骨) // (ws²−1)²) × (ws²−1) × 2^(Dinosaurs−1) // 4 × 2` という式である．意味ははっきりしない（推定：必要なリンゴの数の見積もりのつもり）．
- 中では `get_resources_for(リンゴ, num // 2^(Cactus−1))` を呼んでサボテンをそろえる．割る数が Dinosaurs ではなく **Cactus の段階**になっている（書き間違いとみられる．推定）．
- `clear()` → (0,0) へ戻る → `change_hat(Hats.Dinosaur_Hat)` → `dinLoop` を `move` が失敗するまで繰り返す → `change_hat(Hats.Straw_Hat)` で尾を収穫する．
- リンゴの位置は見ずに，4×4 の閉路を回り続ける．盤面が埋まると `move` が失敗して終わる．
- **1回の骨**：尾の長さ 15 で 15² × 2^(Dinosaurs−1) ＝ 225 × 2 ＝ **450**（Dinosaurs 2 段階．倍率は推定）．骨 2,000,000 には **約4,445回**（推定）．1回にリンゴ15個 × サボテン2個（Dinosaurs 2 段階のリンゴの値段．こちらの reset_levels_probe で実測）＝ 30 個のサボテンを使う．

**`farm_gold(limit)`**
1. `substance = get_world_size() × 2^(Mazes−1)`（4×4・Mazes 1 なら 4）．
2. `clear()` したあと，金が目標未満で物質が足りる間：茂みを植える → 物質を使って迷路を作る → `search_maze()`．
3. 物質が尽きたら `clear()` し，`farm_item(物質, (目標 − 金) // (ws² / substance))`，つまり「足りない金 ÷ 物質1個あたりの金」だけ物質を集める（4×4 なら 1 個あたり 4 金）．
- **迷路は使い回さない**（毎回収穫して作り直す）．宝1個の金は 16．金 1,000,000 には宝 62,500 個・物質 250,000 個（推定）．

**`search_maze()`**：右手法．右へ曲がれれば曲がり，だめならまっすぐ，だめなら左，だめなら引き返す．宝の上に来たら `harvest()`．その後の「まだ宝の上なら再配置」の部分は，収穫で宝が消えているので実行されない（推定）．

**`sow_tile(to_harvest, water, entity)`**（「このマスを entity にする」冪等な部品）
1. （`to_harvest` かつ育ち切っている）か，別の植物があれば `harvest()`．
2. 地面が合わなければ `till()`（草・茂みは草地，それ以外は畑）．
3. `water` が真で Watering 済みで畑なら，**水の量が 0.5 未満で水を持っている間，水を使い続ける**（1タンク 0.25）．
4. 目的の植物でなければ `plant(entity)`．

**`get_resources_for(item, nb = ws²)`**
1. 足元の植物が育つまで（空か枯れたかぼちゃなら待たない）何もせずに待つ．
2. `nb = max(ws², nb)`．
3. `get_cost(item)` の品目ごとに，所持が `費用 × nb` 未満なら `farm_item` で集める．盤面1枚ぶんの種をまとめて用意し，植える途中で止まらないようにしている．

### 1.4 盤面・機数・水・肥料のまとめ
| 項目 | lab の経路 |
|---|---|
| 盤面 | Expand 3 回．こちらの実測（CLAUDE.md 5c）で 1 → 3 → 3 → **4×4** |
| 機数 | **1機**（Megafarm を買わない．`spawn_drone` を使わない） |
| 水 | にんじん・木・かぼちゃ・サボテンで，水の量が 0.5 未満なら使う．Watering は 3 段階 |
| 肥料 | かぼちゃにだけ，持っていれば毎マス1回．目的は奇妙な物質を得ること．Fertilizer は 4 段階（木 54,000 が最も高い買い物） |
| Power | 使わない（Sunflowers を買わない） |
| 迷路 | 4×4，Mazes 1，右手法，使い回しなし |
| 恐竜 | 4×4 の固定閉路，リンゴを追わない |
| かかった時間 | 書かれていない（不明）．関数名は `slowest_automation`，出力の見出しは「Slowest Reset」 |

### 1.5 同じディレクトリのほかのスクリプト（参考）
- `bone_collector.py`：恐竜リーダーボード用．`import no_polyculture_solo` でサボテンを集めるが，**そのファイルはリポジトリに無い**．リンゴを追う段階（stage1）と蛇行の段階（stage2）を，尾の長さ `length` に応じた `offset` で切り替える．1機．
- `power_collector.py`：ひまわりリーダーボード用．各機が東へ1マス動いてから次の機体を生成し，1列ずつ受け持つ．各機は北へ進みながら「育っていれば収穫 → ひまわりを植える → 水」を繰り返す．**花びらは見ていない**．
- `crops/weird_substance_polyculture.py`：32×32・8機．`get_companion()` が求める植物を植えて肥料をかけ，草・茂み・木・にんじん以外のもの（コメントでは「物質」）があれば収穫する．物質の量や速さの記録は無い（不明）．

---

## 2. 奇妙な物質（Weird_Substance）

### 2.1 wiki の原文（要点）
出典：https://thefarmerwasreplaced.wiki.gg/wiki/Fertilizer ，https://thefarmerwasreplaced.wiki.gg/wiki/Items
- 肥料は水と同じく **10秒ごとに1個**届き，強化ごとに2倍（Fertilizer）．
- `use_item(Items.Fertilizer)` は足元の植物の残りの成長時間を **2秒** 減らす．
- **肥料で育てた植物は感染する．感染した植物を収穫すると，収穫量の半分が `Items.Weird_Substance` になる．**
- **物質を植物に使うと，その植物と隣り合うすべての植物の感染が反転する**（"toggling the infected status of the plant and all adjacent plants"）．感染した植物に使えば治り，健康な植物に使えば感染する．感染した植物の隣が健康なら，その植物は治り，隣は感染する（逆も同じ）．
- Items：「茂みに使うと迷路が育つ．ほかの植物に使うと感染が反転する．感染した植物から得られる．肥料をかけると感染する．」
- 感染しているかを調べる関数は無い（Steam：https://steamcommunity.com/app/2060160/discussions/0/684112827030444383/ の回答「知る限り無い．肥料と物質を使ったマスを自分で覚えておくしかない」）．
- `use_item(item, n)` は「item を n 回使う」（Tooltips_Code）．成功で 200 tick．

### 2.2 こちらの実測（CLAUDE.md 5b，かぼちゃ・通常プレイ）
- 1マスに肥料1回 → かぼちゃ 256・物質 256（1マスの 512 の半分ずつ）．
- 6×6 の1マスだけ肥料 → かぼちゃ 109,056・物質 1,536．**減るのは感染したマスの取り分（3,072）の半分だけ**で，合体したほかのマスには影響しない．合体も妨げない．
- 感染したマスに物質を使うと治った（収穫が 110,592・0 に戻った）．

### 2.3 物質を増やす方法（推定．実機未確認）
**(a) 肥料だけ（lab の方法）**：物質の量 ＝ 肥料の数 × 1マスの取り分 ÷ 2．肥料は Fertilizer 4 段階でも 10秒に8個（推定）しか届かない．
- lab の 4×4 なら，合体かぼちゃ（Pumpkins 2 段階）は 4³ × 2 ＝ 128，1マスの取り分 8，物質 4．250,000 個には肥料 62,500 個，約 78,000 秒（約22時間，推定）かかる．

**(b) 物質で感染を広げる**：健康な畑の真ん中で物質を1個使うと，そのマスと上下左右の最大5マスが感染する（推定．「adjacent」が上下左右の4方向か，斜めを含む8方向かは不明）．
- 収穫で返ってくる物質は「感染したマス数 × 1マスの取り分 ÷ 2」．取り分が 0.4 を超えれば，使った物質より多く返る（5 × 取り分 ÷ 2 > 1，推定）．
- 反転なので，同じマスを2回反転させると治ってしまう．十字（中心＋上下左右）がちょうど畑を敷き詰める置き方は `(x + 2y) % 5 == 0` のマスに使うことである（盤面の一辺が5の倍数で端で回り込むなら全マスがちょうど1回反転する．回り込まない場合は端に補いが要る．推定）．必要な物質と `use_item` の回数は畑のマス数の約1/5．
- 1マスの取り分の目安（段階の倍率を m とする．推定）：

| 畑 | 収穫量 | 1マスの取り分 | 全マス感染での物質 |
|---|---|---|---|
| 茂み1本 | m | m | m／2 |
| 木1本 | 5m | 5m | 2.5m |
| かぼちゃ 6×6 以上（n×n） | 6n²m | 6m | 3n²m |
| かぼちゃ 4×4 | 64m | 4m | 32m |
| 整列したサボテン n×n（n² 本の連鎖） | (n²)²m | n²m（取り分が均等なら） | n⁴m／2 |

- **サボテンの連鎖収穫で感染がどう効くかは不明**．かぼちゃと同じく「感染したマスの取り分の半分」なら，32×32 を全部感染させた整列サボテン（Cactus 2 段階で m=2）は 1024² × 2 ÷ 2 ＝ **約105万個の物質**になる（推定）．感染したサボテンが連鎖するか，整列の判定に影響するかも不明．
- かぼちゃの合体・サボテンの連鎖のどちらも，こちらの実測（2.2）と同じ「取り分」の考え方が当てはまるかを probe で確かめる必要がある．

**(c) 物質の量の見積もり（推定）**：迷路の物質は 3 節．Mazes 1 のアンロック自体にも物質 1,000 が要る．

### 2.4 迷路1回に要る物質
出典：https://thefarmerwasreplaced.wiki.gg/wiki/Mazes
- **物質 n 個で n×n の迷路**．Mazes の段階が1つ上がるごとに宝も物質も2倍．盤面いっぱいの迷路は `get_world_size() × 2^(num_unlocked(Unlocks.Mazes) − 1)`．
- 宝の金は **迷路の面積**（5×5 で 25）．Entities のページは「一辺の長さ」と書いていて食い違うが，こちらの実測（8×8・段階6で 2,048 ＝ 64 × 32）は面積の方と合う．
- 宝の上で同じ量を使うと再配置（最大300回）．再配置1回ごとに同じ量の物質を使う．「使い回しても，収穫して作り直すより多くの金はもらえない」（Mazes）．
- Tooltips_Code の `num_unlocked` の例は `get_world_size() * num_unlocked(Unlocks.Mazes)` と書いていて，Mazes のページ（2^(段階−1)）と食い違う．こちらの実機（CLAUDE.md 3.4）は 2^(段階−1) と合う．
- Steam（https://steamcommunity.com/app/2060160/discussions/0/591767767138452059/ ）：「物質の量は Mazes の段階ごとに2倍になるので，1×1 の迷路の古いコードは段階1でしか動かない」．
- **金／物質 ＝ 一辺**（段階によらない）．同じ金に要る物質は一辺に反比例する．金 1,000,000 に要る物質：一辺 4 で 250,000，8 で 125,000，16 で 62,500，32 で 31,250（推定）．

---

## 3. 金（迷路）と骨（恐竜）の速さ・記録の目安

### 3.1 lab の文書から
- **measured-numbers**（https://lucascerattors.github.io/the-farmer-was-replaced-lab/mechanics/measured-numbers/ ）：金や骨の速さの数値は無い．載っているのは tick 費用の表だけである．
  - 0 tick：`get_tick_count()`，`get_time()`，`quick_print()`．
  - 1 tick：`can_harvest`，`can_move`，`get_pos_x/y`，`get_world_size`，`get_entity_type`，`get_ground_type`，`get_water`，`num_items`，`get_companion`，`measure`，`has_finished`，`max_drones`，`num_drones`，`get_cost`，`num_unlocked`，`random`，`abs`，`len`，`str`，`range`，`list.append`，`set.add`．
  - 常に 200 tick：`till`，`clear`，`change_hat`，`set_execution_speed`，`set_world_size`，`simulate`，`leaderboard_run`．
  - 成功で 200，失敗で 1：`harvest`，`plant`，`swap`，`use_item`，`move`，`spawn_drone`，`unlock`．
  - 可変：`list.insert(i,x)` は 1 + len − i，`wait_for` は 1 + 相手の残り tick．
  - **秒で決まる：`print`，`do_a_flip`，`pet_the_piggy` は各1秒．**
  - 未測定（⏳）として，成長時間，かぼちゃの枯れる割合，花びらの分布，サボテンの収穫量，木の隣接の遅れ，肥料の2秒が挙がっている．
- **leaderboard-strategies**（https://lucascerattors.github.io/the-farmer-was-replaced-lab/guides/leaderboard-strategies/ ）：最速リセットは `leaderboard_run.py` を「そのまま真似る価値がある作り」と紹介しているだけで，時間の記録は無い．迷路は「小さな迷路をたくさん回す方が大きな迷路1つより速い」．
  - ただしこれは物質が無限にある迷路リーダーボードの話である．最速リセットでは物質が足りないので，2.4 節の「金／物質 ＝ 一辺」から大きな迷路の方が有利になりうる（推定）．
- **lab の文書の誤り**（wiki やこちらの実測と合わない）：ひまわりの倍率を「5倍」，花びらを「1〜15」としている（wiki は8倍，7〜15）．かぼちゃを「合体した個数の3乗」としている（wiki は一辺の3乗，6以上は n²×6）．リーダーボードの目標も一部違う（`docs/fastest_reset_wiki.md` 6 節）．lab の数値は wiki より信頼度が低い．

### 3.2 Steam の議論から
- 1×1 の迷路を使い回して金を取るスクリプト：「最高速・Mazes 最大・Power 満タンでも **約150 金／秒**」（Uncoelacanth，2026-09-20，https://steamcommunity.com/app/2060160/discussions/0/591767767138452059/ ）．1×1 は物質1個あたり金1個しか出ないので，最速リセットには向かない（推定）．
- 最速リセット用の全自動スクリプト（Vellthar，2026-08-07，https://steamcommunity.com/app/2060160/discussions/0/580552862448447474/ ）：「最悪のコードだが動く．10〜30分くらい（計っていない．推測）」．順番は Speed・Expand → Plant → Carrots → Trees → Sunflowers → Fertilizer → Watering → Pumpkins → Cactus → Mazes → Hats → Dinosaurs → 金と骨を集める．ただしコメントに「物質は木に肥料をかけて得る．肥料はにんじんの収穫の副産物」とあり，wiki（肥料は時間で届く）と合わない．時間の主張も「推測」と本人が書いているので，信頼できない．
- 「Full Automation」の実績は「full reset のリーダーボードに載る」ことで，時間は問わない（https://steamcommunity.com/app/2060160/discussions/0/662719183492280409/ ）．

### 3.3 公式リーダーボード（Steam）
出典：https://steamcommunity.com/stats/2060160/leaderboards/?xml=1 と各リーダーボードの `?xml=1&start=1&end=3000`（2026-09-29 取得）．
- 16 のリーダーボードがある．Fastest Reset は `fastest_reset_multi`（ID 17869903），3,782件．並べ方は昇順（小さいほど良い）．
- **スコアの単位はミリ秒とみられる**（推定）．根拠：YouTube の「WORLD RECORD FULL RESET (28:03)」＝ 1,683 秒が，Fastest Reset の上位の値（1,460,604〜2,087,375）と同じ桁になる．また，こちらのサボテン実測 196,016 tick を 6,075 tick／秒で割った 32.3 秒が，Cactus の上位1%（31,651）と同じ桁になる．
- Fastest Reset（上位3,000件から計算．分はミリ秒とみなした推定）：

| 順位・割合 | スコア | 分：秒（推定） |
|---|---|---|
| 1位 | 1,460,604 | 24:21 |
| 2位 | 1,490,234 | 24:50 |
| 3位 | 1,668,860 | 27:49 |
| 10位 | 2,087,375 | 34:47 |
| 30位 | 約3,000,000 | 約50:00 |
| 上位1% | 3,007,492 | 50:07 |
| 上位10% | 4,497,183 | 74:57 |
| 中央値 | 73,465,299 | 約20時間 |

- 記録は「2時間以上走らせ，全回の平均」である（wiki：Leaderboard）．30分なら約4回の平均になる（推定）．
- 参考：ほかのリーダーボードの上位（ミリ秒とみなした推定）．Maze 1位 5,056，上位1% 95,698．Dinosaur 1位 227,942，上位1% 676,329．Cactus 1位 7,184，上位1% 31,651．こちらの実測を 6,075 tick／秒で秒に直すと（推定），サボテン 32.3 秒で約23位／2,063，迷路 117.7 秒で約52位／1,609，恐竜 933.7 秒で約162位／1,569 に当たる．各リーダーボードの最上位の数件は桁違いに小さく，今の規則でどう出したかは不明である．

### 3.4 YouTube（題名だけ．説明文はこの環境から読めなかった）
noembed（https://noembed.com/ ）で題名と投稿者だけを取れた．YouTube 本体は 429（回数制限）で開けなかった．
- 「The Farmer Was Replaced 1.0 WORLD RECORD (38:48)」（Josh，https://www.youtube.com/watch?v=lIS41aXwhdQ ）．
- 「The Farmer Was Replaced SUB 32 FULL RESET (WORLD RECORD)」（Josh，https://www.youtube.com/watch?v=HR-OQ8GzwVk ）．
- 「The Farmer Was Replaced WORLD RECORD FULL RESET (28:03)」（Josh，https://www.youtube.com/watch?v=hdBSvuOim74 ）．検索の要約では2025年11月の投稿で，「このリセットの3本目で，たぶん最後」とされている（要約からの引用．未確認）．
- 「The Farmer Was Replaced - Fastest Reset leaderboards: first success」（J4，https://www.youtube.com/watch?v=INdQg4IxnMA ）．
- 1.0（2025-10-10 の大型更新．SteamDB の題名 "Version 1.0 is Here! – Multiple Drones, New Unlock Tree and more!"）の後，38:48 → 32分未満 → 28:03 → 今の1位 24:21（推定）と縮んできたことになる．

### 3.5 骨と金の量の見積もり（推定．こちらの計算）
- 骨：盤面を埋めた尾の長さは w²−1，1回の骨は (w²−1)² × 2^(Dinosaurs−1)（倍率は推定）．Dinosaurs 2 段階で w=4：450，w=8：7,938，w=16：130,050，w=22：466,578，w=32：2,093,058（1回で 200万に届く）．
- リンゴの値段（Dinosaurs 2 段階）はサボテン2個（こちらの実測）．w=32 を1回埋めるリンゴ 1,023 個でサボテン 2,046 個．
- 恐竜リーダーボード（全アンロック，Dinosaurs 6 段階，32×32）のこちらの実測は 5,672,334 tick（6,075 tick／秒で約934秒，推定）．最速リセットでは Speed 5 まで買えるが，Power が無ければ 3,037.5 tick／秒なので，同じ手順でも約1,870秒かかる（推定）．`move` の費用（400 から始まりリンゴ1個ごとに3%減る）は段階によらないので，骨の時間は主に盤面の広さと Speed・Power で決まる（推定）．
- 金：宝1個 ＝ 面積 × 2^(Mazes−1)．Mazes 1 で 32×32 なら 1,024 金／宝，金 1,000,000 に宝 977 個・物質 31,250（推定）．迷路リーダーボードのこちらの実測（32機・8×8×16・Mazes 6）は宝 4,816 個で約 118 秒（推定）．

---

## 4. ひまわりと Power

出典：https://thefarmerwasreplaced.wiki.gg/wiki/Sunflowers ，https://thefarmerwasreplaced.wiki.gg/wiki/Execution_Details ，https://thefarmerwasreplaced.wiki.gg/wiki/Items ，Unlocks_Data（`docs/fastest_reset_wiki.md` 2 節）．

### 4.1 wiki の原文（要点）
- 植え方はにんじん・かぼちゃと同じ（畑に植える）．育ち切ったひまわりを収穫すると Power が得られる．
- `measure()` は花びらの数を返す．**花びらは 7〜15 枚**．育つ前でも測れる．
- **畑に10本以上あり，花びらが最多のものを収穫すると Power が8倍**．花びらがもっと多いひまわりが残っているのに収穫すると，**次に収穫するものも**通常の量になる．最多が複数あればどれを収穫してもよい．
- **Power がある間，ドローンは2倍速で動く**．**30 動作（move・harvest・plant など）ごとに Power を1使う**．ほかの文の実行も Power を使うが，ずっと少ない．
- Speed の強化で速くなるものは Power でも速くなる．Power で速くなるものは，Speed の強化を無視した「かかる時間」に比例して Power を使う．
- Execution_Details：Power 1 は 30 動作，つまり **6,000 tick** ぶんもつ．tick は一定の速さで進むので，**コードが動いている間は1機ごとに一定の速さで Power を使う**．速さは Speed の段階に比例する．
- Speed と Power の tick／秒：Speed 0 で 400／800，Speed 5 で 3,037.5／6,075（Power で2倍）．
- 費用：Sunflowers のアンロックはにんじん 500 の1段だけ（Unlocks_Data）．説明には「強化：ひまわりから得る Power が増える」とあるが，強化の段は表に無い．植える費用は全段階を上げた状態でにんじん1個（Entity_Planting_Costs）．
- 成長時間：5.6〜8.4 秒，平均 7.0（Plant_growth）．

### 4.2 分かっていないこと（不明）
- **1回の収穫で得る Power の基本量**（wiki にも lab にも無い）．
- Power が複数機で共有されるか（所持品は共有なので共有と推定）．1機ごとに消費するので，32機なら32倍の速さで減る（推定）．
- 待ち（`pass` のループや `wait_for`）でも Power を使うか．「コードが動いている間」とあるので使うと推定．
- 成長時間は秒で決まる（こちらの reset_yield_probe では，Speed を上げても成長の秒はほぼ同じだった）．Power で成長が速くなるかは不明（成長は tick ではなく秒なので，速くならないと推定）．

### 4.3 最速リセットでの損得の見積もり（推定）
- Power 1 は 6,000 tick ぶんの動作を2倍速にする．節約できる時間は 6,000 ÷ (2 × Power なしの tick／秒)．Speed 0 で 7.5 秒，Speed 3 で 2.2 秒，**Speed 5 で約 0.99 秒**．
- Speed 5・Power ありでは1機が実時間1秒あたり約1個（6,075 ÷ 6,000）の Power を使う．1機で25分（1,500秒）ずっと Power を使うなら約1,500個が要る（推定）．
- 元が取れるかは，収穫1回の Power（不明）と，ひまわりを植えて育てて収穫する手間（植える・収穫で 400 tick ＋ 移動．成長 約7秒）で決まる．probe で「1回の収穫の Power（8倍なし／あり）」を測るまで判断できない．

---

## 5. 次に probe で確かめること（提案）

1. **感染の反転の範囲**：健康な畑（例：5×5 の茂み）の中央で `use_item(Items.Weird_Substance)` を1回使い，各マスを収穫して物質が出るマスを数える（4方向か8方向か，端での回り込みがあるか）．
2. **物質の収益**：全マスを感染させた 4×4・6×6 の合体かぼちゃと，整列した n×n のサボテンを収穫したときの物質の量（連鎖の取り分の決まり方，感染したサボテンが連鎖するか）．
3. **肥料の届く速さ**：Fertilizer 1〜4 段階で `simulate` し，一定秒数での肥料の増え方を測る（10秒に 2^(段階−1) 個か）．
4. **Power**：Sunflowers 1 段階でひまわりを10本以上植え，最多の花びらのものとそれ以外を収穫して Power の増え方を測る．Power がある間の tick／秒と消費も測る．
5. **骨の倍率**：Dinosaurs 1・2 段階で小さな盤面を埋め，骨が (長さ)² × 2^(段階−1) かを確かめる．

---

## 6. 出典

- lab：https://github.com/LucasCerattoRS/the-farmer-was-replaced-lab （`farms/leaderboards/leaderboard_run.py`，`fastest_reset.py`，`bone_collector.py`，`power_collector.py`，`launcher.py`，`farms/crops/weird_substance_polyculture.py`，`farms/lib/__builtins__.py`，`docs/en/mechanics/measured-numbers.md`，`docs/en/guides/leaderboard-strategies.md`，`docs/en/guides/progression.md`，`docs/en/mechanics/leaderboards.md`，`mazes.md`，`dinosaurs.md`，`crops.md`，`polyculture.md`）．サイト版は https://lucascerattors.github.io/the-farmer-was-replaced-lab/ ．
- wiki（`?action=raw`）：Fertilizer，Items，Mazes，Dinosaurs，Sunflowers，Cactus，Pumpkins，Leaderboard，Polyculture，Watering，Megafarm，Execution_Details，Timing，Simulation，Tooltips_Code，Entities，Entity_Planting_Costs．wiki に Weird_Substance・Infection・Power・Apple・Treasure という名前のページは無い（404）．全ページの一覧は `api.php?action=query&list=allpages` で確認した．
- Steam の議論：https://steamcommunity.com/app/2060160/discussions/0/662719183492280409/ ，https://steamcommunity.com/app/2060160/discussions/0/580552862448447474/ ，https://steamcommunity.com/app/2060160/discussions/0/682988089947254137/ ，https://steamcommunity.com/app/2060160/discussions/0/591767767138452059/ ，https://steamcommunity.com/app/2060160/discussions/0/684112827030444383/ ．
- Steam の公式リーダーボード：https://steamcommunity.com/stats/2060160/leaderboards/?xml=1 ．
- YouTube（題名のみ）：上の 3.4 節．
