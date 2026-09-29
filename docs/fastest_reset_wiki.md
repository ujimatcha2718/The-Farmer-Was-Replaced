# 最速リセット（Leaderboards.Fastest_Reset）の wiki 調査（2026-09-29）

ネットワークの許可（ユーザーが設定）のあと，wiki 本体と lab のガイドを読んだ．wiki は `?action=raw` で生テキストを取り，数値はそこから写した．
読んだページは 8 節にまとめた．wiki に無い値は「不明」，こちらで計算した値や推し量った値は「推定」と書く．

---

## 1. 結論（先に要点）

- **Leaderboard の費用は `{Items.Bone: 2000000, Items.Gold: 1000000}`**（骨 200万・金 100万）．そのほかのアンロックの費用は合わせても木 約7万，かぼちゃ 2.5万といった桁で，**骨と金が費用のほとんどを占める**（推定．下の表の合計から）．
- アンロックは自動では進まない．`unlock(Unlocks.X)` を呼ぶ（成功で 200 tick，失敗で 1 tick）か，研究ツリーのボタンを押す．
- **記録は tick ではなく時間（秒）で測る**（推定．`simulate()` は秒を返し，リーダーボードは「fastest times」である）．Speed の強化とひまわりの Power で 1 tick の長さが縮むので，他のリーダーボードと違って速度の強化そのものが記録に効く．
- 言語の機能（変数・ループ・関数・リスト・辞書など）は，シミュレーションでは常に使える（Simulation のページ）．lab の実例も言語のアンロックを1つも買っていない．
- **アンロックの前提（技術ツリーの親）は wiki に無い（不明）．** lab の実例が実際に通った順番（3 節）が，前提を満たす順の例になる（推定）．
- 盤面の大きさ（Expand の各段階で何マスになるか）と，Megafarm の段階ごとの機数は wiki に無い（不明）．

---

## 2. アンロックの一覧と段階ごとの費用

出典：https://thefarmerwasreplaced.wiki.gg/wiki/Unlocks_Data （費用．`GetUnlocksData()` のとおり），https://thefarmerwasreplaced.wiki.gg/wiki/Unlocks （効果．英文をそのまま）．
段階は1段目（最初の解放）から順に並べた．

