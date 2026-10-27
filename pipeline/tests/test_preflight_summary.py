import contextlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from pipeline import preflight, summary

ROOT = Path(__file__).resolve().parents[2]


class PreflightTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "config", self.root / "config")
        shutil.copytree(ROOT / "assets" / "fonts", self.root / "assets" / "fonts")
        shutil.copytree(ROOT / "assets" / "characters", self.root / "assets" / "characters")
        shutil.copytree(ROOT / "episodes" / "ep000_sample", self.root / "episodes" / "ep000_sample")
        self.episode = self.root / "episodes" / "ep000_sample"

    def tearDown(self):
        self.temp.cleanup()

    def run_all(self):
        return preflight.run("ep000_sample", "all", root=self.root)

    def test_sample_passes(self):
        lines, screens, warnings = self.run_all()
        self.assertEqual((lines, screens, warnings), (8, 3, []))

    def test_missing_slide_stops(self):
        (self.episode / "slides" / "02.png").unlink()
        with self.assertRaisesRegex(preflight.PreflightError, "slides/02.png"):
            self.run_all()

    def test_meta_required_fields_and_limits(self):
        meta = json.loads((self.episode / "meta.json").read_text(encoding="utf-8"))
        for broken in ({**meta, "title": ""}, {**meta, "title": "あ" * 101}, {**meta, "category_id": 27},
                       {**meta, "description": "<b>"}, {k: v for k, v in meta.items() if k != "tags"}):
            with self.subTest(broken=str(broken)[:40]):
                (self.episode / "meta.json").write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
                with self.assertRaisesRegex(preflight.PreflightError, "meta.json"):
                    self.run_all()

    def test_meta_only_needed_for_all(self):
        (self.episode / "meta.json").unlink()
        self.assertEqual(preflight.run("ep000_sample", "video", root=self.root)[0], 8)
        with self.assertRaises(preflight.PreflightError):
            self.run_all()

    def test_bad_thumbnail_stops(self):
        (self.episode / "thumbnail.json").write_text('{"main_text": "x"}', encoding="utf-8")
        with self.assertRaisesRegex(preflight.PreflightError, "thumbnail.json"):
            preflight.run("ep000_sample", "thumbnail", root=self.root)

    def test_cli_exit_code(self):
        # stdout を捨てる（::error:: がテスト中に Actions の注記にならないように）
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(preflight.main(["--episode", "../x", "--stage", "all"]), 2)
        self.assertIn("入力チェックで停止", out.getvalue())


class SummaryTest(unittest.TestCase):
    def test_reports_failed_stage_and_warnings(self):
        with tempfile.TemporaryDirectory() as temporary:
            text, failed = summary.build("ep000_sample", {"preflight": "success", "video": "failure",
                                                          "thumbnail": "skipped"}, ["注意1"], root=Path(temporary))
        self.assertTrue(failed)
        self.assertIn("動画 で失敗", text)
        self.assertIn("| サムネ | － 実行なし |", text)
        self.assertIn("- 注意1", text)

    def test_length_warning(self):
        self.assertIsNone(summary.length_warning(600))
        self.assertIn("0.5分", summary.length_warning(30))
        self.assertIsNone(summary.length_warning(None))


if __name__ == "__main__":
    unittest.main()
