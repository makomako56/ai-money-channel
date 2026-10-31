import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from pipeline import upload_result_store
from pipeline.publish_review import publish


class UploadResultStoreTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.remote = self.root / "remote.git"
        subprocess.run(["git", "init", "--bare", str(self.remote)], check=True,
                       capture_output=True, text=True)
        self.destination = self.root / "restored/upload_result.json"

    def test_missing_result_is_allowed(self):
        self.assertFalse(upload_result_store.fetch(str(self.remote), "ep000_sample", self.destination))
        self.assertFalse(self.destination.exists())

    def test_published_result_is_restored_with_video_id(self):
        source = self.root / "source"
        source.mkdir()
        expected = {"video_id": "video-123", "url": "https://example.invalid/video-123"}
        (source / "upload_result.json").write_text(json.dumps(expected), encoding="utf-8")
        publish(source, str(self.remote), "ep000_sample", "upload")

        self.assertTrue(upload_result_store.fetch(str(self.remote), "ep000_sample", self.destination))
        self.assertEqual(json.loads(self.destination.read_text(encoding="utf-8")), expected)

    def test_transport_failure_stops_instead_of_treating_result_as_missing(self):
        missing_remote = self.root / "does-not-exist.git"
        with self.assertRaisesRegex(upload_result_store.ResultStoreError, "確認できない"):
            upload_result_store.fetch(str(missing_remote), "ep000_sample", self.destination)
        self.assertFalse(self.destination.exists())


if __name__ == "__main__":
    unittest.main()
