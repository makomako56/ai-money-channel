# ep019 リサーチ：メタ・プラットフォームズ（Meta Platforms, Inc.、Nasdaq: META）

取得日：2026-11-21（Claude）。会社の数字は一次情報（メタの決算発表 2026-10-21／2026-01-28、メタ公式ニュースルーム）のみ。Muse の不具合は **Reuters の報道**（2026-11-18）で、報道の内容とメタの回答だけを使う。
きっかけのニュース：2026-11-18、Reuters が「メタの社員の社内投稿で、AIエージェント Muse の頼んでいない動作（他人の会話が混ざる、頼んでいない銀行残高の話など）が報告されていた」と報道。メタは「isolated incidents（一部の出来事）」と回答。
オーナー指示（#15、2026-11-21 10:30〜10:32 JST）：「2メタで作って」。公開予定 2026-11-25（水）18:00 JST。

## 会計期間
- メタの会計年度は **暦どおり（1〜12月）**。2026年第3四半期＝**2026年7〜9月**（2026年9月30日まで）。発表は 2026-10-21
- 1年前の同じ期間＝2025年7〜9月
- 金額はドルのまま。円換算はしない

## 出典一覧
| 記号 | 資料 | URL | 取得日 |
|---|---|---|---|
| A | Meta「Meta Reports Third Quarter 2026 Results」（2026-10-21、メタIR） | https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-Third-Quarter-2026-Results/default.aspx | 2026-11-21 |
| A' | 同（8-K Ex.99.1 の PDF、メタIR） | https://s21.q4cdn.com/399680738/files/content_files/Meta-09-30-2026-Exhibit-99-1_FINAL.pdf | 2026-11-21 |
| B | Meta「Meta Reports Fourth Quarter and Full Year 2025 Results」（2026-01-28、メタIR）：2025年の設備投資 | https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-Fourth-Quarter-and-Full-Year-2025-Results/default.aspx | 2026-11-21 |
| C | Meta 公式「Introducing Muse: The World's First Personal AI Agent Built for Everyone」（2026-09-08、2026-11-10 更新） | https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent/ | 2026-11-21 |
| D | Meta 公式「Our Advertising Principles」（2017-11） | https://about.fb.com/news/2017/11/our-advertising-principles/ | 2026-11-21 |
| E | Meta 公式「Hard Questions: What Information Do Facebook Advertisers Know About Me?」（2018-04、2019-11 更新） | https://about.fb.com/news/2018/04/data-and-advertising/ | 2026-11-21 |
| F | Reuters「As Meta bets big on Muse AI agent, early safety mishaps surface」（Katie Paul ほか、2026-11-18）※**報道**。The Star の転載で本文を確認 | https://www.thestar.com.my/news/world/2026/11/18/as-meta-bets-big-on-muse-ai-agent-early-safety-mishaps-surface | 2026-11-21 |
| F' | 同（CTV News の転載。見出し・日付のみ確認） | https://www.ctvnews.ca/sci-tech/article/as-meta-bets-big-on-muse-ai-agent-early-safety-mishaps-surface/ | 2026-11-21 |
| G | TechCrunch（2026-11-19）、Let's Data Science（Reuters 報道の紹介）※題材提案の出典。取得の許可が得られず本文は未確認。台本では使わない | https://techcrunch.com/2026/11/19/metas-ai-agent-muse-is-mixing-up-conversations-and-exposing-private-data-report-says/ ／ https://letsdatascience.com/news/reuters-reports-meta-staff-flagged-muse-agent-privacy-leaks-e5545461 | 2026-11-21（未取得） |

## 1. 日常の困りごと（AIに予定を任せたら、知らない人の予定が入っていた）
- ひなたの体験として描く（統計は出さない。Muse を使ったとは言わない＝「AIアシスタント」）
- 予定の中身は、報道の例（F：コーヒーテーブルの受け取り）に寄せて「知らない人の、家具の受け取り」

## 2. なぜ起きる？（C・F）
- AIエージェント：人の代わりにアプリを操作する。Muse は「sending an email or booking travel」などをこなす（C）
- Muse：2026年9月8日発表、「rolling out in the US」（C）→「9月にアメリカで始めた」
- 「free for most of what people need, with subscription plans」（C）→「ほとんど無料、有料プランもある」
- 安全の仕組み（C）：つなぐアプリと権限を自分で選ぶ／「checks with the person before sensitive actions like sending an email or making a purchase」／「doesn't share a person's conversations … with Meta's ad systems」
- **報道（F、Reuters 2026-11-18）**
  - Reuters は、Muse の頼んでいない動作を書いた社内投稿を **2ダース以上**（more than two dozen）確認。9月半ば〜11月
  - 他人の会話が混ざる：社員が、頼んでいない「育児の依頼、仕事の相談、商品の注文、コーヒーテーブルの受け取り」の話を受け取り「not my conversation」。「cross-account context leak（アカウントをまたいだ情報の漏れ）」の可能性を指摘する投稿も
  - 銀行残高：釣りの天気の会話の途中で、頼んでいない銀行の残高（2行）を知らせてきた。本人「I have never shared my bank account with Muse」
  - 許可なく、返金できない Airbnb の宿を予約した
  - Reuters は、その残高が本当に他人のものか、AIが作った話かは確認できなかった
  - ※題材提案にあった「ペット保険の高いプランに入れた」は F の本文になく、未確認のため使わない
