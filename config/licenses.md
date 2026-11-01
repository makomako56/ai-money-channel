# 利用規約メモ

確認日：2026-10-24（Claude）。規約は変わるので、四半期に1回見直す。法的助言ではない。

## VOICEVOX（ソフト全体）
- 商用・非商用を問わず無料で使える
- **VOICEVOXを使ったことがわかるクレジット表記が必要**
- 作った音声は、**キャラクター（音声ライブラリ）ごとの規約**にも従う必要がある
- 出典：[VOICEVOX ソフトウェア利用規約](https://voicevox.hiroshiba.jp/term/)

## VOICEVOX（キャラクターごと）— 声の決定後に最終確認
表記の基本形は `VOICEVOX:キャラクター名`。動画の概要欄（できれば動画内にも）に、使った全キャラ分を書く。
キャラごとに、政治・宗教・成人向け・誹謗中傷などの禁止事項がある。

| 候補 | 役 | 公式ページ | 確認すること |
|---|---|---|---|
| No.7 | ミライ | [公式](https://voicevox.hiroshiba.jp/product/number_seven/) | 個別規約、クレジット表記、自作キャラの立ち絵での使用可否 |
| 冥鳴ひまり | ミライ | [公式](https://voicevox.hiroshiba.jp/product/meimei_himari/)、[規約](https://meimeihimari.wixsite.com/himari/terms-of-use) | 同上 |
| 九州そら | ミライ | VOICEVOX公式の製品ページ | 同上 |
| 春日部つむぎ | ひなた | VOICEVOX公式の製品ページ | 同上 |
| 四国めたん | ひなた | VOICEVOX公式の製品ページ | 同上 |

**未確認の重要点**：その声を、元のキャラとは別の自作キャラ（ミライ・ひなた）の声として使ってよいか。声が決まったら、その2キャラの規約で最初に確認する。

## AivisSpeech（採用：2026-10-26）
- ソフト本体：個人・法人・商用・非商用を問わず無料、クレジット不要（[AivisSpeech Engine](https://github.com/Aivis-Project/AivisSpeech-Engine)）
- 声のモデルごとにライセンスがある。ACML と CC0 はクレジット義務なし、ACML-NC は非商用向け（同上）
- **ミライ：まお（おちつき）** ／ ライセンス ACML 1.0 ／ 推奨表記「AivisSpeech: まお」／ キャラクター ©Oz Chat/Trippy、CV: ねゆたろ（[モデルページ](https://hub.aivis-project.com/aivm-models/a59cb814-0083-4369-8542-f51a29e72af7)）
- **ひなた：コハク（ノーマル）** ／ ライセンス ACML 1.0 ／ 推奨表記「AivisSpeech: コハク」／ キャラクター ©Oz Chat/Trippy、CV: ねゆたろ（[モデルページ](https://hub.aivis-project.com/aivm-models/22e8ed77-94fe-4ef2-871f-a86f94e9a579)）
- 義務はないが、概要欄に「音声：AivisSpeech（まお・コハク）」と表記する
- 未確認：ACML 1.0 の全文（禁止事項）。モデルの元キャラとは別の自作キャラに声を当てる使い方に制限がないかを、全文で確認する

### AivisHub 追加モデル候補（T036）

| モデル | UUID | ライセンス | AivisHub・補足 |
|---|---|---|---|
| すみれ | `2ff1c526-27d4-4eeb-b069-4207ae5fe259` | ACML 1.0 | [モデルページ](https://hub.aivis-project.com/aivm-models/2ff1c526-27d4-4eeb-b069-4207ae5fe259)。説明欄で声のクレジット表記を要請 |
| わかな | `f83c385c-829b-40c4-8c11-639027e61636` | ACML 1.0 | [モデルページ](https://hub.aivis-project.com/aivm-models/f83c385c-829b-40c4-8c11-639027e61636)。説明欄で声のクレジット表記を要請 |
| みちのくあいり | `1b2830f4-8cf1-4184-a0d9-3a1bace3a844` | ACML 1.0 | [モデルページ](https://hub.aivis-project.com/aivm-models/1b2830f4-8cf1-4184-a0d9-3a1bace3a844)。声：上戸恵里 |
| 天深シノ | `0f6821f4-9f86-4da1-a41a-fbe6fff9ca88` | **ACML-NC 1.0** | [モデルページ](https://hub.aivis-project.com/aivm-models/0f6821f4-9f86-4da1-a41a-fbe6fff9ca88)。非商用向けのため収益化動画には採用不可 |
| ほのか | `59f96896-64d2-4378-830a-4d5feb3d81aa` | ACML 1.0 | [モデルページ](https://hub.aivis-project.com/aivm-models/59f96896-64d2-4378-830a-4d5feb3d81aa)。説明欄で声のクレジット表記を要請 |

ライセンス確認日：2026-11-01。サンプル比較には全候補を含めるが、採用時にはモデルページと ACML 本文を再確認する。

## Gemini（画像生成）
- Googleの利用規約で、生成物の商用利用は明確には禁止されていない（ただし公式に「許可」と言い切れる文言でもない）
- [生成AIの使用禁止に関するポリシー](https://policies.google.com/terms/generative-ai/use-policy?hl=ja) で、違法・有害・誤解を招く内容などの生成は禁止
- 既存作品・実在人物・企業ロゴに似た画像は、著作権・肖像権・商標権の問題になりうる。**公開前に画像検索で類似チェック**
- AIだけで作った画像は著作物として保護されにくい。人の手で加工を加えておく
- 出典：[Geminiの商用利用（TSクラウド）](https://googleworkspace.tscloud.co.jp/gemini/commercial-use)

## BGM・効果音
未選定。候補を決めたら、商用可否・クレジット要否・YouTubeのコンテンツID登録の有無を確認する。

## YouTube・note
- アフィリエイトリンクには「PR」「広告」を明記（景品表示法のステマ規制）
- AIで作った人物の映像は、実在と誤認させない（YouTubeの合成コンテンツの申告が必要な場合がある）
