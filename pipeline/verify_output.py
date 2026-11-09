"""Check actual generated audio before uploading the artifact."""
import argparse
import json
import math
import os
import subprocess
from pathlib import Path

from pipeline.make_voice import inspect_wav, load_gaps
from pipeline.script_parser import episode_video_style, load_characters, parse_script


def verify(episode, stage):
    output = Path("output") / episode / stage
    if stage == "voice":
        timeline = json.loads((output / "timeline.json").read_text(encoding="utf-8"))
        episode_dir = Path("episodes") / episode
        expected = parse_script(episode_dir / "script.txt", load_characters("config/characters.yaml"),
                                check_slides=False, video_style=episode_video_style(episode_dir))
        if len(timeline) != len(expected):
            raise ValueError("台本とタイムラインのセリフ数が不一致です")
        gaps = load_gaps("config/style.yaml")
        previous_end, previous_slide = 0, None
        wavs = []
        for index, (item, line) in enumerate(zip(timeline, expected)):
            for key in ("line", "speaker", "text", "expression", "slide"):
                if item[key] != line[key]:
                    raise ValueError(f"台本とタイムラインが不一致: {key}")
            wav = output / item["wav"]
            if not wav.resolve().is_relative_to(output.resolve()):
                raise ValueError("WAVが出力先の外を参照しています")
            duration, envelope = inspect_wav(wav.read_bytes())
            gap = 0 if index == 0 else gaps[int(item["slide"] != previous_slide)]
            if not math.isclose(item["start"], previous_end + gap, abs_tol=1e-9):
                raise ValueError("タイムラインの間が不正です")
            if not math.isclose(item["end"] - item["start"], duration, abs_tol=1e-9):
                raise ValueError("WAVとタイムラインの尺が不一致です")
            if item["envelope_fps"] != 30 or item["envelope"] != envelope or not any(envelope):
                raise ValueError("音量の包絡が不一致、または音声が無音です")
            wavs.append(wav)
            previous_end, previous_slide = item["end"], item["slide"]
        if len(set(wavs)) != len(expected) or set(wavs) != set(output.glob("wav/*.wav")):
            raise ValueError("WAVの数が不正です")
        summary = f"voice: {len(wavs)} WAV + timeline.json、尺 {previous_end:.3f}秒、30fps包絡・セリフ間{gaps[0]}秒/切替{gaps[1]}秒を検証"
    else:
        mp3s = sorted(output.glob("*.mp3"))
        manifest = json.loads((output / "samples.json").read_text(encoding="utf-8"))
        catalog = json.loads((output / "engine.json").read_text(encoding="utf-8"))["catalog"]
        voices = manifest["voices"]
        if not catalog or len(voices) != len(catalog) or {v["id"] for v in voices} != {v["id"] for v in catalog}:
            raise ValueError("全話者・全スタイルのサンプルが揃っていません")
        for item in voices:
            if not any(all(item[key] == voice[key] for key in ("id", "name", "style")) for voice in catalog):
                raise ValueError("サンプルの話者情報が不一致です")
        if {p.name for p in mp3s} != {v["mp3"] for v in voices} or len(mp3s) != len(voices):
            raise ValueError("MP3とサンプル一覧が一致しません")
        for path in mp3s:
            probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)], capture_output=True, text=True, check=True)
            duration = float(json.loads(probe.stdout)["format"]["duration"])
            if not math.isfinite(duration) or duration <= 0:
                raise ValueError(f"MP3の尺が不正: {path}")
            subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-nostdin", "-i", str(path), "-f", "null", "-"], check=True)
            print(f"MP3検証: {path.name}, {duration:.3f}秒")
        summary = f"voice_samples: 全{len(catalog)}スタイルのMP3、全ファイルの尺とデコードを検証"
    print(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
            stream.write(f"- {summary}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--stage", choices=("voice", "voice_samples"), required=True)
    args = parser.parse_args()
    verify(args.episode, args.stage)
