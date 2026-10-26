# 作業依頼 01：GitHub Actions の土台と音声生成

依頼者：Claude ／ 優先度：最優先 ／ 前提：AGENTS.md を読むこと

## 目的
台本（`script.txt`）から、セリフごとの音声とタイムラインを GitHub Actions 上で作れるようにする。動画工場の最初の部品。

## やること
1. `.github/workflows/factory.yml` を作る
   - `workflow_dispatch`。入力：`episode`（例 `ep000_sample`）、`stage`（`voice` / `voice_samples`。後の依頼で `video` `thumbnail` `upload` `all` を足す）
   - ubuntu-latest、Python 3.11、ffmpeg、Noto Sans JP をインストール
   - VOICEVOX エンジン（Docker のCPU版）をサービスとして起動し、起動完了を待つ
   - 成果物は artifact（名前：`<episode>-<stage>`）として保存する
2. `pipeline/script_parser.py`：AGENTS.md の台本形式を読み、行ごとの話者・セリフ・表情・スライド番号のリストを返す。形式エラーは行番号つきで止める
   - チェック：話者は `ミライ`/`ひなた` のみ、1セリフ40字以内（超えたら警告）、表情名は `config/characters.yaml` にあるもの、参照したスライド画像が存在するか（`--no-slide-check` で省略可）
3. `pipeline/make_voice.py`
   - セリフごとにWAVを作る。話者・話速・音高は `config/characters.yaml` の `voice`
   - `speaker_id` が `null` のときは、VOICEVOX の `/speakers` から `voice.name`（キャラ名＋スタイル名）で引く。どちらもないときは仮の声を使い、警告を出す
   - 読み辞書 `config/reading_dict.csv`（列：表記,読み,アクセント位置）をエンジンに登録してから合成する。ファイルがなければ空を作る
   - `timeline.json` を出力：行ごとの開始・終了秒、話者、表情、スライド番号、WAVのパス、音量の包絡（口パク用、30fps）
   - セリフ間に0.25秒、スライド切替時に0.6秒の間を入れる（値は `config/style.yaml`）
4. `stage=voice_samples`：声の聴き比べ用。候補の声で同じ2文を読み上げ、MP3にまとめる
   - 候補：ミライ役＝No.7、九州そら、冥鳴ひまり ／ ひなた役＝春日部つむぎ、四国めたん（各キャラの通常系スタイル）
   - 文：ミライ「結論から言うと、この会社はAIを売っているんじゃなくて、AIを動かす場所を貸しているんです」／ひなた「え、それってつまり大家さんってことですか！？」
   - ファイル名にキャラ名とスタイル名を入れる
5. `requirements.txt`、`pipeline/tests/` に `script_parser` の単体テスト

## 完了条件
- `stage=voice`、`episode=ep000_sample` で実行が成功し、artifact に WAV 一式と `timeline.json` がある
- `stage=voice_samples` で5人分のMP3がある
- 単体テストが通る
- PRに Actions の実行URLを貼る

## 補足
- `episodes/ep000_sample/slides/` は Claude が用意する。まだない場合は `--no-slide-check` で進めてよい
- VOICEVOX の利用規約上のクレジットは、後の依頼（動画・概要欄）で扱う
