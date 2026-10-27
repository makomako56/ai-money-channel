import io
import json
import tempfile
import unittest
import warnings
import wave
from pathlib import Path
from unittest.mock import Mock

from pipeline.make_voice import inspect_wav, make_voice, register_dictionary, resolve_voice, voice_catalog
from pipeline.script_parser import load_characters

ROOT = Path(__file__).resolve().parents[2]


def audio(frames=2400):
    stream = io.BytesIO()
    with wave.open(stream, "wb") as wav:
        wav.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
        wav.writeframes(b"\x00\x40" * frames)
    return stream.getvalue()


class VoiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.catalog = voice_catalog([
            {"name": "No.7", "styles": [{"name": "ノーマル", "id": 29}]},
            {"name": "春日部つむぎ", "styles": [{"name": "ノーマル", "id": 8}]},
        ])

    def test_voice_id_precedes_name(self):
        self.assertEqual(resolve_voice({"speaker_id": 8, "name": "invalid"}, self.catalog, "ミライ")["id"], 8)

    def test_streaming_talk_is_supported_and_singing_is_excluded(self):
        catalog = voice_catalog([{"name": "No.7", "styles": [
            {"name": "ノーマル", "id": 29, "type": "streaming_talk"},
            {"name": "歌", "id": 3029, "type": "sing"},
        ]}])
        self.assertEqual(len(catalog), 1)
        self.assertEqual(resolve_voice({"speaker_id": 29}, catalog, "ミライ")["id"], 29)

    def test_voice_name(self):
        for name in ("No.7（ノーマル）", "No.7(ノーマル)", "No.7 ノーマル", "No.7/ノーマル"):
            self.assertEqual(resolve_voice({"name": name}, self.catalog, "ミライ")["id"], 29)

    def test_missing_voice_warns_but_invalid_explicit_voice_fails(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self.assertEqual(resolve_voice({}, self.catalog, "ミライ")["id"], 29)
        self.assertEqual(len(caught), 1)
        for config in ({"name": "typo"}, {"speaker_id": 999}, {"speaker_id": True}):
            with self.assertRaises(ValueError):
                resolve_voice(config, self.catalog, "ミライ")

    def test_envelope_including_partial_frame(self):
        duration, envelope = inspect_wav(audio(2401))
        self.assertAlmostEqual(duration, 2401 / 24000)
        self.assertEqual(envelope, [0.5] * 4)
        with self.assertRaises(ValueError):
            inspect_wav(audio(0))

    def test_dictionary_creation_and_registration(self):
        client = Mock()
        dictionary = self.root / "reading_dict.csv"
        register_dictionary(client, dictionary)
        self.assertEqual(dictionary.read_text(), "表記,読み,アクセント位置\n")
        client.request.assert_not_called()
        dictionary.write_text("表記,読み,アクセント位置\nAI,エーアイ,3\n", encoding="utf-8")
        register_dictionary(client, dictionary)
        client.request.assert_called_once_with("/user_dict_word", method="POST", params=dict(surface="AI", pronunciation="エーアイ", accent_type=3))

    def test_invalid_dictionary_fails_before_registration(self):
        client = Mock()
        dictionary = self.root / "reading_dict.csv"
        dictionary.write_text("表記,読み,アクセント位置\nAI,エーアイ,3\n不正,フセイ,x\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "csv:3:"):
            register_dictionary(client, dictionary)
        client.request.assert_not_called()

    def test_timeline_wav_duration_gaps_and_voice_settings(self):
        client = Mock()
        client.synthesize.return_value = audio()
        characters = load_characters(ROOT / "config/characters.yaml")
        lines = [dict(line=i + 1, speaker="ミライ", text="はい", expression="通常", slide=slide)
                 for i, slide in enumerate(["01", "01", "02"])]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            make_voice(lines, characters, self.catalog, client, self.root, (0.25, 0.6))
        timeline = json.loads((self.root / "timeline.json").read_text())
        for actual, expected in zip([item["start"] for item in timeline], [0, 0.35, 1.05]):
            self.assertAlmostEqual(actual, expected)
        self.assertAlmostEqual(timeline[-1]["end"], 1.15)
        self.assertEqual(timeline[0]["envelope"], [0.5] * 3)
        self.assertEqual(len(list(self.root.glob("wav/*.wav"))), 3)
        client.synthesize.assert_called_with("はい", 29, 1.1, -0.02, intonation=1.2, volume=1.0, pre_phoneme=0.05, post_phoneme=0.05, pause_scale=1.4)


if __name__ == "__main__":
    unittest.main()
