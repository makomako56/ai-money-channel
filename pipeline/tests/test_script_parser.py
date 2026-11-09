import tempfile
import unittest
import warnings
from pathlib import Path

from pipeline.script_parser import ScriptError, load_characters, parse_script

ROOT = Path(__file__).resolve().parents[2]


class ScriptParserTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.script = Path(self.temp.name) / "script.txt"
        self.characters = load_characters(ROOT / "config/characters.yaml")

    def parse(self, text, check=True, video_style=None):
        self.script.write_text(text, encoding="utf-8")
        return parse_script(self.script, self.characters, check_slides=check, video_style=video_style)

    def test_dialogue_defaults_and_nested_quotes(self):
        lines = self.parse('ミライ「「AI」の話です」\nひなた「はい！」{笑顔}')
        self.assertEqual(lines[0], dict(line=1, speaker="ミライ", text="「AI」の話です", expression="通常", slide=None))
        self.assertEqual(lines[1]["expression"], "笑顔")

    def test_slide_inheritance_switch_and_line_numbers(self):
        slides = self.script.parent / "slides"
        slides.mkdir()
        for number in ("01", "03"):
            (slides / f"{number}.png").touch()
        lines = self.parse('# comment\n\n[スライド: 1]\nミライ「一」\nひなた「二」\n[スライド: 03]\nミライ「三」')
        self.assertEqual([line["slide"] for line in lines], ["01", "01", "03"])
        self.assertEqual([line["line"] for line in lines], [4, 5, 7])

    def test_v2_screen_display_and_motion(self):
        pages = self.script.parent / "pages"
        pages.mkdir()
        (pages / "01.html").touch()
        lines = self.parse('[画面: 1]\n[表示]\nミライ「はい」{通常|ぴょん}\n'
                           'ひなた「うん」{通常|うんうん}')
        self.assertEqual([line["slide"] for line in lines], ["01", "01"])
        self.assertEqual([line["line"] for line in lines], [3, 4])
        self.assertEqual([line["expression"] for line in lines], ["通常", "通常"])
        for motion in ("ぴょん", "びくっ", "うんうん", "かしげ", "ずいっ", "しょんぼり"):
            with self.subTest(motion=motion):
                self.assertEqual(self.parse(f'ミライ「はい」{{通常|{motion}}}')[0]["expression"], "通常")
        with self.assertRaisesRegex(ScriptError, "未定義の動き"):
            self.parse('ミライ「はい」{通常|回転}')
        with self.assertRaisesRegex(ScriptError, r"pages/03.html"):
            self.parse('[画面: 03]\nミライ「はい」')
        self.assertEqual(self.parse('[画面: 03]\nミライ「はい」', check=False)[0]["slide"], "03")

    def test_missing_slide_and_opt_out(self):
        text = '[スライド: 03]\nミライ「はい」'
        with self.assertRaisesRegex(ScriptError, r"script.txt:1:.*03.png"):
            self.parse(text)
        self.assertEqual(self.parse(text, check=False)[0]["slide"], "03")

    def test_invalid_rows_report_source_line(self):
        for invalid in ['先生「はい」', 'ミライ「はい」{未定義}', 'ミライ「」', 'ミライ「 」',
                        'ミライ「はい」{笑顔}余分', '[スライド: ../1]', '[スライド: 0]',
                        '[スライド: abc]', 'ミライ: はい', 'ミライ「はい」{}', 'ミライ「はい']:
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ScriptError, r"script.txt:2:"):
                self.parse('# comment\n' + invalid)

    def test_null_expression_assets_are_valid(self):
        self.characters["ミライ"]["expressions"]["驚き"] = None
        self.assertEqual(self.parse('ミライ「え！」{驚き}')[0]["expression"], "驚き")

    def test_whiteboard_tags_and_spotlight_are_opt_in(self):
        text = ('[手書き: 見出し]\n[絵: 📞 | 電話がつながらない]\n'
                'ミライ「【AIが問い合わせに】／答えます」\n[消す]\n'
                '[絵: 🤖 | AIの窓口]\nひなた「本当？」')
        lines = self.parse(text, video_style="whiteboard")
        self.assertEqual(lines[0]["text"], "AIが問い合わせに／答えます")
        self.assertEqual(lines[0]["display_text"], "【AIが問い合わせに】／答えます")
        self.assertEqual(lines[1]["text"], "本当？")
        with self.assertRaisesRegex(ScriptError, "形式が不正"):
            self.parse(text)

    def test_whiteboard_rejects_more_than_six_pictures_and_bad_brackets(self):
        pictures = "\n".join(f"[絵: {i} | 説明{i}]" for i in range(7))
        with self.assertRaisesRegex(ScriptError, "6つまで"):
            self.parse(pictures + '\nミライ「はい」', video_style="whiteboard")
        with self.assertRaisesRegex(ScriptError, "【】"):
            self.parse('ミライ「【閉じない」', video_style="whiteboard")

    def test_long_dialogue_warns_without_truncation(self):
        for length in (40, 41):
            text = "あ" * length
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                result = self.parse(f'ミライ「{text}」')
            self.assertEqual(result[0]["text"], text)
            self.assertEqual(len(caught), int(length > 40))
            if caught:
                self.assertIn("script.txt:1:", str(caught[0].message))

    def test_bom_crlf_comments(self):
        lines = self.parse('\ufeff # コメント\r\n\r\n  ミライ「はい」  \r\n')
        self.assertEqual(lines[0]["line"], 3)

    def test_empty_script_fails(self):
        with self.assertRaisesRegex(ScriptError, r"script.txt:1:"):
            self.parse('# comment\n')

    def test_sample_script_unchanged(self):
        lines = parse_script(ROOT / "episodes/ep000_sample/script.txt", self.characters, check_slides=False)
        self.assertEqual(len(lines), 8)
        self.assertEqual([line["slide"] for line in lines], ["01"] * 3 + ["02"] * 3 + ["03"] * 2)


if __name__ == "__main__":
    unittest.main()
