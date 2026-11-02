import copy
import io
import json
import os
import subprocess
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest.mock import Mock, patch

from pipeline.engine_config import load_engine
from pipeline.aivis_models import download_models
from pipeline.make_voice import SpeechEngine, engine_credit, make_samples, resolve_voice, voice_settings
from pipeline.publish_review import publish, validate_source
from test_make_voice import audio


class VoiceSupplementTests(unittest.TestCase):
    def test_voicevox_query_settings_and_capped_pauses(self):
        query = {"accent_phrases": [{"pause_mora": {"vowel_length": 0.2}},
                                    {"pause_mora": {"vowel_length": 0.4}}, {"pause_mora": None}]}
        client = SpeechEngine("http://localhost", "voicevox")
        client.request = Mock(side_effect=[query, b"audio"])
        client.synthesize("はい", 29, 1.1, -0.02, **voice_settings({}, "ミライ"))
        body = client.request.call_args.kwargs["body"]
        self.assertAlmostEqual(body["accent_phrases"][0]["pause_mora"]["vowel_length"], 0.28)
        self.assertEqual(body["accent_phrases"][1]["pause_mora"]["vowel_length"], 0.5)
        self.assertEqual((body["intonationScale"], body["volumeScale"], body["prePhonemeLength"], body["postPhonemeLength"]), (1.2, 1.0, 0.05, 0.05))

    def test_aivis_preserves_text_and_ignores_mora_lengths(self):
        query = {"kana": "え、そうなんですか！？", "accent_phrases": [{"pause_mora": {"vowel_length": 0.0}}]}
        original = copy.deepcopy(query)
        client = SpeechEngine("http://localhost", "aivisspeech")
        client.request = Mock(side_effect=[query, b"audio"])
        client.synthesize(query["kana"], 1876543210, 1, 0, intonation=1, pause_scale=2)
        call = client.request.call_args
        self.assertEqual(call.kwargs["params"]["speaker"], 1876543210)
        self.assertEqual(call.kwargs["body"]["kana"], original["kana"])
        self.assertEqual(call.kwargs["body"]["accent_phrases"], original["accent_phrases"])

    def test_large_aivis_id_is_resolved_by_name(self):
        catalog = [{"name": "まお", "style": "おちつき", "id": 1876543210}]
        self.assertEqual(resolve_voice({"name": "まお/おちつき"}, catalog, "ミライ", "aivisspeech")["id"], 1876543210)

    def test_defaults_and_invalid_settings(self):
        self.assertEqual(voice_settings({}, "ミライ")["intonation"], 1.2)
        self.assertEqual(voice_settings({}, "ひなた")["intonation"], 1.3)
        for key, value in [("volume", -1), ("pre_phoneme", float("nan")), ("pause_scale", True), ("intonation", 3)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                voice_settings({key: value}, "ミライ")

    def test_engine_switch_changes_image_and_port(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "engine.yaml"
            for engine, image, port in [("voicevox", "voicevox/voicevox_engine:cpu-latest", 50021),
                                        ("aivisspeech", "ghcr.io/aivis-project/aivisspeech-engine:cpu-latest", 10101)]:
                path.write_text(f"engine: {engine}\nengines:\n  {engine}:\n    image: {image}\n    port: {port}\n")
                config = load_engine(path)
                self.assertEqual(config["image"], image)
                self.assertEqual(config["url"], f"http://127.0.0.1:{port}")
            path.write_text("engine: unknown\n")
            with self.assertRaises(ValueError):
                load_engine(path)

    def test_aivishub_extra_models_are_validated(self):
        model = "2ff1c526-27d4-4eeb-b069-4207ae5fe259"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "engine.yaml"
            prefix = ("engine: aivisspeech\nengines:\n  aivisspeech:\n"
                      "    image: ghcr.io/aivis-project/aivisspeech-engine:cpu-latest\n    port: 10101\n")
            path.write_text(prefix + f"    extra_models: [{model}]\n")
            self.assertEqual(load_engine(path)["extra_models"], [model])
            for models in ("[not-a-uuid]", f"[{model}, {model}]", "not-a-list"):
                path.write_text(prefix + f"    extra_models: {models}\n")
                with self.subTest(models=models), self.assertRaises(ValueError):
                    load_engine(path)

    def test_aivishub_download_is_atomic_and_reuses_cache(self):
        model = "2ff1c526-27d4-4eeb-b069-4207ae5fe259"
        with tempfile.TemporaryDirectory() as tmp, patch(
                "pipeline.aivis_models.urllib.request.urlopen", return_value=io.BytesIO(b"aivmx")) as get:
            output = Path(tmp)
            download_models([model], output)
            self.assertEqual((output / f"{model}.aivmx").read_bytes(), b"aivmx")
            self.assertFalse((output / f"{model}.aivmx.part").exists())
            download_models([model], output)
            get.assert_called_once()

    def test_samples_include_every_style_and_unique_filenames(self):
        catalog = [{"name": "声/名", "style": "通常", "id": 1},
                   {"name": "声_名", "style": "通常", "id": 2},
                   {"name": "別の声", "style": "おちつき", "id": 1876543210}]
        client = Mock()
        client.synthesize.return_value = audio()
        with tempfile.TemporaryDirectory() as tmp, patch("pipeline.make_voice.subprocess.run") as ffmpeg:
            make_samples(catalog, client, Path(tmp), 0.35)
            data = json.loads((Path(tmp) / "samples.json").read_text())
            self.assertEqual([v["id"] for v in data["voices"]], [1, 2, 1876543210])
            self.assertEqual(len({v["mp3"] for v in data["voices"]}), 3)
            self.assertTrue(all("/" not in v["mp3"] for v in data["voices"]))
            self.assertEqual(client.synthesize.call_count, 6)
            self.assertEqual(ffmpeg.call_count, 3)

    def test_aivis_credit_includes_all_sample_model_names(self):
        self.assertEqual(engine_credit("aivisspeech", ["まお", "すみれ", "わかな"]),
                         "音声：AivisSpeech（まお・すみれ・わかな）")


class ReviewPublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.remote = self.root / "remote.git"
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / "timeline.json").write_text("[]")
        (self.source / "0001.mp3").write_bytes(b"test fixture")
        self.env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.invalid",
                        GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="test@example.invalid")
        self.git("init", "--bare", "--initial-branch", "main", str(self.remote))
        seed = self.root / "seed"
        self.git("init", "--initial-branch", "main", str(seed))
        (seed / "keep.txt").write_text("main must not change")
        self.git("-C", str(seed), "add", ".")
        self.git("-C", str(seed), "commit", "-m", "seed")
        self.git("-C", str(seed), "push", str(self.remote), "main")
        self.main_sha = self.git("--git-dir", str(self.remote), "rev-parse", "main")

    def git(self, *args):
        return subprocess.run(["git", *args], env=self.env, check=True, capture_output=True, text=True).stdout.strip()

    def test_bootstrap_replace_only_stage_preserve_main_and_other_episode(self):
        publish(self.source, str(self.remote), "ep000_sample", "voice", env=self.env)
        publish(self.source, str(self.remote), "ep001_other", "voice", env=self.env)
        (self.source / "0001.mp3").unlink()
        (self.source / "0002.mp3").write_bytes(b"replacement")
        publish(self.source, str(self.remote), "ep000_sample", "voice", env=self.env)
        files = self.git("--git-dir", str(self.remote), "ls-tree", "-r", "--name-only", "review-outputs").splitlines()
        self.assertIn("ep000_sample/voice/0002.mp3", files)
        self.assertNotIn("ep000_sample/voice/0001.mp3", files)
        self.assertIn("ep001_other/voice/0001.mp3", files)
        self.assertNotIn("keep.txt", files)
        self.assertEqual(self.git("--git-dir", str(self.remote), "rev-parse", "main"), self.main_sha)
        before = self.git("--git-dir", str(self.remote), "rev-parse", "review-outputs")
        publish(self.source, str(self.remote), "ep000_sample", "voice", env=self.env)
        self.assertEqual(self.git("--git-dir", str(self.remote), "rev-parse", "review-outputs"), before)

    def test_reject_bad_path_and_forbidden_payload(self):
        for episode, stage in [("../main", "voice"), ("ep000_sample", "../../main")]:
            with self.assertRaises(ValueError):
                validate_source(self.source, episode, stage)
        forbidden = self.source / ".env"
        forbidden.write_text("fixture")
        with self.assertRaises(ValueError):
            validate_source(self.source, "ep000_sample", "voice")
        forbidden.unlink()
        (self.source / "link.json").symlink_to(self.source / "timeline.json")
        with self.assertRaises(ValueError):
            validate_source(self.source, "ep000_sample", "voice")


if __name__ == "__main__":
    unittest.main()
