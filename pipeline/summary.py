"""実行結果をジョブの Summary（Markdown の表）にまとめる。失敗した段階もここでわかる。"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
LENGTH_MIN, LENGTH_MAX = 3 * 60, 15 * 60
LABELS = {"preflight": "入力チェック", "voice": "音声", "video": "動画", "thumbnail": "サムネ", "upload": "予約投稿"}
MARKS = {"success": "✅ 成功", "failure": "❌ 失敗", "cancelled": "⏹ 中止", "skipped": "－ 実行なし", "": "－ 実行なし"}


def video_seconds(path):
    if not path.is_file():
        return None
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
                           capture_output=True, text=True, check=False)
    try:
        return float(json.loads(probe.stdout)["format"]["duration"])
    except (ValueError, KeyError, json.JSONDecodeError):
        return None


def length_warning(seconds):
    if seconds is not None and not LENGTH_MIN <= seconds <= LENGTH_MAX:
        return f"動画の長さが {seconds / 60:.1f}分です（目安は3〜15分）"
    return None


def build(episode, outcomes, warnings, root=ROOT, upload="未実行（このしくみでは投稿しない）"):
    """outcomes: {段階: 'success'|'failure'|'skipped'|...}。Markdown を返す。"""
    output = root / "output" / episode
    seconds = video_seconds(output / "video" / "video.mp4")
    frames = sorted((output / "video" / "frames").glob("*.png")) if (output / "video" / "frames").is_dir() else []
    screens = len({frame.name.split("-")[0] for frame in frames})
    thumbnail = output / "thumbnail" / "thumbnail.png"
    warnings = [w for w in warnings if w]
    extra = length_warning(seconds)
    if extra:
        warnings.append(extra)
    failed = [LABELS.get(stage, stage) for stage, result in outcomes.items() if result == "failure"]
    rows = [f"## 動画工場の結果：{episode}", ""]
    rows.append(f"**{'❌ ' + '・'.join(failed) + ' で失敗' if failed else '✅ すべて成功'}**")
    rows += ["", "| 段階 | 結果 |", "|---|---|"]
    rows += [f"| {LABELS.get(stage, stage)} | {MARKS.get(result, result)} |" for stage, result in outcomes.items()]
    rows += ["", "| 項目 | 値 |", "|---|---|"]
    rows.append(f"| 動画の長さ | {f'{int(seconds // 60)}分{int(seconds % 60):02d}秒' if seconds is not None else '－'} |")
    rows.append(f"| 画面（スライド）数 | {screens or '－'} |")
    rows.append(f"| 確認用の静止画 | {len(frames) or '－'}枚 |")
    rows.append(f"| サムネ | {f'{thumbnail.stat().st_size / 1_000_000:.2f}MB' if thumbnail.is_file() else '－'} |")
    rows.append(f"| 予約投稿 | {upload} |")
    rows += ["", "### 警告", ""]
    rows += [f"- {warning}" for warning in warnings] or ["- なし"]
    return "\n".join(rows) + "\n", bool(failed)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--outcome", action="append", default=[], help="段階=結果（例: video=success）")
    parser.add_argument("--warnings-file")
    parser.add_argument("--summary-file", help="既定は標準出力")
    args = parser.parse_args(argv)
    outcomes = dict(item.split("=", 1) for item in args.outcome)
    warnings = []
    if args.warnings_file and Path(args.warnings_file).is_file():
        warnings = Path(args.warnings_file).read_text(encoding="utf-8").splitlines()
    text, failed = build(args.episode, outcomes, warnings)
    if args.summary_file:
        with open(args.summary_file, "a", encoding="utf-8") as stream:
            stream.write(text)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