| Unlocks.X | 効果（原文） | 段階ごとの費用 |
|---|---|---|
| Auto_Unlock | Automatically unlock things. | Pumpkin 5000 |
| Cactus | Unlock: Cactus! / Upgrade: Increases the yield and cost of cactus. | Pumpkin 5000, 20000, 120000, 720000, 4320000, 25900000 |
| Carrots | Unlock: Till the soil and plant carrots. / Upgrade: Increases the yield and cost of carrots. | Wood 50, 250, 1250, 6250, 31200, 156000, 781000, 3910000, 19500000, 97700000 |
| Costs | Allows access to the cost of things. | Pumpkin 2500 |
| Debug | Tools to help with debugging programs. | Hay 50 + Wood 50 |
| Debug_2 | Functions to temporarily slow down the execution and make the farm smaller. | Gold 500 |
| Dictionaries | Get access to dictionaries and sets. | Pumpkin 2500 |
| Dinosaurs | Unlock: Majestic ancient creatures. / Upgrade: Increases the yield and cost of dinosaurs. | Cactus 2000, 12000, 72000, 432000, 2590000, 15600000 |
| Expand | Unlock: Expands the farm land and unlocks movement. / Upgrade: Expands the farm. This also clears the farm. | Hay 30 → Wood 20 → Wood 30 + Carrot 20 → Wood 100 + Carrot 50 → Pumpkin 1000 → Pumpkin 8000 → Pumpkin 64000 → Pumpkin 512000 → Pumpkin 4100000 |
| Expand_2 | 同じ Expand の系列の続き（Unlocks_Data には別の項目が無い．`Unlocks` の列挙には `.Expand_2` がある） | 不明 |
| Fertilizer | Unlock: Grow plants instantly. / Upgrade: Receive more fertilizer. | Wood 500, 1500, 9000, 54000 |
| Functions | Define your own functions. | Carrot 40 |
| Grass | Increases the yield of grass. | Hay 100, 300 → Wood 500, 2500, 12500, 62500, 312000, 1560000, 7810000, 39100000 |
| Hats | Hats for your drone. | Hay 50 |
| Import | Import things from other files. | Carrot 80 |
| **Leaderboard** | Enter the leaderboard for the fastest times. | **Bone 2000000 + Gold 1000000** |
| Lists | Use lists to store lots of values. | Carrot 500 |
| Loops | Unlocks a simple while loop. | Hay 5 |
| Mazes | Unlock: A maze with a treasure in the middle. / Upgrade: Increases the gold in treasure chests and the amount of weird substance needed to spawn a maze. | Weird_Substance 1000 → Cactus 12000, 72000, 432000, 2590000, 15600000 |
| Megafarm | Unlock: More drones! / Upgrade: Increase drone count further. | Gold 2000, 8000, 32000, 128000, 512000 |
| Operators | Arithmetic, comparison and logic operators. | Hay 150 + Wood 10 |
| Plant | Unlocks planting. | Hay 50 |
| Polyculture | Unlock: Use companion planting to increase the yield. / Upgrade: Increases the yield multiplier of polyculture. | Pumpkin 3000 → Bone 10000, 50000, 250000, 1250000 |
| Pumpkins | Unlock: Pumpkins! / Upgrade: Increases the yield and cost of pumpkins. | Wood 500 + Carrot 200 → Carrot 1000, 4000, 16000, 64000, 256000, 1020000, 4100000, 16400000, 65500000 |
| Senses | The drone can see what's under it and where it is. | Hay 100 |
| Simulation | Test faster and under reproducible conditions. | Gold 5000 |
| Speed | Increases the speed of both the drone and code execution. | Hay 20 → Wood 20 → Wood 50 + Carrot 50 → Carrot 500 → Carrot 1000 |
| Sunflowers | Unlock: Sunflowers and Power. / Upgrade: Increases the power gained from sunflowers. | Carrot 500 |
| The_Farmers_Remains | 隠しアンロック（ゲーム内では ????????? と表示） | Bone 100000000 |
| Timing | It's about time! | Pumpkin 1000 |
| Top_Hat | 隠しアンロック．"A very fancy hat that only the best drones get to wear." | Hay 1000000000 + Wood 10000000000 + Carrot 1000000000 + Cactus 1000000000 + Gold 100000000 |
| Trees | Unlock: Unlocks trees. / Upgrade: Increases the yield of bushes and trees. | Wood 50 + Carrot 70 → Hay 300, 1200, 4800, 19200, 76800, 307000, 1230000, 4920000, 19700000 |
| Utilities | Unlocks the min(), max(), abs() and random() functions. | Pumpkin 1000 |
| Variables | Assign values to variables. | Carrot 35 |
| Watering | Unlock: Water the plants to make them grow faster. / Upgrade: Receive more water. | Wood 50, 200, 800, 3200, 12800, 51200, 205000, 819000, 3280000 |

注意：
- 最初に WebSearch の要約で見た「Speed の2段目 Wood 10，3段目 Wood 50 + Carrots 30」は古い版の値らしい．Unlocks_Data では 2段目 Wood 20，3段目 Wood 50 + Carrot 50 である．どちらが今の版かは，ゲーム内の `get_cost(Unlocks.Speed, 段階)` で確かめること（不明）．
- lab のガイドには「値段は買うたびに上がるので，農作業のあとに `unlock()` が失敗することがある．失敗したら費用を読み直してやり直す」とある．wiki の表では段階ごとに値段が決まっているので，理由は不明．ただ，失敗したときにやり直す作りにしておけば安全である．

---

## 3. Unlocks.Leaderboard までの経路の実例（lab の leaderboard_run.py）

出典：https://lucascerattors.github.io/the-farmer-was-replaced-lab/guides/progression/ と，同じリポジトリの `farms/leaderboards/leaderboard_run.py`（https://github.com/LucasCerattoRS/the-farmer-was-replaced-lab ．git で取得して読んだ）．
lab は「最速リセットで Leaderboard まで通る，最初から作った経路．13種のアンロックを計32回買う」と説明している．かかった時間は書かれていない（不明）．

購入の順番と費用（費用は 2 節の表から付けた）：

