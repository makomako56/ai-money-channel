import contextlib
import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from pipeline import upload


NOW = datetime(2026, 10, 27, 0, 0, tzinfo=timezone.utc)


class FakeYouTube:
    token = "not-a-real-token"

    def __init__(self, *, channel="UCexpected", titles=()):
        self.channel = channel
        self.titles = titles
        self.calls = []

    def get_json(self, resource, **params):
        self.calls.append((resource, params))
        if resource == "channels":
            return {"items": [{"id": self.channel, "contentDetails": {"relatedPlaylists": {"uploads": "playlist"}}}]}
        if resource == "playlistItems":
            return {"items": [{"snippet": {"title": title}} for title in self.titles]}
        raise AssertionError("unexpected API call")


class UploadTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "config").mkdir()
        (self.root / "config/channel.yaml").write_text("channel_id: UCexpected\n", encoding="utf-8")
        self.episode = self.root / "episodes/ep000_sample"
        self.episode.mkdir(parents=True)
        (self.episode / "meta.json").write_text(json.dumps({
            "title": "テスト動画", "description": "説明", "tags": ["AI"], "category_id": "27"
        }), encoding="utf-8")
        self.approval = self.episode / "approval.json"
        self.approval.write_text(json.dumps({
            "approved_by": "owner", "approved_at": "2026-10-27T09:00:00+09:00",
            "publish_at": "2026-10-28T18:00:00+09:00"
        }), encoding="utf-8")
        self.video = self.root / "video.mp4"
        self.video.write_bytes(b"test video")
        self.thumbnail = self.root / "thumbnail.png"
        self.thumbnail.write_bytes(b"test image")

    def test_missing_approval_stops_before_api(self):
        self.approval.unlink()
        client = FakeYouTube()
        with self.assertRaisesRegex(upload.UploadError, "approval.json"):
            upload.run(self.root, "ep000_sample", video=self.video,
                       thumbnail=self.thumbnail, youtube=client, now=NOW)
        self.assertEqual(client.calls, [])

    def test_past_publish_time_stops_before_api(self):
        self.approval.write_text(json.dumps({
            "approved_by": "owner", "approved_at": "2026-10-27T09:00:00+09:00",
            "publish_at": "2026-10-26T18:00:00+09:00"
        }), encoding="utf-8")
        client = FakeYouTube()
        with self.assertRaisesRegex(upload.UploadError, "過去"):
            upload.run(self.root, "ep000_sample", video=self.video,
                       thumbnail=self.thumbnail, youtube=client, now=NOW)
        self.assertEqual(client.calls, [])

    def test_wrong_channel_stops_before_upload(self):
        client = FakeYouTube(channel="UCwrong")
        with patch.object(upload, "_video_upload") as insert:
            with self.assertRaisesRegex(upload.UploadError, "チャンネルID"):
                upload.run(self.root, "ep000_sample", video=self.video,
                           thumbnail=self.thumbnail, youtube=client, now=NOW)
            insert.assert_not_called()

    def test_duplicate_title_stops_before_upload(self):
        client = FakeYouTube(titles=["別の動画", "テスト動画"])
        self.assertTrue(upload.already_uploaded(client, "テスト動画"))
        with patch.object(upload, "_video_upload") as insert:
            with self.assertRaisesRegex(upload.UploadError, "二重投稿"):
                upload.run(self.root, "ep000_sample", video=self.video,
                           thumbnail=self.thumbnail, youtube=client, now=NOW)
            insert.assert_not_called()

    def test_dry_run_is_private_utc_and_never_calls_api(self):
        with patch.object(upload, "access_token", side_effect=AssertionError("API called")):
            result = upload.run(self.root, "ep000_sample", dry_run=True, now=NOW)
            self.assertEqual(result["request"]["status"]["privacyStatus"], "private")
            self.assertEqual(result["request"]["status"]["publishAt"], "2026-10-28T09:00:00Z")
            self.assertIs(result["request"]["status"]["selfDeclaredMadeForKids"], False)
            self.assertIs(result["request"]["status"]["containsSyntheticMedia"], True)

    def test_check_only_authenticates_and_checks_channel(self):
        self.approval.unlink()
        client = FakeYouTube()
        self.assertEqual(upload.run(self.root, "ep000_sample", upload_check=True, youtube=client),
                         {"channel_id": "UCexpected", "status": "ok"})
        self.assertEqual([name for name, _ in client.calls], ["channels"])

    def test_missing_secrets_names_only(self):
        with self.assertRaisesRegex(upload.UploadError, "YT_CLIENT_ID") as context:
            upload.access_token({})
        self.assertNotIn("not-a-real-token", str(context.exception))

    def test_cli_dry_run_output(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = upload.main(["--root", str(self.root), "--episode", "ep000_sample", "--dry-run"])
        self.assertEqual(code, 0)
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["request"]["status"]["privacyStatus"], "private")
        self.assertTrue(result["request"]["status"]["publishAt"].endswith("Z"))


if __name__ == "__main__":
    unittest.main()
