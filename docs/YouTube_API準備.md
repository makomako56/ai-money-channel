# YouTube API の準備（オーナー向け・初回だけ）

作成：2026-10-26（Claude）。所要時間：30〜40分。パソコンで行う（スマホは不可）。
目的：動画工場（GitHub Actions）が、あなたのチャンネルに動画を**予約投稿**できるようにする鍵を作る。

最後にできるもの（3つ）：`クライアントID`、`クライアントシークレット`、`リフレッシュトークン`
これらはパスワードと同じ扱い。チャットやファイルに書かず、手順5でGitHubのSecretsにだけ入れる。

---

## 手順1：Google Cloud のプロジェクトを作る
1. https://console.cloud.google.com/ を開き、**YouTubeチャンネルを持っているGoogleアカウント**でログイン
2. 画面上部のプロジェクト選択 →「新しいプロジェクト」
3. プロジェクト名：`ai-money-channel` →「作成」
4. 作成したプロジェクトが選ばれていることを確認

## 手順2：YouTube Data API を有効にする
1. 左メニュー「APIとサービス」→「ライブラリ」
2. 「YouTube Data API v3」を検索して開き、「有効にする」

## 手順3：OAuth 同意画面を設定する
1. 「APIとサービス」→「OAuth 同意画面」（「Google Auth Platform」と表示される場合もある）
2. ユーザーの種類：**外部** →「作成」
3. アプリ名：`ai-money-channel`、ユーザーサポートメール・デベロッパーの連絡先：自分のメール → 保存して次へ
4. スコープ：「スコープを追加」で次の2つを選ぶ → 保存
   - `https://www.googleapis.com/auth/youtube.upload`
   - `https://www.googleapis.com/auth/youtube`（サムネ設定に必要）
5. テストユーザー：自分のメールを追加
6. **公開ステータスを「本番環境」にする**（「アプリを公開」）
   - 「テスト」のままだと、リフレッシュトークンが**7日で失効**し、毎週やり直しになる
   - 本番にしても、Googleの審査は自分だけで使う分には不要。ログイン時に「このアプリは確認されていません」と出るが、自分のアプリなので「詳細」→「（安全ではないページ）に移動」で進んでよい

## 手順4：認証情報（OAuth クライアント）を作る
1. 「APIとサービス」→「認証情報」→「認証情報を作成」→「OAuth クライアント ID」
2. アプリケーションの種類：**ウェブ アプリケーション**、名前：`factory`
3. 「承認済みのリダイレクト URI」に次を追加：`https://developers.google.com/oauthplayground`
4. 「作成」→ 表示された **クライアントID** と **クライアントシークレット** を控える（この画面はまた開ける）

## 手順5：リフレッシュトークンを取る（OAuth 2.0 Playground）
1. https://developers.google.com/oauthplayground を開く
2. 右上の歯車（OAuth 2.0 configuration）→「Use your own OAuth credentials」にチェック → 手順4のクライアントIDとシークレットを入れる
3. 左の「Step 1」で、入力欄に次の2つを1行ずつ入れる → 「Authorize APIs」
   - `https://www.googleapis.com/auth/youtube.upload`
   - `https://www.googleapis.com/auth/youtube`
4. **チャンネルのアカウント**を選び、許可する（ブランドアカウントでチャンネルを作っている場合は、そのチャンネルを選ぶ）
5. 「Step 2」→「Exchange authorization code for tokens」→ 表示された **Refresh token** を控える

## 手順6：GitHub の Secrets に登録する
1. https://github.com/makomako56/ai-money-channel/settings/secrets/actions を開く
2. 「New repository secret」で、次の3つを登録
   | Name | Secret |
   |---|---|
   | `YT_CLIENT_ID` | 手順4のクライアントID |
   | `YT_CLIENT_SECRET` | 手順4のクライアントシークレット |
   | `YT_REFRESH_TOKEN` | 手順5のリフレッシュトークン |
3. 控えたメモは削除する

## 終わったら
Claudeに「YouTubeの鍵を登録した」と伝える。値は伝えない。
Claudeが、動画工場の予約投稿ができたあとに、テスト動画を**非公開**でアップロードして確認する。

## うまくいかないとき
- 手順5で「redirect_uri_mismatch」：手順4のリダイレクトURIが一字一句同じか確認
- 「access_denied」：手順3のテストユーザーに自分が入っているか、公開ステータスを確認
- チャンネルが選べない：YouTube Studio でチャンネルを作成済みか確認
- upload_check で「チャンネルIDが一致しません」：手順5の4で個人のチャンネルを選んでいる。手順5をやり直し、アカウント選択で「ミライ先生のAIマネー教室」（ブランドアカウント）を選ぶ。新しい Refresh token で Secrets の `YT_REFRESH_TOKEN` だけを更新する（「Update secret」）