| # | アンロック（段階） | 費用 | # | アンロック（段階） | 費用 |
|---|---|---|---|---|---|
| 1 | Speed 1 | Hay 20 | 17 | Trees 2 | Hay 300 |
| 2 | Plant 1 | Hay 50 | 18 | Carrots 2 | Wood 250 |
| 3 | Carrots 1 | Wood 50 | 19 | Speed 5 | Carrot 1000 |
| 4 | Speed 2 | Wood 20 | 20 | Watering 2 | Wood 200 |
| 5 | Watering 1 | Wood 50 | 21 | Fertilizer 4 | Wood 54000 |
| 6 | Trees 1 | Wood 50 + Carrot 70 | 22 | Grass 2 | Hay 300 |
| 7 | Speed 3 | Wood 50 + Carrot 50 | 23 | Trees 3 | Hay 1200 |
| 8 | Expand 1 | Hay 30 | 24 | Carrots 3 | Wood 1250 |
| 9 | Expand 2 | Wood 20 | 25 | Pumpkins 2 | Carrot 1000 |
| 10 | Speed 4 | Carrot 500 | 26 | Watering 3 | Wood 800 |
| 11 | Fertilizer 1 | Wood 500 | 27 | Cactus 1 | Pumpkin 5000 |
| 12 | Pumpkins 1 | Wood 500 + Carrot 200 | 28 | Cactus 2 | Pumpkin 20000 |
| 13 | Expand 3 | Wood 30 + Carrot 20 | 29 | Dinosaurs 1 | Cactus 2000 |
| 14 | Fertilizer 2 | Wood 1500 | 30 | Dinosaurs 2 | Cactus 12000 |
| 15 | Fertilizer 3 | Wood 9000 | 31 | Mazes 1 | Weird_Substance 1000 |
| 16 | Grass 1 | Hay 100 | 32 | **Leaderboard 1** | **Bone 2000000 + Gold 1000000** |

**費用の合計**（こちらで計算）：Hay 2,000，Wood 68,270，Carrot 2,840，Pumpkin 25,000，Cactus 14,000，Weird_Substance 1,000，**Bone 2,000,000，Gold 1,000,000**．
- ここに書いたのは購入に払う額だけである．植えるときの費用（にんじんは干し草と木，かぼちゃはにんじん，リンゴはサボテン），迷路に使う奇妙な物質，恐竜のリンゴのためのサボテンは入っていない．
- この経路は Megafarm（ドローンを増やす）と Sunflowers（Power）を買わず，1機で進む．lab は「言語のアンロックは1つも買わない」とも書いている．
- 途中で `unlock()` が失敗すると，このスクリプトは同じアンロックを買い直し続ける．実際に通ったのなら，この順番は前提を満たしている（推定）．

lab のスクリプトの作り（参考）：
- `unlock_tech(tech)`：`get_cost` の品目ごとに `farm_item` で集め，`unlock` する．失敗したらやり直す．
- `farm_item(item, num)`：品目ごとの集め方へ振り分ける．干し草は草，木は木（なければ茂み），にんじん，かぼちゃ（肥料で感染させて奇妙な物質も得る），サボテン，骨は恐竜，金は迷路（右手法）．
- `sow_tile(to_harvest, water, entity)`：そのマスを指定の植物にする．必要なら収穫し，耕し，水が 0.5 未満なら水をまき，植える．
- 最後の行に，Speed と Plant が 0 のときだけ走る安全装置がある（普段のセーブで誤って実行しないため）．

---

## 4. 骨と金の見積もり（推定）

費用のほとんどを占める骨 200万と金 100万について，wiki の式から必要な回数を計算する．盤面の一辺を w とする．**Expand の段階ごとの w は不明**なので，いくつかの w で示す．

### 4.1 金（迷路）
- wiki（Mazes）：`n` の物質を使うと n×n の迷路ができる．Mazes の段階が1つ上がるごとに宝も必要な物質も2倍になる．宝の金は「迷路の面積」（例：5×5 で 25）．Entities のページは「一辺の長さ」と書いていて，食い違っている．こちらの実機の測定（CLAUDE.md 3.4 節：8×8・段階6で 2,048 ＝ 64×32）は「面積×2^(段階−1)」と合うので，面積の方を採る．
- 同じ迷路を再配置で使い回せる（最大300回）．再配置1回ごとに同じ量の物質を使う．
- Mazes 1段目，w×w の迷路なら，宝1個で金 w²，物質 w．必要な宝の数は 1,000,000 / w²，物質は 1,000,000 / w（推定）．

| w | 宝の数 | 奇妙な物質 |
|---|---|---|
| 8 | 15,625 | 125,000 |
| 12 | 6,945 | 83,340 |
| 16 | 3,907 | 62,512 |
| 22 | 2,067 | 45,474 |
| 32 | 977 | 31,264 |

