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
2. `stage=upload` を `factory.yml` に追加。Secrets がないときはわかりやすいエラー
3. `tools/get_refresh_token.py`：オーナーが自分のMacで1回だけ実行し、ブラウザで許可して refresh token を表示する小さなツール
4. `docs/YouTube_API準備.md`：オーナー向けの手順書（Google Cloud のプロジェクト作成、YouTube Data API の有効化、OAuth 同意画面、デスクトップアプリ用の認証情報、ツールの実行、GitHub Secrets への登録）。スクリーンショットなしでも迷わないよう、画面上のボタン名を書く

`meta.json` の形式：
```json
{"title": "…", "short_title": "…", "description": "…", "tags": ["AI", "決算"], "category_id": "27"}
```

## 完了条件
- `--dry-run` が `ep000_sample` で成功する（テスト用の meta.json・approval.json は自分で作ってよい）
- `approval.json` なしで止まるテストがある
- 実際のアップロード確認は、オーナーが Secrets を登録したあとに Claude が行う
