# タスクボード

状態：未着手 / 作業中 / 完了 / 差し戻し / 承認待ち

| ID | 回 | 作業 | 担当 | 状態 | 次 | メモ |
|---|---|---|---|---|---|---|
| T001 | 共通 | GitHubリポジトリ作成 | 人 | 完了 | Codex | makomako56/ai-money-channel（Private） |
| T001b | 共通 | GitHubのClaude許可に ai-money-channel を追加 | 人 | 完了 | | Claudeから読み書き可能を確認（2026-10-24） |
| T001c | 共通 | 初回push（Claude済み）→ デスクトップのフォルダをリポジトリにつなぐ | Codex | 未着手 | | docs/Codexへの最初の指示.md の手順1 |
| T002 | 共通 | VOICEVOX導入、2人の声を決定 | 人 | 未着手 | Claude | 候補は設定書の「声」 |
| T003 | 共通 | GeminiのAPIキー・YouTube API認証を .env に設定 | 人 | 未着手 | Codex | .env.example を参照 |
| T004 | 共通 | 声・Gemini画像・BGMの利用規約確認 → config/licenses.md | Claude | 未着手 | 人 | T002の後 |
| T005 | 共通 | pipeline/ 構築（make_character〜run_episode） | Codex | 未着手 | Codex | AGENTS.md の要件どおり |
| T006 | 共通 | ミライ先生の残り差分を生成（口少し開き・目閉じ・驚き・困り顔・ドヤ顔） | Codex | 未着手 | Claude | make_character.py で |
| T007 | 共通 | ひなたの基本画像と差分を生成（リボンはオレンジ） | Codex | 未着手 | Claude | 基本画像は人が1度だけ確認 |
| T008 | ep000 | 30秒サンプル台本 | Claude | 完了 | Codex | episodes/ep000_sample/script.txt |
| T009 | ep000 | サンプル30秒動画を生成 | Codex | 未着手 | 人(CP0) | |
| T010 | ep000 | CP0：キャラ・声・画面構成を承認 | 人 | 未着手 | Claude | ここを越えたら毎日制作へ |
