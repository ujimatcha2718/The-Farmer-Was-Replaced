# 最速リセット（Leaderboards.Fastest_Reset）の wiki 調査（2026-09-29）

## 0. 結論：wiki は読めなかった

この環境のネットワーク制限（egress proxy）で，次のドメインへの接続がすべて拒否された．そのため**アンロックの一覧・段階ごとの費用・前提は取得できていない（不明）**．

| ドメイン | 試したURL | 結果 |
|---|---|---|
| thefarmerwasreplaced.wiki.gg | /wiki/Unlocks | WebFetch：`EGRESS_BLOCKED`．curl：`CONNECT tunnel failed, response 403` |
| thefarmerwasreplaced-wiki-gg.translate.goog | /wiki/Unlocks_Data（Google 翻訳経由） | curl：403 |
| thefarmerwasreplaced.fandom.com | /wiki/Unlocks | curl：403 |
| lucascerattors.github.io | /the-farmer-was-replaced-lab/guides/progression/ | WebFetch：`EGRESS_BLOCKED` |
| web.archive.org，archive.org | アーカイブ | curl：403 |
| steamcommunity.com | /app/2060160 | curl：403 |
| gamesron.com | /the-farmer-was-replaced-all-unlock-costs-guide/ | curl：403 |
| medium.com，www.youtube.com | 攻略記事・世界記録動画 | curl：403 |
| api.github.com | Flekay/The-Farmer-Was-Replaced，lucascerattors/the-farmer-was-replaced-lab | セッションの対象リポジトリ外として拒否 |

読むには，環境の設定（セッションのクラウド環境メニュー → Edit → Network access）で上のドメインを許可する必要がある．

## 1. 検索結果の要約から分かったこと（原文ではない）

WebSearch は使えたので，検索エンジンが返した要約だけを記す．**要約は検索側のモデルが書いたもので，原文の写しではない．数値は原文で確かめるまで「未確認」として扱うこと．**

| 項目 | 要約の内容 | 出典として示されたURL | 確からしさ |
|---|---|---|---|
| 成功条件と計測 | `Unlocks.Leaderboard` をできるだけ早くアンロックする．すべてをアンロックする必要はない．ばらつきを減らすため合計2時間以上走らせる必要があり（速度を上げてよい），早く終わると2時間に達するまで繰り返し，全回の平均が記録になる | https://thefarmerwasreplaced.wiki.gg/wiki/Leaderboard | 要約（CLAUDE.md 5b 節のかぼちゃの「2時間以上」とも合う） |
| `reset()` | 農地を 1×1 に戻し，資源をすべて消し，ほとんどのアンロックを戻す．コードは消えない．戻り値 None，200 tick | https://thefarmerwasreplaced.wiki.gg/wiki/Reset | 要約 |
| `unlock()` | `unlock(Unlocks.Speed)` のようにコードからアンロックできる（Auto_Unlock 系の機能）．**自動では進まず unlock() を呼ぶ必要がある（推定）** | https://thefarmerwasreplaced.wiki.gg/wiki/Auto_Unlocks | 要約．unlock() 自体がアンロック（Unlocks.Auto_Unlock）を要するかは不明 |
| `get_cost()` | 作物またはアンロックの費用を dict で返す．アンロックには第2引数で段階を指定でき，既定は現在の段階．最大段階なら None | https://steamcommunity.com/app/2060160/discussions/0/7203035958218714871/ | 要約 |
| `num_unlocked(u)` | そのアンロックを何段階持っているかを返す | https://thefarmerwasreplaced.wiki.gg/wiki/Reset | 要約 |
| Leaderboard の費用 | `{Items.Bones: 2000}`（「コミュニティの議論による」との要約） | 検索要約（特定ページ不明） | **未確認**．前提アンロックも不明 |
| Speed の費用 | 1段目 Hay 20，2段目 Wood 10，3段目 Wood 50 と Carrots 30 | https://thefarmerwasreplaced.wiki.gg/wiki/Unlocks_Data など | **未確認** |
| アンロックの名前（一部） | Auto_Unlock, Cactus, Carrots, Costs, Debug, Debug_2, Dictionaries, Dinosaurs, Expand, Expand_2, Fertilizer, Functions, Grass, Hats, Import, Leaderboard, Lists, Loops, Mazes, Megafarm, Operators, Plant, Polyculture, Pumpkins, Senses, Simulation（途中で切れている．Speed, Sunflowers, Trees, Watering なども別の要約に出るが一覧は不完全） | https://thefarmerwasreplaced.wiki.gg/wiki/Unlocks_Data | 要約．表記（Dinosaurs か Dinosaur か等）は未確認 |
| Carrots | 土を耕してにんじんを植える．強化で収穫量と費用が増える | 同上 | 要約 |
| Expand | 農地を広げ，移動を解放する．強化でさらに広げる | 同上 | 要約 |
| Megafarm | 複数ドローンとその管理関数を解放する．費用は不明 | 同上 | 要約 |
| 恐竜 | リンゴを骨に変える．1回で n²（尾の長さ²）の骨 | https://thefarmerwasreplaced.wiki.gg/wiki/Leaderboard | 要約（CLAUDE.md 4.1 節と合う） |
| 世界記録（参考） | 「FULL RESET 28:03」「1.0 WORLD RECORD 38:48」という題の動画がある．計測の単位・条件は不明 | https://www.youtube.com/watch?v=hdBSvuOim74 ，https://www.youtube.com/watch?v=lIS41aXwhdQ | 題名のみ |

wiki には一覧用のページとして Unlocks，Unlocks_Data（全費用を返す関数 GetUnlocksData() があるらしい），Costs，Auto_Unlocks，Available_Functions，Items，Tooltips_Code がある（検索結果の題名から）．

## 2. 読めなかった項目（すべて不明）

- 全アンロックの一覧，各段階の費用，前提（技術ツリーの親）．
- 各作物（草・茂み・木・にんじん・かぼちゃ・サボテン・ひまわり・恐竜・迷路）の成長時間・収穫量・植える費用．
- Expand の盤面の広がり方，Speed の速度倍率，Megafarm の段階ごとの機数．
- Polyculture，Watering，Fertilizer の効果．関数ごとの tick 費用（CLAUDE.md 1.3 節の実測以外）．

## 3. Unlocks.Leaderboard までの最短経路

**wiki の数値が得られなかったので計算できない（不明）．** 検索要約の「Leaderboard = 骨 2,000」が正しいと仮定すると，恐竜（Dinosaurs）で骨を得る必要があり，1回で尾の長さ² の骨なので，倍率が1なら尾の長さ 45（45² = 2,025）の1回で足りる（推定）．ただし，恐竜のアンロックの前提と費用，骨の倍率，リンゴのためのサボテンの必要量はいずれも不明である．

## 4. 代わりの手段（wiki が使えない場合）

CLAUDE.md 5c 節のとおり，ゲーム内で調べるのが確実である．probe の例：

```
# 全アンロックの費用と前提をゲーム内で出力する（案）
for u in Unlocks:        # Unlocks が反復できるかは不明
    quick_print(u, num_unlocked(u), get_cost(u))
```

`Unlocks` を反復できない場合は，名前を列挙して `get_cost(Unlocks.X, 段階)` を段階ごとに呼ぶ．
