# 作業依頼08：Actions の artifact の容量を減らす（2026-11-15 Claude）

## なぜ
2026-11-15 の ep012（run 43708001345）が「Upload original video」で失敗：
`Failed to CreateArtifact: Artifact storage quota has been hit. Unable to upload any new artifacts.`
有効な artifact は約756MB（多くが ep000・ep900・ep901 の試作と、毎回の `-all-review`）。このままだと毎日の動画が作れない。

## やること（`.github/workflows/factory.yml` だけ）
1. `<ep>-<stage>-review`（publish-review 用の確認コピー）の `retention-days` を **1** にする（publish-review が同じ実行の中で review-outputs ブランチに載せるので、それ以上は要らない）
2. 音声だけの artifact（`voice` / `voice_samples`）の `retention-days` を **2** にする
3. `<ep>-video`・`<ep>-thumbnail` は **7日のまま**（stage=upload が source_run_id から取り出すため。短くしない）
4. `<ep>-upload-result` は 30日のまま（二重投稿防止）

## 完了条件
- CI 緑。差分は retention-days の数字だけ
- 台本・画面・meta・承認の流れには触らない
- 既存の artifact の削除はしない（削除はオーナーの判断）

## 読むファイル
- `.github/workflows/factory.yml`（200〜300行目あたり）
- `AGENTS.md`
