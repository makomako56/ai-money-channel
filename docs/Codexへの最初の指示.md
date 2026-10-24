# Codexへの最初の指示

Codexでこのフォルダ（デスクトップの「ミライ先生AIマネー教室」）を作業場所にして、下の文章をそのまま貼る。
2回目以降は「指示ログとタスクボードを見て、自分の担当を進めて」だけでよい。

---

```
このフォルダは、YouTubeチャンネル「ミライ先生のAIマネー教室」の制作リポジトリです。
AIで稼いでいる企業を、先生（天野ミライ）と生徒（春野ひなた）の会話形式で解説する約10分の動画を、毎日自動で作る仕組みを作っています。

【分担】
- オーナー：チェックポイントで承認するだけ
- Claude：企画、リサーチ、台本、ファクトチェック、概要欄・note記事、完成動画のレビュー
- あなた（Codex）：動画を自動で作るパイプラインのコードを作り、動かし、保守する

【毎回最初に読むファイル】
1. AGENTS.md … あなたの作業ルールと各スクリプトの要件
2. tasks/指示ログ.md … オーナーの最新の指示（Claudeが記録している）
3. tasks/board.md … タスクの引き継ぎ表。担当がCodexのタスクを進める
4. 00_手順書.md と config/characters.yaml

【最初にやってほしいこと】
1. GitHub（https://github.com/makomako56/ai-money-channel.git、Private）にはClaudeが同じ内容を初回保存済み。このフォルダで git init → git remote add origin <URL> → git fetch origin → git reset origin/main を実行してつなぐ（ファイルは上書きしない）。git status で差分がないことを確認する。.env はコミットしない
2. tasks/board.md の T005：AGENTS.md の要件どおりに pipeline/ を構築する（make_voice.py と make_video.py を優先、他は骨組みでよい）
3. VOICEVOXはこのMacで動くので、ローカルの http://127.0.0.1:50021 を使う
4. episodes/ep000_sample/ で30秒のサンプル動画が作れる状態にする（台本はClaudeが用意する）
5. 終わったら tasks/board.md の状態を更新し、コミットしてpushする

【守ること】
- 台本や概要欄の中身は変更しない（直しが必要なら tasks/board.md でClaudeに差し戻す）
- APIキーをコミットしない（.env を使う）
- YouTubeへの公開は、tasks/board.md にオーナーの承認（CP3）がある回だけ。必ず非公開か予約投稿にする
```