- 奇妙な物質は，肥料で感染させた植物を収穫すると得られる（収穫量の半分が物質になる）．肥料は10秒ごとに1個届き，Fertilizer を強化するたびに2倍になる（Fertilizer のページ）．物質をどれだけ速く作れるかが，金の段階の速さを決める見込みである（推定）．
- Mazes を強化すると宝も物質も2倍になるので，宝1個あたりの金と物質の比は変わらない．強化で得をするのは，宝の数（＝歩く回数）が半分になる点だけである（推定）．

### 4.2 骨（恐竜）
- wiki（Dinosaurs）：尾の長さ n で骨 n²．帽子を脱ぐと尾が収穫される．リンゴを食べるたびに `move` の tick が 3% 減る（400 から始まり，端数は切り捨て）．
- Dinosaurs の強化で収穫量が何倍になるかは wiki に無い．こちらの実機（リーダーボードで 6段目，(32²−1)²×32 が目標とちょうど一致）から，段階ごとに2倍（2^(段階−1)）と推定する．lab のスクリプトも `2**(num_unlocked(Unlocks.Dinosaurs) - 1)` を掛けている．
- 盤面を埋め切ると尾は w²−1．Dinosaurs 2段目なら，1回の骨は (w²−1)²×2（推定）．

| w | 1回の骨（2段目，推定） | 必要な回数 | 食べるリンゴの合計 |
|---|---|---|---|
| 8 | 7,938 | 252 | 約15,900 |
| 12 | 40,898 | 49 | 約7,000 |
| 16 | 130,050 | 16 | 約4,100 |
| 22 | 466,578 | 5 | 約2,400 |
| 32 | 2,093,058 | 1 | 1,023 |

- 骨は n² で増えるので，**盤面が広いほど必要なリンゴがずっと少なくなる**（推定）．Expand の後ろの段階は Pumpkin 1000 / 8000 / 64000 / 512000 / 4100000 で，骨や金に比べて安い．だから Expand を先に進めてから骨と金を集める順番が有利かもしれない（推定．w の値と，広い盤面で各段階の作業に何秒かかるかが分からないので，まだ確かめられない）．
- リンゴ1個の値段：Entity Planting Costs の表では `Apple: {Items.Cactus: 64}`．これはすべて強化し切った状態の値らしい（かぼちゃの 512 はリーダーボードでの実測と一致する）．低い段階での値段は不明．

### 4.3 植える費用が段階で変わること（推定）
- Entity Planting Costs（https://thefarmerwasreplaced.wiki.gg/wiki/Entity_Planting_Costs ）：Carrot は Hay 512 + Wood 512，Pumpkin は Carrot 512，Cactus は Pumpkin 64，Sunflower は Carrot 1，Apple は Cactus 64，Hedge と Treasure は Weird_Substance 32．Bush・Grass・Tree は無料．
- Costs のページには `get_cost(Entities.Pumpkin)` が `{Items.Carrot:1}` を返すとあり，表の 512 と食い違う．表は強化し切った状態の値で，段階ごとに2倍になる（Pumpkins は10段階 → 2^9 = 512）と推定する．アンロックの説明「Increases the yield and cost」とも合う．実際の値はゲーム内の `get_cost(Entities.X)` で確かめること．

---

## 5. 作物・仕組みの数値（wiki）

### 5.1 成長時間（秒．一様分布）
出典：https://thefarmerwasreplaced.wiki.gg/wiki/Plant_growth

| 植物 | 最小 | 平均 | 最大 |
|---|---|---|---|
| Grass | 0.5 | 0.5 | 0.5 |
| Bush | 3.2 | 4.0 | 4.8 |
| Carrots | 4.8 | 6.0 | 7.2 |
| Tree | 5.6 | 7.0 | 8.4 |
| Pumpkin | 0.2 | 2.0 | 3.8 |
| Cactus | 1.0 | 1.0 | 1.0 |
| Sunflower | 5.6 | 7.0 | 8.4 |
| Dinosaur | 0.18 | 0.2 | 0.22 |

