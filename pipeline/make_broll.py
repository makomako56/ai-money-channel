"""Fetch Pexels clips for episodes whose meta.json enables the b-roll style."""
import argparse
import json
import os
import shutil
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
API_URL = "https://api.pexels.com/videos/search"


def required_clips(timeline):
    """Return contiguous b-roll sections and the duration each clip must cover."""
    sections = []
    current = None
    for item in timeline:
        keyword = item.get("broll_keyword")
        if not keyword:
            current = None
            continue
        if current is None or current["keyword"] != keyword:
            current = {"keyword": keyword, "note": item.get("broll_note", ""),
                       "start": float(item["start"]), "end": float(item["end"])}
            sections.append(current)
        else:
            current["end"] = float(item["end"])
    for section in sections:
        section["required_seconds"] = round(section["end"] - section["start"], 3)
    return sections


def best_file(video):
    files = [item for item in video.get("video_files", [])
             if item.get("file_type") == "video/mp4" and str(item.get("link", "")).startswith("https://")
             and int(item.get("width") or 0) > int(item.get("height") or 0)]
    if not files:
        return None
    return min(files, key=lambda item: (item.get("quality") != "hd", int(item.get("width") or 0) < 1280,
                                        abs(int(item.get("width") or 0) - 1920)))


def candidate_info(video):
    selected = best_file(video)
    return {"id": video.get("id"), "duration": video.get("duration"),
            "url": video.get("url"), "photographer": video.get("user", {}).get("name"),
            "width": selected.get("width") if selected else None,
            "height": selected.get("height") if selected else None,
            "download_url": selected.get("link") if selected else None}


def api_candidates(keyword, api_key, minimum_duration, opener=urllib.request.urlopen):
    query = urllib.parse.urlencode({"query": keyword, "orientation": "landscape", "size": "medium", "per_page": 15})
    request = urllib.request.Request(f"{API_URL}?{query}", headers={"Authorization": api_key})
    with opener(request, timeout=30) as response:
        payload = json.loads(response.read())
    candidates = [candidate_info(video) for video in payload.get("videos", [])]
    return [item for item in candidates if item["download_url"]
            and float(item.get("duration") or 0) >= minimum_duration][:3]


def download(url, target, opener=urllib.request.urlopen):
    if not str(url).startswith("https://"):
        raise ValueError("素材URLはhttpsが必要です")
    temporary = target.with_suffix(".part")
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with opener(urllib.request.Request(url), timeout=180) as response, temporary.open("wb") as stream:
            shutil.copyfileobj(response, stream)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def generate(episode, api_key, *, root=ROOT, opener=urllib.request.urlopen, cache_dir=None):
    episode_dir = root / "episodes" / episode
    meta = json.loads((episode_dir / "meta.json").read_text(encoding="utf-8"))
    if meta.get("video_style") != "broll":
        print("映像モードではないため素材取得を省略します")
        return None
    timeline = json.loads((root / "output" / episode / "voice" / "timeline.json").read_text(encoding="utf-8"))
    output = root / "output" / episode / "broll"
    output.mkdir(parents=True, exist_ok=True)
    cache_dir = Path(cache_dir) if cache_dir else root / ".cache" / "pexels-broll"
    clips = []
    for section in required_clips(timeline):
        record = {**section, "status": "fallback", "candidates": []}
        if not api_key:
            record["fallback_reason"] = "PEXELS_API_KEY is not configured"
            clips.append(record)
            continue
        try:
            candidates = api_candidates(section["keyword"], api_key, section["required_seconds"], opener)
            record["candidates"] = candidates
            if not candidates:
                record["fallback_reason"] = "no landscape HD clip long enough"
                clips.append(record)
                continue
            chosen = candidates[0]
            cached = cache_dir / f'{chosen["id"]}.mp4'
            if not cached.is_file():
                download(chosen["download_url"], cached, opener)
            relative = Path("files") / cached.name
            (output / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cached, output / relative)
            record.update(status="ready", id=chosen["id"], url=chosen["url"],
                          photographer=chosen["photographer"], duration=chosen["duration"], file=str(relative))
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
                urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            record["fallback_reason"] = f"Pexels request failed: {type(exc).__name__}"
        clips.append(record)
    manifest = {"source": "Pexels", "clips": clips}
    (output / "broll.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ready = sum(clip["status"] == "ready" for clip in clips)
    print(f"映像素材: {ready}/{len(clips)}件（残りは図解へフォールバック）")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--cache-dir")
    args = parser.parse_args()
    if not args.episode or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for char in args.episode):
        parser.error("episode は英数字、_、- のみ指定できます")
    try:
        generate(args.episode, os.environ.get("PEXELS_API_KEY", ""), cache_dir=args.cache_dir)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")


if __name__ == "__main__":
    main()
