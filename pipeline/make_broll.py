"""Fetch stock clips for episodes whose meta.json enables the b-roll style."""
import argparse
import hashlib
import json
import os
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROVIDERS = {
    "pixabay": {"api_url": "https://pixabay.com/api/videos/", "api_key_env": "PIXABAY_API_KEY"},
    "pexels": {"api_url": "https://api.pexels.com/videos/search", "api_key_env": "PEXELS_API_KEY"},
}
REQUEST_HEADERS = {
    "User-Agent": "ai-money-channel/1.0",
    "Accept": "application/json",
}


def load_config(root=ROOT):
    data = {}
    for line in (Path(root) / "config" / "broll.yaml").read_text(encoding="utf-8").splitlines():
        content = line.split("#", 1)[0].strip()
        if content and ":" in content:
            key, value = content.split(":", 1)
            data[key.strip()] = value.strip()
    provider = str(data.get("provider", "pixabay")).lower()
    if provider not in PROVIDERS:
        raise ValueError(f"未対応の映像素材取得元です: {provider}")
    return {"provider": provider, "search_cache_hours": int(data.get("search_cache_hours", 24))}


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
    """Return the best landscape MP4 from a Pexels API video (legacy provider)."""
    files = [item for item in video.get("video_files", [])
             if item.get("file_type") == "video/mp4" and str(item.get("link", "")).startswith("https://")
             and int(item.get("width") or 0) > int(item.get("height") or 0)]
    if not files:
        return None
    return min(files, key=lambda item: (item.get("quality") != "hd", int(item.get("width") or 0) < 1280,
                                        abs(int(item.get("width") or 0) - 1920)))


def best_pixabay_file(video):
    files = [item for item in video.get("videos", {}).values()
             if str(item.get("url", "")).startswith("https://")
             and int(item.get("width") or 0) > int(item.get("height") or 0)]
    if not files:
        return None
    return min(files, key=lambda item: (int(item.get("width") or 0) < 1280,
                                        int(item.get("height") or 0) < 720,
                                        abs(int(item.get("width") or 0) - 1920)))


def candidate_info(video, provider):
    if provider == "pixabay":
        selected = best_pixabay_file(video)
        return {"id": video.get("id"), "duration": video.get("duration"),
                "page_url": video.get("pageURL"), "contributor": video.get("user"),
                "width": selected.get("width") if selected else None,
                "height": selected.get("height") if selected else None,
                "download_url": selected.get("url") if selected else None}
    selected = best_file(video)
    return {"id": video.get("id"), "duration": video.get("duration"),
            "page_url": video.get("url"), "contributor": video.get("user", {}).get("name"),
            "width": selected.get("width") if selected else None,
            "height": selected.get("height") if selected else None,
            "download_url": selected.get("link") if selected else None}


def _request_candidates(keyword, api_key, provider, opener):
    settings = PROVIDERS[provider]
    if provider == "pixabay":
        query = urllib.parse.urlencode({"key": api_key, "q": keyword, "min_width": 1280,
                                        "min_height": 720, "safesearch": "true",
                                        "order": "popular", "per_page": 15})
        request = urllib.request.Request(f'{settings["api_url"]}?{query}', headers=REQUEST_HEADERS)
        result_key = "hits"
    else:
        query = urllib.parse.urlencode({"query": keyword, "orientation": "landscape",
                                        "size": "medium", "per_page": 15})
        request = urllib.request.Request(
            f'{settings["api_url"]}?{query}',
            headers={**REQUEST_HEADERS, "Authorization": api_key},
        )
        result_key = "videos"
    with opener(request, timeout=30) as response:
        payload = json.loads(response.read())
    return [candidate_info(video, provider) for video in payload.get(result_key, [])]


def api_candidates(keyword, api_key, minimum_duration, provider="pixabay", *,
                   opener=urllib.request.urlopen, cache_dir=None, cache_hours=24, now=None):
    """Return up to three candidates, caching key-free search results for 24 hours."""
    now = time.time() if now is None else now
    cache_dir = Path(cache_dir) if cache_dir else ROOT / ".cache" / "broll"
    cache_key = hashlib.sha256(f"{provider}\0{keyword}\0{minimum_duration}".encode("utf-8")).hexdigest()
    cache_file = cache_dir / "search" / f"{cache_key}.json"
    fresh = cache_file.is_file() and now - cache_file.stat().st_mtime < cache_hours * 3600
    if fresh:
        candidates = json.loads(cache_file.read_text(encoding="utf-8"))
    else:
        candidates = _request_candidates(keyword, api_key, provider, opener)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return [item for item in candidates if item["download_url"]
            and float(item.get("duration") or 0) >= minimum_duration][:3]


def download(url, target, opener=urllib.request.urlopen):
    if not str(url).startswith("https://"):
        raise ValueError("素材URLはhttpsが必要です")
    temporary = target.with_suffix(".part")
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        request = urllib.request.Request(url, headers=REQUEST_HEADERS)
        with opener(request, timeout=180) as response, temporary.open("wb") as stream:
            shutil.copyfileobj(response, stream)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def generate(episode, api_key, *, provider="pixabay", root=ROOT,
             opener=urllib.request.urlopen, cache_dir=None, cache_hours=24):
    episode_dir = root / "episodes" / episode
    meta = json.loads((episode_dir / "meta.json").read_text(encoding="utf-8"))
    if meta.get("video_style") != "broll":
        print("映像モードではないため素材取得を省略します")
        return None
    timeline = json.loads((root / "output" / episode / "voice" / "timeline.json").read_text(encoding="utf-8"))
    output = root / "output" / episode / "broll"
    output.mkdir(parents=True, exist_ok=True)
    cache_dir = Path(cache_dir) if cache_dir else root / ".cache" / "broll"
    clips = []
    for section in required_clips(timeline):
        record = {**section, "status": "fallback", "candidates": []}
        if not api_key:
            record["fallback_reason"] = f'{PROVIDERS[provider]["api_key_env"]} is not configured'
            clips.append(record)
            continue
        try:
            candidates = api_candidates(section["keyword"], api_key, section["required_seconds"], provider,
                                        opener=opener, cache_dir=cache_dir, cache_hours=cache_hours)
            record["candidates"] = candidates
            if not candidates:
                record["fallback_reason"] = "no landscape HD clip long enough"
                clips.append(record)
                continue
            chosen = candidates[0]
            cached = cache_dir / "videos" / f'{provider}-{chosen["id"]}.mp4'
            if not cached.is_file():
                download(chosen["download_url"], cached, opener)
            relative = Path("files") / cached.name
            (output / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cached, output / relative)
            record.update(status="ready", id=chosen["id"], page_url=chosen["page_url"],
                          contributor=chosen["contributor"], duration=chosen["duration"], file=str(relative))
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
                urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            status = f" HTTP {exc.code}" if isinstance(exc, urllib.error.HTTPError) else ""
            record["fallback_reason"] = f"{provider.title()} request failed: {type(exc).__name__}{status}"
        clips.append(record)
    manifest = {"source": provider, "clips": clips}
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
        config = load_config()
        provider = config["provider"]
        api_key = os.environ.get(PROVIDERS[provider]["api_key_env"], "")
        generate(args.episode, api_key, provider=provider, cache_dir=args.cache_dir,
                 cache_hours=config["search_cache_hours"])
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")


if __name__ == "__main__":
    main()
