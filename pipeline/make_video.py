"""Record the preview player against the generated voice timeline and mux its audio."""
import argparse
import json
import math
import os
import re
import shutil
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import wave
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread


ROOT = Path(__file__).resolve().parent.parent
RATE = 24000
CREDIT_SECONDS = 2
BGM_DIR = ROOT / "assets" / "bgm_se"
BGM_DB = -24
FRAME_SETTLE = 0.7  # 段階表示のアニメーションが落ち着くまでの秒数
REVIEW_LIMIT = 100_000_000


def build_audio(timeline_path, voice_dir, target):
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    if not isinstance(timeline, list) or not timeline:
        raise ValueError("timeline.json が空です")
    cursor = 0
    with wave.open(str(target), "wb") as output:
        output.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
        for item in timeline:
            start = float(item["start"])
            end = float(item["end"])
            if not math.isfinite(start) or not math.isfinite(end) or start < 0 or end <= start:
                raise ValueError("timeline.json の start/end が不正です")
            relative = Path(item["wav"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("timeline.json の wav パスが不正です")
            wav_path = (voice_dir / relative).resolve()
            if not wav_path.is_relative_to(voice_dir.resolve()) or not wav_path.is_file():
                raise ValueError(f"音声WAVがありません: {relative}")
            with wave.open(str(wav_path), "rb") as source:
                if source.getcomptype() != "NONE" or source.getsampwidth() != 2 or source.getnchannels() != 1 or source.getframerate() != RATE:
                    raise ValueError(f"音声形式は24kHz/16bit/mono PCMが必要です: {relative}")
                frames = source.getnframes()
                pcm = source.readframes(frames)
            start_frame = max(cursor, round(start * RATE))
            output.writeframes(b"\0\0" * (start_frame - cursor))
            output.writeframes(pcm)
            cursor = start_frame + frames
        tail = round(CREDIT_SECONDS * RATE)
        output.writeframes(b"\0\0" * tail)
    return max(float(item["end"]) for item in timeline) + CREDIT_SECONDS


def frame_times(events, duration):
    """画面・段階の切替ごとに (ファイル名, 秒) を返す。次の切替の直前を超えない。"""
    result = []
    events = sorted(events, key=lambda e: float(e["t"]))
    for index, event in enumerate(events):
        screen, step, start = str(event["screen"]), int(event["step"]), float(event["t"])
        if not re.fullmatch(r"[0-9]{2,3}", screen) or step < 1 or not math.isfinite(start):
            raise ValueError(f"画面の切替記録が不正です: {event}")
        end = float(events[index + 1]["t"]) if index + 1 < len(events) else duration
        at = min(start + FRAME_SETTLE, (start + end) / 2) if end > start else start
        result.append((f"{screen}-{step}.png", round(max(0.0, min(at, duration - 0.05)), 3)))
    return list(dict((name, at) for name, at in result).items())  # 同じ名前は最後の段階を使う


def find_bgm(directory=BGM_DIR):
    """assets/bgm_se/bgm.(mp3|wav|ogg|m4a) があれば返す。なければ None（BGMなし）。"""
    for suffix in (".mp3", ".wav", ".ogg", ".m4a"):
        candidate = directory / f"bgm{suffix}"
        if candidate.is_file():
            return candidate
    return None


def encode_command(webm, audio, offset, duration, video, review, bgm=None):
    """1回のデコードで本番（1080p）と確認用（854×480）を同時に書き出す。"""
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
               "-ss", f"{offset:.6f}", "-i", str(webm), "-i", str(audio)]
    if bgm:
        command += ["-stream_loop", "-1", "-i", str(bgm)]
        audio_graph = (f"[2:a]volume={BGM_DB}dB,aresample=48000[bg];[1:a]aresample=48000[vo];"
                       f"[vo][bg]amix=inputs=2:duration=first:normalize=0[mix];[mix]asplit=2[a1][a2]")
    else:
        audio_graph = "[1:a]aresample=48000,asplit=2[a1][a2]"
    command += ["-filter_complex", f"[0:v]fps=30,split=2[v1][v0];[v0]scale=854:480:flags=lanczos[v2];{audio_graph}",
                "-map", "[v1]", "-map", "[a1]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                "-t", f"{duration:.6f}", str(video),
                "-map", "[v2]", "-map", "[a2]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "32",
                "-maxrate", "800k", "-bufsize", "1600k", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "64k",
                "-movflags", "+faststart", "-t", f"{duration:.6f}", str(review)]
    return command


def extract_frames(video, frames, target):
    target.mkdir(parents=True, exist_ok=True)
    for name, at in frames:
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-ss", f"{at:.3f}",
                        "-i", str(video), "-frames:v", "1", "-vf", "scale=960:540:flags=lanczos",
                        str(target / name)], check=True)


