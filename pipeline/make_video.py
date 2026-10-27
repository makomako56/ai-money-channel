"""Record the preview player against the generated voice timeline and mux its audio."""
import argparse
import json
import math
import os
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
  page.on("pageerror", error => console.error(error.message));
  await page.goto("http://127.0.0.1:"+port+"/pipeline/stage/player.html?ep="+encodeURIComponent(episode), {waitUntil:"load"});
  await page.waitForFunction(() => document.title === "done" || document.title === "error", null, {timeout:1200000});
  if (await page.title() === "error") throw new Error(await page.evaluate(() => document.body.dataset.error || "player failed"));
  const video = page.video();
  await context.close();
  await video.saveAs(output);
  await browser.close();
})().catch(error => { console.error(error.stack || error); process.exit(1); });
"""
    try:
        subprocess.run(["node", "-e", node_script, str(port), episode, str(webm_path)],
                       cwd=ROOT, check=True, timeout=max(1200, duration + 300))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True)
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
    output_dir.mkdir(parents=True)
    try:
        timeline = voice_dir / "timeline.json"
        with tempfile.TemporaryDirectory(dir=output_dir, prefix=".record-") as temporary:
            temp = Path(temporary)
            audio = temp / "narration.wav"
            webm = temp / "recording.webm"
            duration = build_audio(timeline, voice_dir, audio)
            render(args.episode, webm, duration)
            video = output_dir / "video.mp4"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                            "-i", str(webm), "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                            "-r", "30", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                            "-t", f"{duration:.6f}", str(video)], check=True)
        probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height",
                                "-of", "json", str(video)], check=True, capture_output=True, text=True)
        streams = json.loads(probe.stdout)["streams"]
        if not any(s.get("codec_type") == "video" and s.get("codec_name") == "h264" and s.get("width") == 1920 and s.get("height") == 1080 for s in streams):
            raise RuntimeError("出力動画がH.264/1920x1080ではありません")
        if not any(s.get("codec_type") == "audio" and s.get("codec_name") == "aac" for s in streams):
            raise RuntimeError("出力音声がAACではありません")
        print(f"動画を作成しました: {video} ({duration:.1f}秒)", flush=True)
    except (OSError, KeyError, TypeError, ValueError, subprocess.CalledProcessError) as exc:
        import shutil
        shutil.rmtree(output_dir, ignore_errors=True)
        raise SystemExit(f"ERROR: {exc}") from exc


if __name__ == "__main__":
    main()
