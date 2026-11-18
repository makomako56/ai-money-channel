# ep016 リサーチ：インテル（Intel Corporation、Nasdaq: INTC）

取得日：2026-11-18（Claude）。会社の数字は一次情報（インテルの決算発表 8-K、2026-10-29。インテル公式発表）のみ。CEO の発言と SC26 の展示は報道（インタビュー）として扱う。
きっかけのニュース：2026-11-12〜13、インテルのリップブー・タン CEO がインタビューで「AI は学習から推論（使う段階）へ移り、AI が GPU とほぼ同じ数の CPU を買っている」と話した（24/7 Wall St.）。SC26（11/16〜）で、最大256コアの次世代サーバー用 CPU「Diamond Rapids（ダイヤモンド・ラピッズ）」の詳細を紹介（報道）。
オーナー指示（#15、2026-11-18 09:47 JST）：「インテルで動画作成して」。公開予定 2026-11-22（日）18:00 JST。

## 会計期間
- インテルの会計年度はほぼ暦どおり（12月末ごろに終わる）。2026年第3四半期（Q3）＝**2026年7〜9月**（決算上は2026年9月26日まで）
- 金額はドルのまま。円換算はしない

## 出典一覧
| 記号 | 資料 | URL | 取得日 |
|---|---|---|---|
| A | Intel「Intel Reports Third-Quarter 2026 Financial Results」（8-K、2026-10-29） | https://www.sec.gov/Archives/edgar/data/0000050863/000005086326000188/q326earningsrelease.htm | 2026-11-18 |
| A' | 同（インテルIR） | https://www.intc.com/news-events/press-releases/detail/1786/intel-reports-third-quarter-2026-financial-results | 2026-11-18（見出しのみ） |
| B | Intel 公式「Intel Outlines Architectures for Agentic AI at Hot Chips 2026」（2026-08-24） | https://www.intel.com/content/www/us/en/newsroom/news/client-computing/intel-outlines-architectures-for-agentic-ai-at-hot-chips-2026.html | 2026-11-18 |
| C | StorageReview「Intel Diamond Rapids Xeon … SC26」（2026-11-16） | https://www.storagereview.com/news/intel-diamond-rapids-1-6tb-s-memory-bandwidth-1-28gb-cache-gpu-d270-sc26 | 2026-11-18 |
| C' | KitGuru「Intel details Diamond Rapids Xeon and GPU D-series accelerators」（SC26） | https://www.kitguru.net/channel/generaltech/matthew-wilson/intel-details-diamond-rapids-xeon-and-gpu-d-series-accelerators/ | 2026-11-18 |
| D | 24/7 Wall St.「Intel's CEO Says AI Is Now Buying Almost as Many CPUs as GPUs」（2026-11-13）※本文は取得できず。Yahoo Finance 転載版（2026-11-12）で確認 | https://247wallst.com/investing/2026/11/13/intels-ceo-says-ai-is-now-buying-almost-as-many-cpus-as-gpus/ ／ https://finance.yahoo.com/technology/ai/articles/intel-ceo-says-ai-now-140945370.html | 2026-11-18 |
| E | TIKR「Intel's CEO Says AI Is Buying "Almost as Many CPUs as GPUs."」（2026-11-16）：Yahoo Finance の Brian Sozzi によるインタビュー（Invest カンファレンス） | https://www.tikr.com/blog/intels-ceo-says-ai-is-buying-almost-as-many-cpus-as-gpus-amd-and-arm-gain-too | 2026-11-18 |
| F | The Stack「"The CPU is reinserting itself"…: Tan」（2026-04-27、2026年1〜3月期の決算説明会の発言） | https://www.thestack.technology/the-cpu-is-reinserting-itself-will-reach-parity-with-gpus-for-ai-workloads-tan/ | 2026-11-18 |
| G | Intel「CES 2026: Intel Core Ultra Series 3 Debuts as First Built on Intel 18A」（2026-01-05、Business Wire） | https://www.businesswire.com/news/home/20260105738564/en/CES-2026-Intel-Core-Ultra-Series-3-Debuts-as-First-Built-on-Intel-18A | 2026-11-18 |
| H | eWeek「Intel's 256-Core Diamond Rapids Xeon Targets AMD's Venice in 2027」（2026-08-27） | https://www.eweek.com/news/intel-diamond-rapids-256-core-xeon-amd-venice/ | 2026-11-18 |

## 1. 日常の困りごと（AIを使うとパソコンが重い・ファンがうるさい）
- ひなたの体験として描く（統計は出さない）
- なぜ起きる：AI は計算の量がとても多い → パソコンの頭脳（CPU・GPU）がフル回転 → 熱が出る → 冷やすためにファンが回る（一般的な説明）
- パソコン側の工夫：インテルの「Core Ultra シリーズ3」は、CPU・GPU に加えて AI 用の部品（NPU）を持つ（G「up to 16 CPU cores, 12 Xe-cores and 50 NPU TOPS」）。「米国で設計・製造した、Intel 18A で作る初の AI PC 向け」（G）
  - 台本では「AI 専用の部品を入れたパソコン用の CPU もある」まで。ファンが静かになる等の効果は言わない

