# タスクボード

状態：未着手 / 作業中 / 完了 / 差し戻し / 承認待ち

| ID | 回 | 作業 | 担当 | 状態 | 次 | メモ |
|---|---|---|---|---|---|---|
| T001 | 共通 | GitHubリポジトリ作成 | 人 | 完了 | Codex | makomako56/ai-money-channel（Private） |
| T001b | 共通 | GitHubのClaude許可に ai-money-channel を追加 | 人 | 完了 | | Claudeから読み書き可能を確認（2026-10-24） |
| T001c | 共通 | （不要）クラウドのCodexを使う方式に変更 | - | 完了 | | 2026-10-26 |
| T001d | 共通 | Codexのクラウド環境を作成・公開、コードレビューを有効化 | 人 | 完了 | Claude | 2026-10-31 解決：@codex は使わず、Mac の Codex アプリ予定済みタスク「連絡確認」（毎時・プロジェクト ai-money-channel・gh 使用）が #15 を読む方式で稼働 |
| T001e | 共通 | テストIssueで @codex 連携を確認 | Claude | 未着手 | Claude | T001dの後 |
| T002 | 共通 | VOICEVOX導入、2人の声を決定 | 人 | 未着手 | Claude | 候補は設定書の「声」 |
| T003 | 共通 | YouTube APIの鍵を作りGitHub Secretsに登録 | 人 | 完了 | | 2026-11-03 OAuthアプリを「本番環境」に変更（ホーム・プライバシーポリシー・利用規約は https://makomako56.github.io ）。新しい client_secret と refresh_token を登録し upload_check 成功（run 41581024741）。7日失効はなくなった。古い client_secret は1つ残っているので削除する |
| T004 | 共通 | 声・Gemini画像・BGMの利用規約確認 → config/licenses.md | Claude | 作業中 | Claude | 全体とGeminiは確認済み。キャラ別は声の決定（T002）後 |
| T005 | 共通 | （作業依頼01〜05に置き換え） | - | 完了 | | |
| T006 | 共通 | ミライ先生の残り差分を生成（口少し開き・目閉じ・驚き・困り顔・ドヤ顔） | Codex | 未着手 | Claude | make_character.py で |
| T007 | 共通 | ひなたの立ち絵 | 人 | 作業中 | Claude | 口開き1枚を透過済み（assets/characters/hinata/transparent/hinata_02_normal_open.png）。口閉じの基本画像を依頼中。characters.yaml への登録は01bのマージ後にClaudeが行う |
| T008 | ep000 | 30秒サンプル台本 | Claude | 完了 | Codex | episodes/ep000_sample/script.txt |
| T009 | ep000 | サンプル30秒動画を生成 | Claude | 完了 | 人(CP0) | stage=all で生成（2026-10-27夜）。review-outputs/ep000_sample/video/video.mp4 |
| T037 | ep001 | 新しい声（まい）で本番動画を生成→オーナーOK→予約投稿 | Claude | 完了 | 人(Studioで確認) | 2026-11-03 オーナーOK。stage=upload（run 41563028266）で 11/3 18:00 JST に予約投稿。https://www.youtube.com/watch?v=PbxeScsFcOM 。オーナーが Studio で「公開予約」・サムネ反映を確認（ロックなし） |
| T038 | 共通 | サムネのデザインv3（2キャラ・PIVOT風）を動画工場に組み込む | Codex | 承認待ち | 人(マージ) | 2026-11-03 オーナー指示。見本 templates/thumbnail_v3/ep001.html、依頼 docs/作業依頼/06。PR #21（CI緑）→ 11/3 13:00 JST レビューで修正依頼：旧形式jsonで文字はみ出し・顔に重なる・1キャラ、重なりチェックとテスト、ep001の実物を review-outputs に。11/3 14:00 JST：追加コミット ee4aa70 の CI 失敗（ep000 サムネで顔の重なり検出＝古い形式の自動縮小が未対応）→ PR・#15 で再依頼。11/3 15:00 JST：ba6a1f2（CI緑・run 41581723645）を再レビューOK（ep000/ep001 とも2人・顔と文字の重なりなし）。巡回からのマージは権限で止められるため #15 でオーナーにマージを依頼 |
| T039 | 共通 | 毎朝のテーマ提案→制作→OKで予約公開 の流れを開始 | Claude | 完了 | | 2026-11-03。定時タスク「毎朝のテーマ提案」（7:13 JST）。docs/毎朝のテーマ提案と制作の流れ.md |
| T040 | ep101〜104 | 予備4本「AIで追い風の会社ファイル」（アドバンテスト・フジクラ・日立・さくらインターネット） | Claude | 完了 | Claude(順に使う) | 2026-11-03 stage=all 成功（run ep101 41585741290／ep102 41585748959／ep103 41585756245／ep104 41585763567）。プレビュー https://claude.ai/artifact/9StVLqav4ZYAwyDWxSYb9T 。**2026-11-03 オーナーが全部OK**。使用済み：ep101（11/4 18:00 JST に予約投稿済み。2026-11-04 02:10 JST の巡回で stage=upload 成功（run 41680895677）https://www.youtube.com/watch?v=mX3mCcc1D9I 。サムネは旧デザイン。**ep101 の upload は再実行しない**）。残り予備：ep102・ep103・ep104。OKの回はニュースの回が作れない日に順に予約公開。決算発表後に出す回は数字を更新 |
| T010 | ep000 | CP0：キャラ・声・画面構成を承認 | 人 | 承認待ち | Claude | ここを越えたら毎日制作へ |
| T011 | ep001 | テーマ3案 | Claude | 完了 | 人(CP1) | tasks/ep001_テーマ案.md |
| T012 | ep001 | CP1：テーマを1つ選ぶ | 人 | 完了 | | ディスコに決定（2026-10-26） |
| T013 | ep001 | リサーチ・台本・スライド11枚・meta・サムネ文言 | Claude | 完了 | 人(CP2) | episodes/ep001_disco/ |
| T014 | ep001 | CP2：スライドレビュー（OK/NG） | 人 | 承認待ち | Claude | v2で作り直し済み。動画・静止画59枚・サムネが review-outputs/ep001_disco/ にある（2026-10-27夜） |
| T020 | 共通 | 作業依頼01：Actions土台と音声生成 | Codex | 完了 | | PR #6 マージ済み（2026-10-26） |
| T020b | 共通 | 作業依頼01b：音声の追補（Issue #7） | Codex | 完了 | | PR #8 マージ済み（2026-10-27、Claudeレビュー） |
| T029 | 共通 | Codexのクラウド環境を作成（chatgpt.com/codex/cloud/settings/environments） | 人 | 任意 | | Codexは自分で進めるため必須ではない。作れば GitHub の @codex でも依頼できる |
| T021 | 共通 | 作業依頼02a：動画の組み立て（録画方式・最小版） | Codex | 完了 | | PR #9 マージ（2026-10-27、書式v2対応・CI安定化はClaudeが追加） |
| T027 | ep001 | ep001を書式v2で作り直す | Claude | 完了 | 人(CP2) | pages/ 18画面、台本119行・約8分。プレビュー動画あり |
| T028 | 共通 | 表情・ポーズの立ち絵（docs/立ち絵の作成リスト.md） | 人 | ほぼ完了 | Claude | 2人とも表情・口パク・まばたきが完了（表情シートから合成・登録済み）。残りは任意：口の半開き、ポーズ（指さし・ばんざい） |
| T021b | 共通 | 作業依頼02b：動画の組み立て（仕上げ） | Claude | 完了 | | PR #10 マージ（2026-10-27）。静止画59枚・旧書式・BGM（ファイルがあれば）・ep001で21分 |
| T022 | 共通 | 作業依頼03：サムネ生成 | Codex | 完了 | | PR #11 マージ（2026-10-27）。review-outputs/ep001_disco/thumbnail/ |
| T023 | 共通 | 作業依頼04：YouTube予約投稿 | Codex | 完了 | | PR #13 マージ（2026-10-28、オーナー許可・Claudeレビュー）。upload_check は認証成功・チャンネルID不一致で停止（誤投稿防止が正常に動作）→T031 |
| T024 | 共通 | 作業依頼05：一括実行 | Codex | 完了 | | 前半は PR #12、残り（05b）は PR #18 マージ（2026-11-02、Codexが衝突解消→CI緑・差分が前回レビュー時と同じことを確認し Claude がマージ）。注意：投稿成功後に結果保存ジョブだけ失敗すると再実行で二重投稿の恐れ→初回投稿後に review-outputs の upload_result.json を確認 |
| T033 | 共通 | 本番の player（pipeline/stage/player.html）の字幕アイコンを face/ の顔画像に切り替える | Codex | 完了 | Claude(レビュー) | PR #16 マージ（2026-10-31、オーナーOK） |
| T034 | 共通 | 連絡板の自動実行テスト（T033の行を更新） | Codex | 完了 | Claude(レビュー) | PR #17 マージ（2026-10-31）。Codexの予定済みタスクが #15 の依頼を自動で拾いPR作成まで成功 |
| T035 | 共通 | サムネに2人目のキャラ（ひなた）を出せるようにする | Codex | 承認待ち | 人(マージ) | 2026-11-01 オーナー指示。PR #19：Codex修正済み→Claude再レビューOK（CI緑・描画で重なりなしを確認）。巡回からのマージは権限で止められるため、#15 でサムネ確認とマージを依頼（プレビュー https://claude.ai/artifact/MBFoVmqi8NoEXZC5jxpW93） |
| T036 | 共通 | AivisHub の追加モデル（ミライの新しい声の候補5つ）を入れられるようにする | Codex | 完了 | 人(声の選択) | 2026-11-01 オーナー指示。PR #20 マージ（2026-11-01、CI緑・Claudeレビュー）。声の候補は聞き比べページ（7〜10）で #15 にてオーナーの選択待ち |
| T032 | 共通 | YouTube投稿エラーの表示改善・Actions更新（PR #14） | Codex | 完了 | Claude | PR #14 マージ（2026-10-31、オーナーOK） |
| T025 | ep000 | サンプル用スライド3枚 | Claude | 完了 | Codex | episodes/ep000_sample/slides/ |
| T026 | 共通 | 声の選定 | 人 | 完了 | | AivisSpeech。ミライ＝まい（ノーマル・2026-11-03 決定、まおから変更）、ひなた＝コハク |
| T030 | 共通 | YouTubeチャンネル開設・中級者向け機能（カスタムサムネ）を有効化 | 人 | 完了 | | 2026-10-27 |
| T031 | 共通 | YouTubeの鍵を作り直す（ブランドアカウント「AI企業ニュース」で認可） | 人 | 完了 | | 2026-10-28。テストユーザーにブランドアカウントのアドレスと tenissanalysis@gmail.com を追加。upload_check 成功（run 40705702609）。鍵は「テスト中」のため約7日で失効→11/4ごろ更新が必要。client_secret がチャットのスクショに写ったため取り替えを案内 |
| T041 | 11/5分 | 題材提案 2026-11-04：オーナーの返事待ち | 人 | 返事待ち | Claude(制作) | #15 に3案（★1 AMD／2 パランティア／3 マーベル）https://github.com/makomako56/ai-money-channel/issues/15#issuecomment-6616878324 。11/5 18:00 公開分（11/4分は予備 ep101 予約済み） |
