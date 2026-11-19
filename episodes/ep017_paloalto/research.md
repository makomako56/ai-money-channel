# ep017 リサーチ：パロアルトネットワークス（Palo Alto Networks, Inc.、Nasdaq: PANW）

取得日：2026-11-19（Claude）。会社の数字は一次情報（パロアルトの決算発表 8-K、2026-11-18／2026-09-01。パロアルト公式発表）のみ。AI の攻撃能力は OpenAI の公式発表。
きっかけのニュース：2026-11-18、パロアルトが2027年度第1四半期（2026年8〜10月）の決算を発表。売上39%増、通期予想を大幅に上方修正。
オーナー指示（#15、2026-11-19 22:08 JST）：「1パロワルドで作って」。公開予定 2026-11-23（月）18:00 JST。

## 会計期間
- パロアルトの会計年度は **7月末で終わる**。2027年度第1四半期（FY2027 Q1）＝**2026年8〜10月**（2026年10月31日まで）
- 1年前の同じ期間（FY2026 Q1）＝2025年8〜10月
- 金額はドルのまま。円換算はしない

## 出典一覧
| 記号 | 資料 | URL | 取得日 |
|---|---|---|---|
| A | Palo Alto Networks「Reports Fiscal First Quarter 2027 Financial Results」（8-K Ex.99.1、2026-11-18） | https://www.sec.gov/Archives/edgar/data/0001327567/000132756726000030/ex991q127earningsrelease.htm | 2026-11-19 |
| A' | 同（パロアルトIR） | https://investors.paloaltonetworks.com/news-releases/news-release-details/palo-alto-networks-reports-fiscal-first-quarter-2027-financial | 2026-11-19（見出しのみ） |
| B | Palo Alto Networks「Reports Fiscal Fourth Quarter and Fiscal Year 2026 Financial Results」（8-K Ex.99.1、2026-09-01）：当初の2027年度予想 | https://www.sec.gov/Archives/edgar/data/0001327567/000132756726000019/ex991q426earningsrelease.htm | 2026-11-19 |
| C | Palo Alto Networks「Completes Acquisition of CyberArk to Secure the AI Era」（2026-02-11） | https://paloaltonetworks.com/company/press/2026/palo-alto-networks-completes-acquisition-of-cyberark-to-secure-the-ai-era | 2026-11-19 |
| D | OpenAI「Safety overview: GPT-6 Astra」（2026-09-03） | https://openai.com/index/safety-overview-gpt-6-astra | 2026-11-19 |
| E | OpenAI「Responding to the next frontier of critical cyber capabilities」（2026-08-07） | https://www.openai.com/index/responding-next-frontier-critical-cyber-capabilities/ | 2026-11-19 |
| F | BigGo Finance（決算説明会の要約、2026-11-18）※報道。台本では使わない（参考） | https://finance.biggo.com/news/US_PANW_2026-11-18 | 2026-11-19 |

## 1. 日常の困りごと（本物そっくりの「宅配の不在通知」）
- ひなたの体験として描く（統計は出さない）。リンクを押さない・公式アプリで確かめる、は一般的な注意
- なぜ起きる：AI で、自然な文章やそっくりの画面を、早く大量に作れるようになった（一般的な説明）
- D：「Astra is our first model to reach the Critical level of cybersecurity capability under our Preparedness Framework.」（GPT-6 Astra、2026-09-03）
  - 台本では「AIを作る会社も、自分のAIのサイバー攻撃の力を、最高レベルと評価」まで。OpenAI の評価の段階は High → Critical（E：前のモデル GPT-5.6-Sol は High）
  - ※題材提案で書いた「GPT-6.2」の評価は一次情報を確認できなかったため使わない

## 2. 解決する技術（AIで守る）
- 守る側も AI を使う：怪しい通信・動きを AI で見つけて止める（一般的な説明）
- パロアルトは自らを「the global AI cybersecurity leader」と説明。守る範囲：Network, Cloud, Security Operations, AI and Identity（A の会社紹介）
- 脅威の調査チーム「Unit 42」（A の会社紹介「powered by Unit 42® threat intelligence」）

## 3. 会社（A・B・C）
- アメリカのサイバーセキュリティの会社。発表の発信地はカリフォルニア州サンタクララ（A・B のデートライン）
- 顧客：「Trusted by 75,000+ customers」→ **7万5000以上**（A）。※B（9月）では 70,000以上
- 2026年2月11日、ID（本人確認）のセキュリティの CyberArk（サイバーアーク）の買収を完了（C）。CyberArk は人・機械・AIエージェントの ID を守る（C）
- 2026-11-18：AI モデルの会社 Applied Compute の買収を予定と発表（A。まだ完了していない）→ 台本では「AIの会社の買収も予定」まで

## 4. 稼ぎ方（A、2026年8〜10月）
- 製品（Product）：5億9500万ドル（≒**6億ドル**）
- サブスクリプションとサポート：28億5000万ドル（≒**28.5億ドル**）
- 合計 34.45億ドル → サブスク・サポートの比率 2850÷3445＝82.7%（A の数字からの計算）→ 台本では「**約8割**」
- 会社が会社に「守る仕組み」を毎年の契約で売る（一般的な説明）

## 5. 数字（A・B）
- 売上：**34.4億ドル**（3,445百万ドル、「$3.44 billion」）、**39%増**（1年前 24.74億ドル）
- 次世代セキュリティの年間契約額（Next-Generation Security ARR）：**97億ドル**（$9.73B）、**66%増**
- 残りの契約額（RPO）：210億ドル、35%増 → 台本では使わない
- 2027年度（2026年8月〜2027年7月）の売上の予想
  - 9月時点（B）：141〜142億ドル（23〜24%増）
  - 11月（A）：**145.2〜145.7億ドル**（26〜27%増）→「上方修正」。CFO「materially raising our full year guidance」
- 社長（ニケシュ・アローラ CEO）：「a record Q1 and delivered one of our highest NGS ARR beats ever」（A）→ 台本では「8〜10月として過去最高」程度（「record Q1」）

## 6. 弱点（A・C）
- ①買収の分を含む：CyberArk の買収完了は2026年2月（C）。1年前（2025年8〜10月）には入っていない → 39%増には買収した会社の売上も含まれる（A は買収を除いた伸びを示していない）
- ②会計上の利益が減った：GAAP の営業利益 **9600万ドル**（1年前 **3億900万ドル**）（A）
  - 買収した会社の無形資産の償却 2億8200万ドル（1年前 3900万ドル）、買収関連費用 5500万ドル（A）
- ③伸びは落ち着く見込み：次の3か月（2026年11月〜2027年1月）の売上予想は36〜37%増、通年は26〜27%増（A）。買収の効果が一巡するため（一般的な説明。台本では「買収した分の上乗せがなくなるため」と言う）

## 台本の数字の照合
| 台本の数字 | 出典 |
|---|---|
| 8〜10月の売上 34.4億ドル、39%増 | A |
| 年間契約額 97億ドル、66%増 | A |
| サブスク・サポート 28.5億ドル、製品 6億ドル、約8割 | A（計算） |
| 顧客 7万5000以上 | A |
| CyberArk 買収完了 2026年2月 | C |
| 通期予想 141〜142億ドル → 145.2〜145.7億ドル | B・A |
| 営業利益 9600万ドル（1年前 3億900万ドル）、償却 2億8200万ドル | A |
| 次の3か月 36〜37%増、通年 26〜27%増 | A |
| OpenAI のモデルが「最高レベル（Critical）」 | D |