## 2. 解決する技術（CPU と GPU、学習と推論）
- CPU＝何でもこなす「司令塔」。GPU＝同じ計算を大勢で一気にやるのが得意（一般的な説明）
- 学習＝AI に勉強させる段階。推論＝勉強した AI を使って答えを出す段階（一般的な説明）
- タン CEO：AI は「学習」から「使う（推論）」段階へ移っている（D）
- タン CEO：AI の仕組みの中の比率は、以前は GPU 約8個に CPU 1個 → 今は「kind of parity now（ほぼ同じ）」「in some cases actually more CPU than GPU（CPU のほうが多いことも）」（E、Yahoo Finance のインタビュー）。D は「タン氏の見立てで、インテルは販売データを出していない」と注記
  - 2026年4月の決算説明会では「1対8 → 1対4、いずれ同じくらいに」（F）→ 台本では使わない
- 決算説明会（10/29）でタン CEO：「GPU は考える仕事が得意。推論の仕事は CPU のほうがずっと効率的」（D の引用 "While GPUs are great at thinking tasks, deterministic CPUs are far more efficient at inference tasks."）
- AI エージェントは道具を呼び出し、データを動かし、手順を進める → CPU が得意（D の説明）
- ※比率は「個数」の話で、金額ではない（E）。台本でも「数」と言う

## 3. 会社（A・B・C・D）
- アメリカの半導体の会社。本社はカリフォルニア州サンタクララ（D：インタビューはサンタクララの本社で収録）
- パソコンやサーバーの CPU（Core、Xeon）で知られる（A）
- 事業は大きく2つ：**インテルの製品**（パソコン向け・データセンターと AI 向け）と、**インテル・ファウンドリー（工場の事業）**（A のセグメント）
- SC26（スーパーコンピューターの展示会、2026年11月16日〜）で、次世代サーバー用 CPU「Diamond Rapids」を紹介（C・C'）
  - 最大 **256コア**（C・C'、公式は B「Up to 256 new cores」）
  - 自社の最新の作り方「Intel 18A-P」で作る。「Built exclusively on Intel technology」（B）
  - 発売日は公式発表なし（B・C）。報道では2027年（H）
  - インテルは「エージェント型 AI のための CPU」と位置づけ（B「designed for enterprise-scale Agentic AI」）

## 4. 稼ぎ方（A、2026年7〜9月）
- CPU などのチップを作って売る。買うのはパソコンのメーカー、データセンターを持つ会社など（一般的な説明）
- 部門別の売上：
  - パソコン向けなど（Client Computing and Physical AI Group、CCPG）：**81億ドル**（5%減）
  - データセンターと AI（DCAI）：**73億ドル**（73.18億、**78%増**）
  - 製品の合計（Intel Products）：154億ドル（22%増）
  - 工場の事業（Intel Foundry）：67億ドル（58%増）。社内の取引の消去が −62.91億ドル → 工場の売上の大部分はインテル自身の製品の分（A の数字からの計算：62.91÷67≒94%）
  - その他：7億ドル（30%減）
- 台本では「パソコン向け81億ドル」「データセンターとAI 73億ドル」「工場は主にインテル自身の分」まで

## 5. 数字（A、2026年第3四半期＝2026年7〜9月）
- 売上：**165億ドル**（165.13億）、1年前より **21%増**
- データセンターと AI：73億ドル、**78%増**。CFO「データセンターの売上の伸びは15年で最も強い」（A）
- 本業のもうけ（GAAP 営業利益）：25.22億ドル（1年前 6.83億ドル）→ 台本では使わない（純利益が1年前の事業売却益で下がって見えるなど、説明が難しいため）
- 次の3か月（2026年10〜12月）の売上の見通し：**150〜160億ドル**（A）
- CEO：「今いちばん大事なのは、Xeon（サーバー用 CPU）へのとても強い需要に応えるため、供給を増やすこと」（A "unlock additional supply to meet extraordinary demand for our Xeon family"）

## 6. 弱点（A・H）
- 工場の事業（Intel Foundry）は赤字：2026年7〜9月の営業損失 **18.5億ドル**（1年前 23.2億ドル → 少し縮小）（A）
- パソコン向けは **5%減**。CFO「パソコンの減速は少なくとも来年前半まで続く」（A "we see the PC slowdown continuing at least through the first half of next year"）
- 次の3か月の売上見通し 150〜160億ドルは、7〜9月の165億ドルより少ない（A）
- ライバル：AMD の次のサーバー用 CPU「Venice」も256コアの予定（H、報道）。Diamond Rapids は2027年に市場へ（H、報道）

## 台本で使わなかった数字
- 純利益（33億ドル、18%減）、1株利益：1年前に事業売却の利益があり、比べると誤解を生むため
- 株価（2026-11-12 終値61.20ドル等、D）：売買推奨と受け取られないよう使わない
- サーバー用 CPU 市場が最大5倍、サーバー CPU 台数が2026・2027年に30%超増（D の決算説明会の発言）：今回は使わない
- 230億ドルの株式の発行、Classiq の買収予定（A）：話の流れに要らないため