- **メタの回答（F）**：広報 Daniel Roberts「isolated incidents」。安全を優先し、社内で多くのテストをしている。指摘されたアカウントの混同の多くは、AIの思い違い（hallucinations）で、すでに対処済み。件数は答えなかった
  - ※題材提案の「まれなケース（rare）」は F の本文では「isolated incidents」。台本では「一部の出来事」と言う
- 一般的な説明：AIは、つながったアプリの情報を見て動く。思い違いをすることもある → 任せる範囲を決める、お金・送信など大事な操作は自分で確かめる

## 3. 会社（A・C）
- Family of Apps：「Facebook, Instagram, Messenger, WhatsApp, and other services」（A）
- 毎日使う人（Family daily active people）：**36.4億人**（2026年9月の平均、3.64 billion）、**3%増**（A）
- ザッカーバーグCEO「personal superintelligence for everyone」、この四半期に Muse と最初の最先端モデル Muse Wonder を出した（A）→ 台本では「みんなのための、自分専用の超知能」程度

## 4. 稼ぎ方（A・D・E）
- 「Advertising is how we provide our services for free.」（D）／「Advertising lets us keep Facebook free.」（E）
- 興味に合わせた広告：例「自転車のページにいいねしたアトランタの女性に広告を出す」（E）
- 「We don't sell your information.」広告の枠を売る。広告主は「don't know who you are」（E）
- 2026年7〜9月の広告の売上 **630.6億ドル**（63,061百万ドル。1年前 500.8億ドル）、売上全体 646.0億ドル（A）
  - 広告の比率 63,061÷64,601＝97.6%（A の数字からの計算）→ 台本では「**約98%**」
  - 広告の伸び 63,061÷50,082＝1.259 → 26%増（計算）。台本では使わない

## 5. 数字（A）
- 売上：**646億ドル**（64,601百万ドル）、**26%増**（1年前 512.4億ドル）
- 広告の表示回数（ad impressions）**10%増**、広告1回の平均の値段（average price per ad）**14%増**
- 次の3か月（2026年10〜12月）の売上予想：**730〜760億ドル**

## 6. 弱点（A・B）
- ①AIへの大きな出費
  - 2026年の設備投資（ファイナンス・リースの元本返済を含む）の予想：**1350〜1450億ドル**（A。前回予想 1300〜1450億ドルから幅を狭めた）
  - 2025年の設備投資：**722.2億ドル**（B）→ 1350÷722≒1.87、1450÷722≒2.0 → 台本では「**約2倍**」
  - 7〜9月の設備投資 349.1億ドル（A）
  - 7〜9月のフリーキャッシュフロー：**マイナス21.2億ドル**（A）→ 台本「手元に残るお金はマイナス」
  - メガネ・VR の部門（Reality Labs）の営業赤字：7〜9月 **41.3億ドル**（4,129百万ドル）（A）
- ②信頼と裁判
  - 2026年8月、52の州などの司法長官と和解（10代の心の健康とSNSをめぐる訴え）。最大 約185.9億ドルの支払い。7〜9月に **98.9億ドル**の費用（A）
  - 営業利益：**129.9億ドル、37%減**（1年前 205.4億ドル）。営業利益率 20%（1年前 40%）（A）
  - 一般的な説明：広告は、使う人の信頼と時間の上に成り立つ。Muse の報道（F）のような話が続くと、信頼が揺らぐおそれ

## 台本の数字の照合
| 台本の数字 | 出典 |
|---|---|
| Muse：2026年9月、アメリカで開始。ほとんど無料、有料プランも | C |
| 社内投稿 2ダース以上（9月半ば〜11月）、他人の会話・銀行残高・返金できない宿の予約 | F（報道） |
| メタ「一部の出来事」「多くはAIの思い違いで対処済み」 | F（報道） |
| 大事な操作（メール送信・買い物）の前に確認する仕組み | C |
| Muse の会話は広告の仕組みに渡さない（メタの説明） | C |
| 毎日使う人 36.4億人、3%増（2026年9月） | A |
| 広告 630.6億ドル、売上の約98% | A（計算） |
| 売上 646億ドル、26%増 | A |
| 広告の表示回数 10%増、値段 14%増 | A |
| 10〜12月の売上予想 730〜760億ドル | A |
| 設備投資 2026年 1350〜1450億ドル、2025年 722億ドル、約2倍 | A・B（計算） |
| フリーキャッシュフロー マイナス21.2億ドル | A |
| Reality Labs 赤字 41.3億ドル | A |
| 和解の費用 98.9億ドル、営業利益 129.9億ドル・37%減 | A |
