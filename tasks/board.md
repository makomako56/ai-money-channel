# タスクボード

状態：未着手 / 作業中 / 完了 / 差し戻し / 承認待ち

| ID | 回 | 作業 | 担当 | 状態 | 次 | メモ |
|---|---|---|---|---|---|---|
| T001 | 共通 | GitHubリポジトリ作成 | 人 | 完了 | Codex | makomako56/ai-money-channel（Private） |
| T001b | 共通 | GitHubのClaude許可に ai-money-channel を追加 | 人 | 完了 | | Claudeから読み書き可能を確認（2026-10-24） |
| T001c | 共通 | （不要）クラウドのCodexを使う方式に変更 | - | 完了 | | 2026-10-26 |
| T001d | 共通 | Codexのクラウド環境を作成・公開、コードレビューを有効化 | 人 | 未着手 | Claude | 仕組みの資料を参照 |
| T001e | 共通 | テストIssueで @codex 連携を確認 | Claude | 未着手 | Claude | T001dの後 |
| T002 | 共通 | VOICEVOX導入、2人の声を決定 | 人 | 未着手 | Claude | 候補は設定書の「声」 |
| T003 | 共通 | YouTube APIの鍵を作りGitHub Secretsに登録 | 人 | 完了 | | 2026-10-27登録。アプリは「テスト中」のため鍵は約7日で失効→11/2に更新案内。恒久対策は本番公開（自分のドメインのページが必要） |
| T004 | 共通 | 声・Gemini画像・BGMの利用規約確認 → config/licenses.md | Claude | 作業中 | Claude | 全体とGeminiは確認済み。キャラ別は声の決定（T002）後 |
| T005 | 共通 | （作業依頼01〜05に置き換え） | - | 完了 | | |
| T006 | 共通 | ミライ先生の残り差分を生成（口少し開き・目閉じ・驚き・困り顔・ドヤ顔） | Codex | 未着手 | Claude | make_character.py で |
| T007 | 共通 | ひなたの立ち絵 | 人 | 作業中 | Claude | 口開き1枚を透過済み（assets/characters/hinata/transparent/hinata_02_normal_open.png）。口閉じの基本画像を依頼中。characters.yaml への登録は01bのマージ後にClaudeが行う |
| T008 | ep000 | 30秒サンプル台本 | Claude | 完了 | Codex | episodes/ep000_sample/script.txt |
| T009 | ep000 | サンプル30秒動画を生成 | Codex | 未着手 | 人(CP0) | |
| T010 | ep000 | CP0：キャラ・声・画面構成を承認 | 人 | 未着手 | Claude | ここを越えたら毎日制作へ |
| T011 | ep001 | テーマ3案 | Claude | 完了 | 人(CP1) | tasks/ep001_テーマ案.md |
| T012 | ep001 | CP1：テーマを1つ選ぶ | 人 | 完了 | | ディスコに決定（2026-10-26） |
| T013 | ep001 | リサーチ・台本・スライド11枚・meta・サムネ文言 | Claude | 完了 | 人(CP2) | episodes/ep001_disco/ |
| T014 | ep001 | CP2：スライドレビュー（OK/NG） | 人 | 未着手 | Claude | v2で作り直してから再提出 |
| T020 | 共通 | 作業依頼01：Actions土台と音声生成 | Codex | 完了 | | PR #6 マージ済み（2026-10-26） |
| T020b | 共通 | 作業依頼01b：音声の追補（Issue #7） | Codex | 完了 | | PR #8 マージ済み（2026-10-27、Claudeレビュー） |
| T029 | 共通 | Codexのクラウド環境を作成（chatgpt.com/codex/cloud/settings/environments） | 人 | 任意 | | Codexは自分で進めるため必須ではない。作れば GitHub の @codex でも依頼できる |
| T021 | 共通 | 作業依頼02：動画の組み立て（v2：HTML画面の段階表示） | Codex | 未着手 | Claude | 01b完了。オーナー経由でCodexの新しいチャットに依頼（Issue #2）。2026-10-26改訂 |
| T027 | ep001 | ep001を書式v2（会話シーン・目次・章・段階表示のHTML画面）で作り直す | Claude | 作業中 | 人(CP2) | docs/動画スタイル仕様.md |
| T028 | 共通 | 表情・ポーズの立ち絵（docs/立ち絵の作成リスト.md） | 人 | ほぼ完了 | Claude | 2人とも表情・口パク・まばたきが完了（表情シートから合成・登録済み）。残りは任意：口の半開き、ポーズ（指さし・ばんざい） |
| T022 | 共通 | 作業依頼03：サムネ生成 | Codex | 未着手 | Claude | 02の後 |
| T023 | 共通 | 作業依頼04：YouTube予約投稿 | Codex | 未着手 | Claude | 03の後 |
| T024 | 共通 | 作業依頼05：一括実行 | Codex | 未着手 | Claude | 04の後 |
| T025 | ep000 | サンプル用スライド3枚 | Claude | 完了 | Codex | episodes/ep000_sample/slides/ |
| T026 | 共通 | 声の選定 | 人 | 完了 | | AivisSpeech。ミライ＝まお（おちつき）、ひなた＝コハク（仮決定） |
| T030 | 共通 | YouTubeチャンネル開設・中級者向け機能（カスタムサムネ）を有効化 | 人 | 完了 | | 2026-10-27 |