- 木は東西南北の隣に木があるたびに成長時間が2倍になる（4方向すべてで16倍）（Trees）．
- 水：成長の速さは水 0 で1倍，水 1 で5倍（その間は直線）．地面の水は1秒に平均1%減る．水は10秒ごとに1タンク届き，Watering を強化するたびに2倍．1タンクで水 0.25（Watering）．
- 肥料：残りの成長時間を2秒減らす．10秒ごとに1個届き，強化ごとに2倍．肥料を使った植物は感染し，収穫量の半分が奇妙な物質になる．感染した植物に奇妙な物質を使うと治るが，隣の健康な植物は感染する（Fertilizer）．
- かぼちゃ：育ち切ると20%が枯れる．n×n の合体は n≤5 で n³，n≥6 で n²×6（Pumpkins）．
- サボテン：n 本を同時に収穫すると n² 個（Cactus）．
- ひまわり：花びらは7〜15枚．10本以上あるときに花びらが最多のものを収穫すると Power が8倍．Power があるとドローンは2倍速く動き，30回の動作ごとに Power を1使う（Sunflowers）．
- 混植：草・茂み・木・にんじんが対象．アンロック前の倍率は5で，強化ごとに2倍（Polyculture）．
- 1回の収穫で何個採れるか（干し草・木・にんじんの基本量）は wiki に無い（不明）．木は「5 wood each」とある（Trees）．Grass の強化は 100% → 200% → 400% と書かれている（Grass）．

### 5.2 秒と tick の関係（記録が秒で決まる場合に効く）
出典：https://thefarmerwasreplaced.wiki.gg/wiki/Execution_Details ，https://thefarmerwasreplaced.wiki.gg/wiki/Timing

| Speed の段階 | 速さの倍率（Power なし） | 同（Power あり） | tick／秒（Power なし） | tick／秒（Power あり） |
|---|---|---|---|---|
| 0 | 1 | 2 | 400 | 800 |
| 1 | 1.5 | 3 | 600 | 1200 |
| 2 | 2.25 | 4.5 | 900 | 1800 |
| 3 | 3.375 | 6.75 | 1350 | 2700 |
| 4 | 5.0625 | 10.125 | 2025 | 4050 |
| 5 | 7.59375 | 15.1875 | 3037.5 | 6075 |

- 食い違い：`set_execution_speed` の説明（Tooltips_Code）には「速さ 8 は Speed を3回強化したドローンに当たる」とあり，上の表（3回で 3.375 倍）と合わない．どちらが正しいかは不明．
- **こちらの実測との照合（推定）**：成長時間を Speed 5・Power あり（6,075 tick／秒）で tick に直すと，サボテン 1.0 秒は 6,075 tick になる．実測は 5,877 で，差は −3%．かぼちゃの平均 2.0 秒は 12,150 tick で，実測の平均は 12,052．かぼちゃの範囲 0.2〜3.8 秒は 1,215〜23,085 tick で，実測の範囲は 1,581〜22,721．どれもよく合うので，**成長時間は秒で決まっていて，Speed と Power で tick 換算が変わる**と推定する．最速リセットの序盤（Speed 0・Power なし）では，かぼちゃの平均 2.0 秒は 800 tick にしかならない．
- 秒で決まる操作：`do_a_flip()` と `print()` は1秒（速度の強化は効かない）．`quick_print()` と `get_tick_count()` は0秒（Operation_Costs）．

### 5.3 関数の tick 費用
出典：https://thefarmerwasreplaced.wiki.gg/wiki/Operation_Costs ，https://thefarmerwasreplaced.wiki.gg/wiki/Tooltips_Code

- 成功した操作（`move`, `clear`, `swap`, `harvest`, `plant`, `till`, `use_item` など）は 200．失敗した操作は 1．
- `unlock()` は成功で 200，失敗で 1．`reset()`，`leaderboard_run()`，`simulate()`，`set_world_size()`，`set_execution_speed()` は 200．
- 値を読む関数（`get_pos_x()`, `can_harvest()`, `measure()`, `get_cost()`, `num_unlocked()` など）は 1．
- 二項演算・`if`・ループの開始は 1．変数の読み書き・関数の呼び出し・`return`・`break` は 0．
- 操作の効果は，その関数の最初に起きる．そのあと 200 tick が過ぎる（Execution_Details）．

