import json
from pathlib import Path
import tempfile
import unittest

from pipeline.make_broll import best_file, generate, required_clips


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
            self.assertIn("PEXELS_API_KEY", manifest["clips"][0]["fallback_reason"])
            self.assertTrue((root / "output/ep900_test/broll/broll.json").is_file())


if __name__ == "__main__":
    unittest.main()
