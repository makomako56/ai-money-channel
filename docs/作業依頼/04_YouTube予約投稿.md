# 作業依頼 04：YouTube への予約投稿

依頼者：Claude ／ 前提：03 がマージ済み

## 目的
承認済みの回を、YouTubeに**非公開＋予約公開**でアップロードする。

## やること
1. `pipeline/upload.py`
   - YouTube Data API v3（`videos.insert`、`thumbnails.set`）
   - 認証：GitHub Secrets の `YT_CLIENT_ID` `YT_CLIENT_SECRET` `YT_REFRESH_TOKEN`
   - `approval.json` がなければ**エラーで止める**
     ```json
     {"approved_by": "owner", "approved_at": "2026-10-27T09:12:00+09:00", "publish_at": "2026-10-27T18:00:00+09:00"}
     ```
   - `privacyStatus` は必ず `private`、`publishAt` は `approval.json` の値（UTCに変換）。過去の時刻ならエラー
   - タイトル・概要欄・タグ・カテゴリは `meta.json`。`selfDeclaredMadeForKids=false`。合成コンテンツの申告項目がAPIにあれば `true`
   - 完了後、動画IDとURLを `upload_result.json` に出し、artifact に保存
   - `--dry-run`：APIを呼ばずに送信内容を表示する
   - アップロード前に、認証したチャンネルのIDが `config/channel.yaml` の `channel_id` と一致することを確認し、違えば止める（別チャンネルへの誤投稿防止）
2. `stage=upload` を `factory.yml` に追加。Secrets がないときはわかりやすいエラー。リフレッシュトークンが失効している（`invalid_grant`）ときは「YouTubeの鍵の更新が必要（docs/YouTube_API準備.md の手順5）」と表示して止める
   - `stage=upload_check`：アップロードせず、認証できるか・チャンネルIDが一致するかだけを確認する（Claudeが鍵の確認に使う）
3. （不要）refresh token は OAuth 2.0 Playground で取得する方式にした
4. `docs/YouTube_API準備.md`：Claudeが作成済み（OAuth 2.0 Playground 方式）。実装に合わせて必要なら追記する。旧要件：オーナー向けの手順書（Google Cloud のプロジェクト作成、YouTube Data API の有効化、OAuth 同意画面、デスクトップアプリ用の認証情報、ツールの実行、GitHub Secrets への登録）。スクリーンショットなしでも迷わないよう、画面上のボタン名を書く

`meta.json` の形式：
```json
{"title": "…", "short_title": "…", "description": "…", "tags": ["AI", "決算"], "category_id": "27"}
```

## 完了条件
- `--dry-run` が `ep000_sample` で成功する（テスト用の meta.json・approval.json は自分で作ってよい）
- `approval.json` なしで止まるテストがある
- 実際のアップロード確認は、オーナーが Secrets を登録したあとに Claude が行う

## 追記（2026-10-27 夜：Claude と分担して並行作業）
今夜は **Codex が 04（この依頼）**、**Claude が 05 の「投稿以外」の部分**（`stage=all` で音声→動画→サムネを一括、入力チェック、Summary）を同時に進める。04 の前提（03 マージ済み）は満たしている。

### 読むファイル（これ以外は開かない）
- このファイル、`AGENTS.md` の「利用上限を節約するための約束」
- `config/channel.yaml`、`episodes/ep001_disco/meta.json`（実物の形式）、`docs/YouTube_API準備.md`
- `.github/workflows/factory.yml`（`stage=video` と `stage=thumbnail` の作り）

### 作り方の指定
- `pipeline/upload.py`（新規）と `pipeline/tests/test_upload.py`（新規）。Google のライブラリを使うなら `requirements.txt` に追加
- `factory.yml` には、**既存の `generate` ジョブとは別の新しいジョブ `upload`** を足す（Claude が `generate` ジョブを変更中のため、衝突を減らす）
  - `stage=upload`：入力 `source_run_id`（動画とサムネを作った実行の ID）を受け取り、`actions/download-artifact@v4` の `run-id` と `github-token` でその実行の `<ep>-video` と `<ep>-thumbnail` を取ってからアップロード
  - `stage=upload_check`：認証とチャンネルIDの一致だけを確認（アップロードしない）
  - 音声エンジン（services）は upload ジョブでは起動しない
- 二重投稿の防止：`episodes/<ep>/upload_result.json` は使わず、**YouTube 側で同じタイトルの動画が自分のチャンネルにあれば止める**（`--force` なし）。05 でも使うので、関数 `already_uploaded(youtube, title)` として切り出す
- テストは API を呼ばない（モックで）。`approval.json` なし・過去の `publish_at`・チャンネルID不一致・二重投稿で止まること、`--dry-run` の送信内容（`privacyStatus=private`、`publishAt` が UTC）を確かめる

### やってはいけないこと
- **実際のアップロードを実行しない**（`stage=upload` を Actions で動かさない）。`approval.json` を作らない・コミットしない（テスト用は一時フォルダに作る）
- Secrets を表示しない・ログに出さない

### 完了条件（上の完了条件に追加）
- 下書きPRでこまめに push。説明に「やったこと・確認方法・確認結果」と `Closes #4`
- CI と `stage=upload_check` の実行は Claude が行う（Codex は push したら終えてよい）