### 5.4 関数の仕様
- `get_cost(thing)`：作物またはアンロックの費用を dict で返す．アンロックでは第2引数で段階を指定できる（既定は今の段階）．最大段階では None を返すと Costs のページにあるが，Tooltips_Code には `{}` を返すとあり，食い違っている（不明）．
- `num_unlocked(thing)`：強化できるアンロックなら「1 ＋ 強化した回数」，それ以外は解放済みなら 1，未解放なら 0（Tooltips_Code）．Senses のページは「何回アンロック・強化したか」と書いている．どちらの書き方でも「未解放なら0」は同じである．
- `unlock(unlock)`：研究ツリーのボタンを押すのとまったく同じ．成功で True，失敗で False．
- `reset()`：盤面を 1×1 に戻し，資源をすべて消し，ほとんどのアンロックを戻す．コードは消えない．
- `simulate(filename, sim_unlocks, sim_items, sim_globals, seed, speedup)`：かかった時間（秒）を返す．sim_unlocks は列（それぞれ最大段階になる），または {アンロック: 段階} の辞書（負の値は最大段階）．シードを固定すると結果は毎回同じになる．speedup は結果に影響しない（Simulation）．
- **途中の状態から部分ごとに測る方法**：たとえば `simulate("fr", {Unlocks.Expand: 5, Unlocks.Mazes: 1}, {Items.Weird_Substance: 100000}, {}, 0, 1000)` で，金を集める部分だけの秒数を比べられる（推定の使い方．引数の形は wiki のとおり）．

---

## 6. リーダーボードの決まり（wiki：Leaderboard）

- `leaderboard_run(Leaderboards.Fastest_Reset, filename, speedup)`．同じ条件のシミュレーションは `simulate(filename, {}, {}, {}, -1, speedup)`．
- 成功条件：`num_unlocked(Unlocks.Leaderboard) > 0`．
- 目標に届いてもシミュレーションは自動では終わらない．プログラムが自分で終わる必要がある．
- ばらつきを減らすため，合計2時間以上走らせる必要がある（加速してよい）．早く終わった場合は，2時間に達するまで繰り返し，全回の平均が記録になる．
- 注意：lab の Leaderboards のページにある目標（例：Pumpkins 2,000,000，Hay 2,000,000）は，wiki（Pumpkins 200,000,000，Hay 2,000,000,000）と食い違う．かぼちゃは実機で 200,000,000 と確認済み（CLAUDE.md 5b 節）なので，lab の数値表は誤りを含む．

---

## 7. まだ不明な点（ゲーム内で調べること）

1. **Expand の各段階での盤面の大きさ**．Expand_2 のページには「タイルが1列でなくなった」とあるので，1段目では1列（推定）．
2. **アンロックの前提**（技術ツリーの親）．未解放のアンロックに `get_cost` を使うと何が返るか．
3. 低い段階での植える費用（`get_cost(Entities.X)`），1回の収穫で採れる量．
4. Megafarm の段階ごとの `max_drones()`．Megafarm の費用は Gold 2000〜512000 なので，金の段階の途中で買う価値があるか．
5. Dinosaurs と Mazes の強化による収穫の倍率（2倍ずつという推定を確かめる）．
6. 記録が秒なのか tick なのか．
7. Speed の倍率（1.5倍ずつか2倍ずつか．5.2 節の食い違い）．

probe の案（ゲーム内で `simulate` から走らせると，最初の状態を確かめられる）：
```
for u in Unlocks:
    quick_print(u, num_unlocked(u), get_cost(u))
quick_print(get_world_size(), max_drones())
```
（`Unlocks` は for で回せると Tooltips_Code に書かれている．段階ごとの費用は `get_cost(u, 段階)` で取れる．）

---

## 8. 出典（読んだページ）

wiki（https://thefarmerwasreplaced.wiki.gg/wiki/ の下．`?action=raw` で取得）：Unlocks，Unlocks_Data，Costs，Auto_Unlocks，Leaderboard，Reset，Items，Entities，Entity_Planting_Costs，Plant_growth，Grass，Trees，Tree，Carrots，Pumpkins，Cactus，Sunflowers，Dinosaurs，Mazes，Megafarm，Expand，Expand_2，Polyculture，Watering，Fertilizer，Plant，Senses，Hats，Timing，Simulation，Execution_Details，Operation_Costs，Tooltips_Code，Item_Costs（「今は使われていない」と書かれたページ）．

lab（https://lucascerattors.github.io/the-farmer-was-replaced-lab/ ）：guides/progression，guides/leaderboard-strategies，mechanics/leaderboards，mechanics/measured-numbers．リポジトリ https://github.com/LucasCerattoRS/the-farmer-was-replaced-lab の `farms/leaderboards/leaderboard_run.py`．

wiki に無かったページ：Bush，Speed，Power などは個別のページが無い（空の応答）．
