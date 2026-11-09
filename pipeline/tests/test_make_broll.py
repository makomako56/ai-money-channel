import json
import io
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from pipeline.make_broll import (api_candidate_by_id, api_candidates, best_file, best_pixabay_file,
                                 download, generate, load_config, make_candidate_preview, required_clips)


def fake_download(url, target, opener):
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"video")


class BrollTest(unittest.TestCase):
    def test_required_clips_groups_contiguous_lines(self):
        timeline = [
            {"start": 0, "end": 1, "broll_keyword": "phone", "broll_note": "電話"},
            {"start": 1.2, "end": 3, "broll_keyword": "phone", "broll_note": "電話"},
            {"start": 3.2, "end": 4, "screen_kind": "画面"},
        ]
        self.assertEqual(required_clips(timeline)[0]["required_seconds"], 3.0)

    def test_best_file_prefers_landscape_hd_near_1080p(self):
        video = {"video_files": [
            {"file_type": "video/mp4", "quality": "sd", "width": 640, "height": 360, "link": "https://x/sd"},
            {"file_type": "video/mp4", "quality": "hd", "width": 1920, "height": 1080, "link": "https://x/hd"},
            {"file_type": "video/mp4", "quality": "hd", "width": 1080, "height": 1920, "link": "https://x/portrait"},
        ]}
        self.assertEqual(best_file(video)["link"], "https://x/hd")

    def test_pixabay_file_prefers_landscape_hd_near_1080p(self):
        video = {"videos": {
            "small": {"width": 640, "height": 360, "url": "https://x/small"},
            "large": {"width": 1920, "height": 1080, "url": "https://x/large"},
            "portrait": {"width": 1080, "height": 1920, "url": "https://x/portrait"},
        }}
        self.assertEqual(best_pixabay_file(video)["url"], "https://x/large")

    def test_pixabay_search_is_cached_and_keeps_credit_fields(self):
        payload = {"hits": [{
            "id": 42, "duration": 8, "pageURL": "https://pixabay.com/videos/id-42/", "user": "Alice",
            "videos": {"large": {"width": 1920, "height": 1080, "url": "https://cdn/x.mp4"}},
        }]}
        calls = []

        def opener(request, timeout):
            calls.append(request.full_url)
            self.assertEqual(request.get_header("User-agent"), "ai-money-channel/1.0")
            self.assertEqual(request.get_header("Accept"), "application/json")
            return io.BytesIO(json.dumps(payload).encode())

        with tempfile.TemporaryDirectory() as temporary:
            first = api_candidates("phone", "secret", 5, opener=opener,
                                   cache_dir=temporary, now=time.time())
            second = api_candidates("phone", "secret", 5, opener=opener,
                                    cache_dir=temporary, now=time.time())
        self.assertEqual(len(calls), 1)
        self.assertEqual(first, second)
        self.assertEqual(first[0]["page_url"], "https://pixabay.com/videos/id-42/")
        self.assertEqual(first[0]["contributor"], "Alice")

    def test_pixabay_id_lookup_uses_id_parameter(self):
        payload = {"hits": [{
            "id": 99, "duration": 8, "pageURL": "https://pixabay.com/videos/id-99/", "user": "Bob",
            "videos": {"medium": {"width": 1920, "height": 1080,
                                    "url": "https://cdn/99.mp4", "thumbnail": "https://cdn/99.jpg"}},
        }]}

        def opener(request, timeout):
            self.assertIn("id=99", request.full_url)
            return io.BytesIO(json.dumps(payload).encode())

        with tempfile.TemporaryDirectory() as temporary:
            result = api_candidate_by_id(99, "secret", 5, opener=opener, cache_dir=temporary)
        self.assertEqual(result["id"], 99)
        self.assertEqual(result["thumbnail_url"], "https://cdn/99.jpg")

    def test_config_selects_pixabay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "config").mkdir()
            (root / "config/broll.yaml").write_text(
                "provider: pixabay\nsearch_cache_hours: 24\n", encoding="utf-8")
            self.assertEqual(load_config(root)["provider"], "pixabay")

    def test_download_uses_identifiable_user_agent(self):
        def opener(request, timeout):
            self.assertEqual(request.get_header("User-agent"), "ai-money-channel/1.0")
            return io.BytesIO(b"video")

        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "clip.mp4"
            download("https://cdn.example/clip.mp4", target, opener=opener)
            self.assertEqual(target.read_bytes(), b"video")

    def test_candidate_preview_is_320px_jpeg_under_limit(self):
        commands = []

        def runner(command, check):
            commands.append(command)
            Path(command[-1]).write_bytes(b"jpeg")

        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "01-1.jpg"
            make_candidate_preview({"download_url": "https://cdn/video.mp4"}, target, runner=runner)
            self.assertLess(target.stat().st_size, 100_000)
        self.assertIn("scale=320:-2", commands[0])
        self.assertIn("https://cdn/video.mp4", commands[0])

    def test_missing_key_writes_fallback_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            episode = root / "episodes" / "ep900_test"
            voice = root / "output" / "ep900_test" / "voice"
            episode.mkdir(parents=True)
            voice.mkdir(parents=True)
            (episode / "meta.json").write_text('{"video_style":"broll"}', encoding="utf-8")
            timeline = [{"start": 0, "end": 2, "broll_keyword": "phone", "broll_note": "電話"}]
            (voice / "timeline.json").write_text(json.dumps(timeline), encoding="utf-8")
            manifest = generate("ep900_test", "", root=root)
            self.assertEqual(manifest["clips"][0]["status"], "fallback")
            self.assertIn("PIXABAY_API_KEY", manifest["clips"][0]["fallback_reason"])
            self.assertTrue((root / "output/ep900_test/broll/broll.json").is_file())

    def test_generate_does_not_reuse_material_id(self):
        first = self.candidate(1)
        second = self.candidate(2)
        timeline = [
            {"start": 0, "end": 2, "broll_keyword": "phone", "broll_note": "電話"},
            {"start": 2, "end": 4, "broll_keyword": "chat", "broll_note": "チャット"},
        ]
        with self.episode_root(timeline) as root:
            with patch("pipeline.make_broll.api_candidates", side_effect=[[first, second], [second]]) as search, \
                    patch("pipeline.make_broll.make_candidate_preview"), \
                    patch("pipeline.make_broll.download", side_effect=fake_download):
                manifest = generate("ep900_test", "secret", root=root, cache_dir=root / "cache")
            self.assertEqual([clip["id"] for clip in manifest["clips"]], [1, 2])
            self.assertEqual(search.call_args_list[1].kwargs["exclude_ids"], {"1"})

    def test_generate_prefers_requested_id_not_in_search_results(self):
        timeline = [{"start": 0, "end": 2, "broll_keyword": "phone", "broll_note": "電話", "broll_id": 99}]
        with self.episode_root(timeline) as root:
            with patch("pipeline.make_broll.api_candidates", return_value=[self.candidate(1)]), \
                    patch("pipeline.make_broll.api_candidate_by_id", return_value=self.candidate(99)), \
                    patch("pipeline.make_broll.make_candidate_preview"), \
                    patch("pipeline.make_broll.download", side_effect=fake_download):
                manifest = generate("ep900_test", "secret", root=root, cache_dir=root / "cache")
        self.assertEqual(manifest["clips"][0]["id"], 99)
        self.assertEqual(manifest["clips"][0]["candidates"][0]["id"], 99)

    @staticmethod
    def candidate(material_id):
        return {"id": material_id, "duration": 8, "page_url": f"https://pixabay/{material_id}",
                "contributor": "Alice", "width": 1920, "height": 1080,
                "thumbnail_url": f"https://cdn/{material_id}.jpg",
                "download_url": f"https://cdn/{material_id}.mp4"}

    def episode_root(self, timeline):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        episode = root / "episodes" / "ep900_test"
        voice = root / "output" / "ep900_test" / "voice"
        episode.mkdir(parents=True)
        voice.mkdir(parents=True)
        (episode / "meta.json").write_text('{"video_style":"broll"}', encoding="utf-8")
        (voice / "timeline.json").write_text(json.dumps(timeline), encoding="utf-8")
        return _PathContext(root)


class _PathContext:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        return self.path

    def __exit__(self, exc_type, exc_value, traceback):
        return False


if __name__ == "__main__":
    unittest.main()
