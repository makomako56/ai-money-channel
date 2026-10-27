"""Create a small review-only copy; keep original WAV artifacts unchanged."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

from pipeline.engine_config import validate_episode


def prepare(episode, stage):
    validate_episode(episode)
    if stage not in ("voice", "voice_samples"):
        raise ValueError("未対応のstageです")
    source = Path("output") / episode / stage
    target = Path("output/review") / episode / stage
    target.mkdir(parents=True, exist_ok=False)
    if stage == "voice":
        timeline = json.loads((source / "timeline.json").read_text(encoding="utf-8"))
        (target / "mp3").mkdir()
        for index, item in enumerate(timeline, 1):
            wav = source / item["wav"]
            if not wav.resolve().is_relative_to(source.resolve()):
                raise ValueError("WAVが出力先の外を参照しています")
            relative = f"mp3/{index:04d}.mp3"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                            "-i", str(wav), "-codec:a", "libmp3lame", "-b:a", "96k", str(target / relative)], check=True)
            item["review_audio"] = relative
        (target / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        manifest = json.loads((source / "samples.json").read_text(encoding="utf-8"))
        for voice in manifest["voices"]:
            filename = voice["mp3"]
            if Path(filename).name != filename:
                raise ValueError("サンプルのファイル名が不正です")
            shutil.copy2(source / filename, target / filename)
        shutil.copy2(source / "samples.json", target / "samples.json")
    shutil.copy2(source / "engine.json", target / "engine.json")
    # Prove the review MP3s are decodable before they leave the generation job.
    mp3s = list(target.rglob("*.mp3"))
    if not mp3s:
        raise ValueError("確認用MP3がありません")
    for path in mp3s:
        subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-nostdin", "-i", str(path), "-f", "null", "-"], check=True)
    print(f"確認用コピー: {target} ({len(mp3s)} MP3)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--stage", choices=("voice", "voice_samples"), required=True)
    args = parser.parse_args()
    prepare(args.episode, args.stage)