def render(episode, webm_path, duration):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, *_):
            pass

    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(ROOT), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    node_script = r"""
const { chromium } = require("playwright");
(async () => {
  const [port, episode, output] = process.argv.slice(1);
  const browser = await chromium.launch({headless:true});
  const context = await browser.newContext({viewport:{width:1920,height:1080},recordVideo:{dir:require("path").dirname(output),size:{width:1920,height:1080}}});
  const page = await context.newPage();
  const pageCreatedAt = Date.now();
  page.on("pageerror", error => console.error(error.message));
  await page.goto("http://127.0.0.1:"+port+"/pipeline/stage/player.html?ep="+encodeURIComponent(episode), {waitUntil:"load"});
  await page.waitForFunction(() => document.title === "done" || document.title === "error", null, {timeout:1200000});
  if (await page.title() === "error") throw new Error(await page.evaluate(() => document.body.dataset.error || "player failed"));
  const playerOrigin = await page.evaluate(() => window.__origin);
  const offset = (playerOrigin - pageCreatedAt) / 1000;
  if (!Number.isFinite(offset) || offset < 0) throw new Error("invalid player origin offset: "+offset);
  process.stdout.write("VIDEO_ORIGIN_OFFSET_SECONDS="+offset.toFixed(6)+"\n");
  process.stdout.write("VIDEO_EVENTS="+JSON.stringify(await page.evaluate(() => window.__events || []))+"\n");
  const video = page.video();
  await context.close();
  await video.saveAs(output);
  await browser.close();
})().catch(error => { console.error(error.stack || error); process.exit(1); });
"""
    try:
        result = subprocess.run(["node", "-e", node_script, str(port), episode, str(webm_path)],
                                cwd=ROOT, capture_output=True, text=True,
                                timeout=max(1200, duration + 300))
        if result.returncode:
            raise RuntimeError("Playwright録画に失敗しました: " + result.stderr[-2000:])
        match = re.search(r"VIDEO_ORIGIN_OFFSET_SECONDS=([0-9]+(?:\.[0-9]+)?)", result.stdout)
        if not match:
            raise RuntimeError("Playwrightから録画開始時刻を受け取れませんでした")
        offset = float(match.group(1))
        if not math.isfinite(offset) or offset < 0:
            raise RuntimeError(f"録画開始時刻が不正です: {offset}")
        events = re.search(r"^VIDEO_EVENTS=(.*)$", result.stdout, re.M)
        return offset, json.loads(events.group(1)) if events else []
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--review-dir", help="確認用コピーの出力先（既定: output/review/<ep>/video）")
    args = parser.parse_args()
    if not args.episode or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for char in args.episode):
        parser.error("episode は英数字、_、- のみ指定できます")
    episode_dir = ROOT / "episodes" / args.episode
    voice_dir = ROOT / "output" / args.episode / "voice"
    output_dir = ROOT / "output" / args.episode / "video"
    if not episode_dir.is_dir() or not (episode_dir / "script.txt").is_file():
        parser.error(f"エピソードがありません: {args.episode}")
    if not (voice_dir / "engine.json").is_file():
        parser.error("先に音声を生成してください（output/<ep>/voice）")
    if output_dir.exists():
        parser.error(f"出力先が既にあります: {output_dir}")
    review_dir = Path(args.review_dir) if args.review_dir else ROOT / "output" / "review" / args.episode / "video"
    output_dir.mkdir(parents=True)
    try:
        timeline = voice_dir / "timeline.json"
        with tempfile.TemporaryDirectory(dir=output_dir, prefix=".record-") as temporary:
            temp = Path(temporary)
            audio = temp / "narration.wav"
            webm = temp / "recording.webm"
            duration = build_audio(timeline, voice_dir, audio)
            offset, events = render(args.episode, webm, duration)
            print(f"映像の先頭待機を同期補正: {offset:.3f}秒", flush=True)
            video = output_dir / "video.mp4"
            review_dir.mkdir(parents=True, exist_ok=True)
            review = review_dir / "video.mp4"
            bgm = find_bgm()
            print(f"BGM: {bgm.relative_to(ROOT) if bgm else 'なし（assets/bgm_se/bgm.* がない）'}", flush=True)
            subprocess.run(encode_command(webm, audio, offset, duration, video, review, bgm), check=True)
        frames = frame_times(events, duration)
        extract_frames(video, frames, output_dir / "frames")
        shutil.copytree(output_dir / "frames", review_dir / "frames", dirs_exist_ok=True)
        if review.stat().st_size >= REVIEW_LIMIT:
            raise RuntimeError(f"確認用の動画が100MB以上です: {review.stat().st_size} bytes")
        print(f"確認用の静止画: {len(frames)}枚", flush=True)
        probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height",
                                "-of", "json", str(video)], check=True, capture_output=True, text=True)
        streams = json.loads(probe.stdout)["streams"]
        if not any(s.get("codec_type") == "video" and s.get("codec_name") == "h264" and s.get("width") == 1920 and s.get("height") == 1080 for s in streams):
            raise RuntimeError("出力動画がH.264/1920x1080ではありません")
        if not any(s.get("codec_type") == "audio" and s.get("codec_name") == "aac" for s in streams):
            raise RuntimeError("出力音声がAACではありません")
        print(f"動画を作成しました: {video} ({duration:.1f}秒)", flush=True)
    except (OSError, KeyError, TypeError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise SystemExit(f"ERROR: {exc}") from exc


if __name__ == "__main__":
    main()
