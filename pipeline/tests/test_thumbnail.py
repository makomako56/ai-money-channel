import struct
import tempfile
import unittest
from pathlib import Path

from pipeline.make_thumbnail import MAX_BYTES, validate_input, verify_png
from pipeline.publish_review import validate_source


class ThumbnailTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        image = self.root / "assets/characters/mirai/transparent/mirai_08_smug.png"
        image.parent.mkdir(parents=True)
        image.write_bytes(b"image")
        sub_image = self.root / "assets/characters/hinata/transparent/hinata_06_surprised.png"
        sub_image.parent.mkdir(parents=True)
        sub_image.write_bytes(b"image")
        font = self.root / "assets/fonts/font.woff2"
        font.parent.mkdir(parents=True)
        font.write_bytes(b"font")
        self.characters = {
            "mirai": {"expressions": {"ドヤ顔": image.name}},
            "hinata": {"expressions": {"驚き": sub_image.name}},
        }
        self.style = {
            "font_file": "assets/fonts/font.woff2",
            "colors": {"background_top": "#050507", "background_bottom": "#320713",
                       "text": "#ffffff", "stroke": "#070509"},
            "layout": {"text_x": 64, "main_y": 160, "sub_y": 574, "text_width": 780,
                       "main_font_max": 108, "main_font_min": 64, "sub_font_size": 44,
                       "character_width": 650, "character_right": -28, "character_bottom": -45,
                       "sub_character_width": 488, "sub_character_right": 370,
                       "sub_character_bottom": -45},
        }
        self.data = {"main_text": "AIが混む裏で\n稼ぐ日本企業", "sub_text": "ディスコって何者？",
                     "character": "mirai", "expression": "ドヤ顔", "accent": "#e5322d"}

    def test_input_validation_and_asset_lookup(self):
        result = validate_input(self.data, self.characters, self.style, self.root)
        self.assertEqual(result["main_lines"], ["AIが混む裏で", "稼ぐ日本企業"])
        self.assertEqual(result["image_url"], "/assets/characters/mirai/transparent/mirai_08_smug.png")
        self.assertIsNone(result["sub_image_url"])
        for changed in ({"accent": "red"}, {"expression": "未定義"},
                        {"main_text": "長" * 11}, {"sub_text": ""}, {"character": "../mirai"},
                        {"character": []}, {"expression": []}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                validate_input({**self.data, **changed}, self.characters, self.style, self.root)
        image = self.root / "assets/characters/mirai/transparent/mirai_08_smug.png"
        image.unlink()
        with self.assertRaisesRegex(ValueError, "素材がありません"):
            validate_input(self.data, self.characters, self.style, self.root)

    def test_optional_second_character(self):
        data = {**self.data, "sub_character": "hinata", "sub_expression": "驚き"}
        result = validate_input(data, self.characters, self.style, self.root)
        self.assertEqual(
            result["sub_image_url"],
            "/assets/characters/hinata/transparent/hinata_06_surprised.png")

    def test_invalid_second_character(self):
        for changed in (
                {"sub_character": "unknown", "sub_expression": "驚き"},
                {"sub_character": "mirai", "sub_expression": "ドヤ顔"},
                {"sub_character": "hinata"}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                validate_input({**self.data, **changed}, self.characters, self.style, self.root)

    def test_review_copy_allows_only_small_thumbnail(self):
        review = self.root / "review"
        review.mkdir()
        image = review / "thumbnail.png"
        image.write_bytes(b"png")
        self.assertEqual(validate_source(review, "ep001_disco", "thumbnail"), review.resolve())
        extra = review / "extra.json"
        extra.write_text("{}")
        with self.assertRaises(ValueError):
            validate_source(review, "ep001_disco", "thumbnail")
        extra.unlink()
        with image.open("ab") as stream:
            stream.truncate(MAX_BYTES)
        with self.assertRaisesRegex(ValueError, "2MB未満"):
            validate_source(review, "ep001_disco", "thumbnail")

    def test_png_dimensions_and_size_limit(self):
        image = self.root / "thumbnail.png"
        header = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR"
        image.write_bytes(header + struct.pack(">II", 1280, 720) + b"padding")
        verify_png(image)
        image.write_bytes(header + struct.pack(">II", 640, 360) + b"padding")
        with self.assertRaisesRegex(ValueError, "1280x720"):
            verify_png(image)
        image.write_bytes(header + struct.pack(">II", 1280, 720) + b"padding")
        with image.open("ab") as stream:
            stream.truncate(MAX_BYTES)
        with self.assertRaisesRegex(ValueError, "2MB未満"):
            verify_png(image)


if __name__ == "__main__":
    unittest.main()
