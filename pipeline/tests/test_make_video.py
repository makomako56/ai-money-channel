import json
from pathlib import Path
import tempfile
import unittest
import wave

from pipeline import make_video
from pipeline.publish_review import validate_source


def write_wav(path, seconds):
    with wave.open(str(path), "wb") as output:
        output.setparams((1, 2, make_video.RATE, 0, "NONE", "not compressed"))
        output.writeframes(b"\1\0" * round(seconds * make_video.RATE))


class BuildAudioTest(unittest.TestCase):
    def test_places_lines_at_timeline_start_and_adds_credit(self):
        with tempfile.TemporaryDirectory() as temporary:
            voice = Path(temporary)
            write_wav(voice / "001.wav", 0.5)
            write_wav(voice / "002.wav", 0.25)
            timeline = [dict(line=1, start=0.0, end=0.5, wav="001.wav"),
                        dict(line=2, start=1.0, end=1.25, wav="002.wav")]
            (voice / "timeline.json").write_text(json.dumps(timeline), encoding="utf-8")
            duration = make_video.build_audio(voice / "timeline.json", voice, voice / "out.wav")
            self.assertAlmostEqual(duration, 1.25 + make_video.CREDIT_SECONDS)
            with wave.open(str(voice / "out.wav")) as result:
                self.assertEqual(result.getnframes(), round(duration * make_video.RATE))
                pcm = result.readframes(result.getnframes())
            second = round(1.0 * make_video.RATE) * 2
            self.assertEqual(pcm[second - 2:second + 2], b"\0\0\1\0")

    def test_rejects_path_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            voice = Path(temporary)
            (voice / "timeline.json").write_text(json.dumps([dict(start=0, end=1, wav="../x.wav")]), encoding="utf-8")
            with self.assertRaises(ValueError):
                make_video.build_audio(voice / "timeline.json", voice, voice / "out.wav")


class FrameTimesTest(unittest.TestCase):
    def test_settles_after_switch_but_before_next(self):
        events = [dict(screen="01", step=1, t=0.1), dict(screen="01", step=2, t=0.5),
                  dict(screen="02", step=1, t=5.0)]
        self.assertEqual(make_video.frame_times(events, 10.0),
                         [("01-1.png", 0.3), ("01-2.png", 1.2), ("02-1.png", 5.7)])

    def test_rejects_unsafe_names(self):
        with self.assertRaises(ValueError):
            make_video.frame_times([dict(screen="../x", step=1, t=0)], 5.0)


class EncodeTest(unittest.TestCase):
    def test_bgm_is_optional_and_quiet(self):
        with tempfile.TemporaryDirectory() as temporary:
            self.assertIsNone(make_video.find_bgm(Path(temporary)))
            (Path(temporary) / "bgm.mp3").touch()
            self.assertEqual(make_video.find_bgm(Path(temporary)).name, "bgm.mp3")
        plain = make_video.encode_command("v.webm", "a.wav", 0.5, 10, "o.mp4", "r.mp4")
        mixed = make_video.encode_command("v.webm", "a.wav", 0.5, 10, "o.mp4", "r.mp4", bgm="bgm.mp3")
        self.assertNotIn("amix", " ".join(plain))
        self.assertIn("volume=-24dB", " ".join(mixed))
        self.assertEqual(plain[-1], "r.mp4")
        self.assertIn("o.mp4", plain)


class PublishVideoTest(unittest.TestCase):
    def test_video_accepts_small_broll_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            (source / "video.mp4").write_bytes(b"x")
            (source / "frames").mkdir()
            (source / "frames" / "01-2.png").write_bytes(b"x")
            (source / "broll.json").write_text(json.dumps({"provider": "pixabay"}), encoding="utf-8")
            (source / "broll_candidates").mkdir()
            (source / "broll_candidates" / "01-1.jpg").write_bytes(b"x")
            (source / "broll_candidates" / "01-2.jpg").write_bytes(b"x")
            validate_source(source, "ep001_disco", "video")

    def test_video_rejects_invalid_broll_candidate_name(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            (source / "video.mp4").write_bytes(b"x")
            (source / "broll_candidates").mkdir()
            (source / "broll_candidates" / "notes.jpg").write_bytes(b"x")
            with self.assertRaises(ValueError):
                validate_source(source, "ep001_disco", "video")

    def test_video_rejects_other_extra_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            (source / "video.mp4").write_bytes(b"x")
            (source / "frames").mkdir()
            (source / "frames" / "01-2.png").write_bytes(b"x")
            (source / "frames" / "notes.txt").write_text("x")
            with self.assertRaises(ValueError):
                validate_source(source, "ep001_disco", "video")


if __name__ == "__main__":
    unittest.main()
