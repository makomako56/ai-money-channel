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

    def parse(self, text, check=True):
        self.script.write_text(text, encoding="utf-8")
        return parse_script(self.script, self.characters, check_slides=check)

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

    def test_missing_slide_and_opt_out(self):
        text = '[スライド: 03]\nミライ「はい」'
        with self.assertRaisesRegex(ScriptError, r"script.txt:1:.*03.png"):
            self.parse(text)
        self.assertEqual(self.parse(text, check=False)[0]["slide"], "03")

    def test_invalid_rows_report_source_line(self):
        for invalid in ['先生「はい」', 'ミライ「はい」{納得顔}', 'ミライ「」', 'ミライ「 」',
                        'ミライ「はい」{笑顔}余分', '[スライド: ../1]', '[スライド: 0]',
                        '[スライド: abc]', 'ミライ: はい', 'ミライ「はい」{}', 'ミライ「はい']:
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ScriptError, r"script.txt:2:"):
                self.parse('# comment\n' + invalid)

    def test_null_expression_assets_are_valid(self):
        self.assertEqual(self.parse('ミライ「え！」{驚き}')[0]["expression"], "驚き")

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
