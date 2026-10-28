"""Upload an owner-approved episode as a private, scheduled YouTube video."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOKEN_URL = "https://oauth2.googleapis.com/token"
API_URL = "https://www.googleapis.com/youtube/v3"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
SCOPES = "https://www.googleapis.com/auth/youtube https://www.googleapis.com/auth/youtube.upload"
CHUNK_SIZE = 8 * 1024 * 1024


class UploadError(Exception):
    """An actionable upload failure without credential contents."""


def _json_file(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise UploadError(f"必須ファイルがありません: {path.name}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise UploadError(f"JSONを読めません: {path.name}") from exc
    if not isinstance(value, dict):
        raise UploadError(f"JSONはオブジェクトにしてください: {path.name}")
    return value


def load_channel_id(root: Path) -> str:
    try:
        text = (root / "config/channel.yaml").read_text(encoding="utf-8")
    except OSError as exc:
        raise UploadError("config/channel.yamlを読めません") from exc
    match = re.search(r"^channel_id:\s*['\"]?(UC[A-Za-z0-9_-]+)['\"]?\s*$", text, re.MULTILINE)
    if not match:
        raise UploadError("config/channel.yamlのchannel_idが不正です")
    return match.group(1)


def build_body(root: Path, episode: str, *, now: datetime | None = None) -> dict:
    if not re.fullmatch(r"ep[0-9]+_[A-Za-z0-9_-]+", episode):
        raise UploadError("episode名が不正です")
    folder = root / "episodes" / episode
    approval = _json_file(folder / "approval.json")
    if approval.get("approved_by") != "owner" or not isinstance(approval.get("approved_at"), str):
        raise UploadError("approval.jsonにオーナーの承認がありません")
    try:
        approved_at = datetime.fromisoformat(approval["approved_at"])
        publish_at = datetime.fromisoformat(approval["publish_at"])
    except (KeyError, TypeError, ValueError) as exc:
        raise UploadError("approval.jsonの日時が不正です") from exc
    if approved_at.tzinfo is None or publish_at.tzinfo is None:
        raise UploadError("approval.jsonの日時にはタイムゾーンが必要です")
    now = now or datetime.now(timezone.utc)
    if publish_at <= now:
        raise UploadError("publish_atが過去です")
    meta = _json_file(folder / "meta.json")
    title, description, tags, category = (meta.get(key) for key in ("title", "description", "tags", "category_id"))
    if not isinstance(title, str) or not title.strip() or len(title) > 100:
        raise UploadError("meta.jsonのtitleが不正です")
    if not isinstance(description, str) or not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        raise UploadError("meta.jsonのdescriptionまたはtagsが不正です")
    if not isinstance(category, str) or not category.isdigit():
        raise UploadError("meta.jsonのcategory_idが不正です")
    return {
        "snippet": {"title": title, "description": description, "tags": tags, "categoryId": category},
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True,
        },
    }


def _request(url: str, *, method: str = "GET", token: str | None = None, data: bytes | None = None,
             headers: dict | None = None) -> tuple[bytes, object]:
    headers = dict(headers or {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read(), response.headers
    except urllib.error.HTTPError as exc:
        # Never show server bodies: OAuth errors may include credential details.
        if exc.code == 400 and url == TOKEN_URL:
            raise UploadError("YouTubeの鍵の更新が必要（docs/YouTube_API準備.md の手順5）") from None
        raise UploadError(f"YouTube APIがHTTP {exc.code}を返しました") from None
    except urllib.error.URLError as exc:
        raise UploadError("YouTube APIに接続できません") from exc


def access_token(env: dict) -> str:
    names = ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")
    missing = [name for name in names if not env.get(name)]
    if missing:
        raise UploadError("GitHub Secretsがありません: " + ", ".join(missing))
    payload = urllib.parse.urlencode({"client_id": env[names[0]], "client_secret": env[names[1]],
                                      "refresh_token": env[names[2]], "grant_type": "refresh_token"}).encode()
    raw, _ = _request(TOKEN_URL, method="POST", data=payload,
                      headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        token = json.loads(raw)["access_token"]
    except (ValueError, KeyError, TypeError) as exc:
        raise UploadError("YouTubeの認証応答が不正です") from exc
    return token


class YouTube:
    def __init__(self, token: str):
        self.token = token

    def get_json(self, resource: str, **params) -> dict:
        url = f"{API_URL}/{resource}?{urllib.parse.urlencode(params)}"
        raw, _ = _request(url, token=self.token)
        try:
            return json.loads(raw)
        except ValueError as exc:
            raise UploadError("YouTube APIの応答が不正です") from exc


def check_channel(youtube: YouTube, expected_id: str) -> str:
    data = youtube.get_json("channels", part="id,contentDetails", mine="true")
    items = data.get("items", [])
    if len(items) != 1 or items[0].get("id") != expected_id:
        raise UploadError("認証したYouTubeチャンネルIDがconfig/channel.yamlと一致しません")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def already_uploaded(youtube: YouTube, title: str) -> bool:
    """Check all uploads on the authenticated channel, including private videos."""
    data = youtube.get_json("channels", part="contentDetails", mine="true")
    items = data.get("items", [])
    if len(items) != 1:
        raise UploadError("認証したチャンネルを確認できません")
    playlist = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    page_token = None
    while True:
        params = {"part": "snippet", "playlistId": playlist, "maxResults": 50}
        if page_token:
            params["pageToken"] = page_token
        page = youtube.get_json("playlistItems", **params)
        if any(item.get("snippet", {}).get("title") == title for item in page.get("items", [])):
            return True
        page_token = page.get("nextPageToken")
        if not page_token:
            return False


def _video_upload(youtube: YouTube, body: dict, video: Path) -> str:
    size = video.stat().st_size
    if size == 0:
        raise UploadError("動画ファイルが空です")
    url = f"{UPLOAD_URL}?{urllib.parse.urlencode({'uploadType': 'resumable', 'part': 'snippet,status'})}"
    _, response_headers = _request(url, method="POST", token=youtube.token,
                                   data=json.dumps(body, ensure_ascii=False).encode(),
                                   headers={"Content-Type": "application/json; charset=UTF-8",
                                            "X-Upload-Content-Type": "video/mp4",
                                            "X-Upload-Content-Length": str(size)})
    location = response_headers.get("Location")
    if not location or not location.startswith("https://www.googleapis.com/"):
        raise UploadError("YouTubeのアップロードURLが不正です")
    offset = 0
    with video.open("rb") as stream:
        while offset < size:
            chunk = stream.read(CHUNK_SIZE)
            end = offset + len(chunk) - 1
            request = urllib.request.Request(location, data=chunk, method="PUT", headers={
                "Authorization": f"Bearer {youtube.token}", "Content-Type": "video/mp4", "Content-Length": str(len(chunk)),
                "Content-Range": f"bytes {offset}-{end}/{size}"})
            try:
                with urllib.request.urlopen(request, timeout=180) as response:
                    raw = response.read()
            except urllib.error.HTTPError as exc:
                if exc.code == 308 and end + 1 < size:
                    confirmed = exc.headers.get("Range", "")
                    match = re.fullmatch(r"bytes=0-([0-9]+)", confirmed)
                    offset = int(match.group(1)) + 1 if match else 0
                    stream.seek(offset)
                    continue
                raise UploadError(f"YouTube動画アップロードがHTTP {exc.code}で失敗しました") from None
            except urllib.error.URLError as exc:
                raise UploadError("YouTube動画アップロードに接続できません") from exc
            offset = end + 1
    try:
        video_id = json.loads(raw)["id"]
    except (ValueError, KeyError, TypeError) as exc:
        raise UploadError("動画IDがYouTubeから返されませんでした") from exc
    return video_id


def _set_thumbnail(youtube: YouTube, video_id: str, image: Path) -> None:
    raw = image.read_bytes()
    if not raw or len(raw) >= 2_000_000:
        raise UploadError("サムネ画像は2MB未満である必要があります")
    url = f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?{urllib.parse.urlencode({'videoId': video_id, 'uploadType': 'media'})}"
    _request(url, method="POST", token=youtube.token, data=raw, headers={"Content-Type": "image/png"})


def run(root: Path, episode: str, *, dry_run: bool = False, upload_check: bool = False,
        video: Path | None = None, thumbnail: Path | None = None, env: dict | None = None,
        youtube: YouTube | None = None, now: datetime | None = None) -> dict:
    expected_channel = load_channel_id(root)
    if upload_check:
        client = youtube or YouTube(access_token(dict(os.environ if env is None else env)))
        check_channel(client, expected_channel)
        return {"channel_id": expected_channel, "status": "ok"}
    body = build_body(root, episode, now=now)
    if dry_run:
        return {"channel_id": expected_channel, "request": body}
    if video is None or thumbnail is None or not video.is_file() or not thumbnail.is_file():
        raise UploadError("動画とサムネのartifactが必要です")
    client = youtube or YouTube(access_token(dict(os.environ if env is None else env)))
    check_channel(client, expected_channel)
    if already_uploaded(client, body["snippet"]["title"]):
        raise UploadError("同じタイトルの動画が既にYouTubeにあります。二重投稿を中止します")
    video_id = _video_upload(client, body, video)
    _set_thumbnail(client, video_id, thumbnail)
    result = {"video_id": video_id, "url": f"https://www.youtube.com/watch?v={video_id}"}
    target = root / "output" / episode / "upload" / "upload_result.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--video", type=Path)
    parser.add_argument("--thumbnail", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = run(args.root, args.episode, dry_run=args.dry_run, upload_check=args.check,
                     video=args.video, thumbnail=args.thumbnail)
    except (UploadError, OSError, KeyError, TypeError) as exc:
        # Do not print raw exceptions from network clients or credential values.
        print(f"エラー: {exc if isinstance(exc, UploadError) else 'アップロード処理に失敗しました'}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
