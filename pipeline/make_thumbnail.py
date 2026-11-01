"""Render a 1280x720 episode thumbnail from thumbnail.json with Playwright."""
import argparse
import json
import re
import struct
import subprocess
import tempfile
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import yaml

ROOT = Path(__file__).resolve().parent.parent
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 2_000_000
WIDTH, HEIGHT = 1280, 720
REQUIRED_FIELDS = {"main_text", "sub_text", "character", "expression", "accent"}
OPTIONAL_FIELDS = {"sub_character", "sub_expression"}
COLOR = re.compile(r"#[0-9a-fA-F]{6}\Z")
EPISODE = re.compile(r"ep[0-9]+_[\w-]+\Z")


def asset_url(root, relative):
    if not isinstance(relative, str):
        raise ValueError("素材のファイル名が不正です")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"素材のパスが不正です: {relative}")
    absolute = (root / path).resolve()
    if not absolute.is_relative_to(root.resolve()) or not absolute.is_file():
        raise ValueError(f"素材がありません: {relative}")
    return "/" + path.as_posix()


def validate_input(data, characters, style, root=ROOT):
    if (not isinstance(data, dict) or not REQUIRED_FIELDS.issubset(data) or
            not set(data).issubset(REQUIRED_FIELDS | OPTIONAL_FIELDS)):
        raise ValueError("thumbnail.json には main_text、sub_text、character、expression、accent が必要です")
    if ("sub_character" in data) != ("sub_expression" in data):
        raise ValueError("sub_character と sub_expression は両方指定してください")
    main = data["main_text"]
    if not isinstance(main, str) or "\r" in main:
        raise ValueError("main_text は1〜2行の文字列が必要です")
    lines = main.split("\n")
    if not 1 <= len(lines) <= 2 or any(not 1 <= len(line.strip()) <= 10 or line != line.strip() for line in lines):
        raise ValueError("main_text は1〜2行、各行1〜10文字で指定してください")
    sub = data["sub_text"]
    if not isinstance(sub, str) or not 1 <= len(sub) <= 18 or sub != sub.strip() or "\n" in sub:
        raise ValueError("sub_text は1〜18文字の1行で指定してください")
    accent = data["accent"]
    if not isinstance(accent, str) or not COLOR.fullmatch(accent):
        raise ValueError("accent は #RRGGBB 形式が必要です")
    character = data["character"]
    if not isinstance(character, str) or character not in ("mirai", "hinata") or character not in characters:
        raise ValueError(f"未定義のキャラです: {character}")
    expression = data["expression"]
    images = characters[character].get("expressions", {})
    if not isinstance(expression, str) or expression not in images or not isinstance(images[expression], str):
        raise ValueError(f"未定義の表情または画像です: {expression}")
    image_name = images[expression]
    if Path(image_name).name != image_name or not image_name.endswith(".png"):
        raise ValueError("キャラ画像名が不正です")
    image_url = asset_url(root, f"assets/characters/{character}/transparent/{image_name}")
    sub_image_url = None
    if "sub_character" in data:
        sub_character = data["sub_character"]
        if (not isinstance(sub_character, str) or sub_character not in ("mirai", "hinata") or
                sub_character not in characters or sub_character == character):
            raise ValueError(f"未定義またはメインと同じサブキャラです: {sub_character}")
        sub_expression = data["sub_expression"]
        sub_images = characters[sub_character].get("expressions", {})
        if (not isinstance(sub_expression, str) or sub_expression not in sub_images or
                not isinstance(sub_images[sub_expression], str)):
            raise ValueError(f"未定義のサブキャラ表情または画像です: {sub_expression}")
        sub_image_name = sub_images[sub_expression]
        if Path(sub_image_name).name != sub_image_name or not sub_image_name.endswith(".png"):
            raise ValueError("サブキャラ画像名が不正です")
        sub_image_url = asset_url(
            root, f"assets/characters/{sub_character}/transparent/{sub_image_name}")
    if not isinstance(style, dict) or not isinstance(style.get("font_file"), str):
        raise ValueError("thumbnail_style.yaml の font_file が必要です")
    font_url = asset_url(root, style["font_file"])
    if not font_url.endswith(".woff2"):
        raise ValueError("サムネのフォントは woff2 が必要です")
    colors, layout = style.get("colors"), style.get("layout")
    color_keys = ("background_top", "background_bottom", "text", "stroke")
    layout_keys = ("text_x", "main_y", "sub_y", "text_width", "main_font_max",
                   "main_font_min", "sub_font_size", "character_width",
                   "character_right", "character_bottom", "sub_character_width",
                   "sub_character_right", "sub_character_bottom")
    if not isinstance(colors, dict) or any(not isinstance(colors.get(key), str) or
                                            not COLOR.fullmatch(colors[key]) for key in color_keys):
        raise ValueError("thumbnail_style.yaml の colors が不正です")
    if not isinstance(layout, dict) or any(type(layout.get(key)) is not int or
                                            abs(layout[key]) > 2000 for key in layout_keys):
        raise ValueError("thumbnail_style.yaml の layout が不正です")
    if not 1 <= layout["main_font_min"] <= layout["main_font_max"] or not 1 <= layout["sub_font_size"]:
        raise ValueError("thumbnail_style.yaml の文字サイズが不正です")
    if (not 1 <= layout["text_width"] <= WIDTH or
            not 1 <= layout["character_width"] <= WIDTH or
            not 1 <= layout["sub_character_width"] <= WIDTH):
        raise ValueError("thumbnail_style.yaml の幅が不正です")
    return {"main_lines": lines, "sub_text": sub, "accent": accent,
            "image_url": image_url, "sub_image_url": sub_image_url, "font_url": font_url,
            "colors": {key: colors[key] for key in color_keys},
            "layout": {key: layout[key] for key in layout_keys}}


def verify_png(path):
    path = Path(path)
    size = path.stat().st_size
    if not 24 <= size < MAX_BYTES:
        raise ValueError(f"サムネ画像は2MB未満が必要です（{size} bytes）")
    with path.open("rb") as stream:
        header = stream.read(24)
    if header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        raise ValueError("サムネ画像がPNGではありません")
    width, height = struct.unpack(">II", header[16:24])
    if (width, height) != (WIDTH, HEIGHT):
        raise ValueError(f"サムネ画像は1280x720が必要です（{width}x{height}）")


NODE_SCRIPT = r"""
const fs = require("fs");
const { chromium } = require("playwright");
(async () => {
  const [port, output] = process.argv.slice(1);
  const payload = JSON.parse(fs.readFileSync(0, "utf8"));
  const browser = await chromium.launch({headless:true});
  try {
    const context = await browser.newContext({viewport:{width:1280,height:720},deviceScaleFactor:1});
    const page = await context.newPage();
    await page.goto("http://127.0.0.1:" + port + "/pipeline/stage/thumbnail.html", {waitUntil:"load"});
    await page.evaluate(async data => { await window.renderThumbnail(data); }, payload);
    await page.screenshot({path:output,type:"png",animations:"disabled"});
    await context.close();
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error.stack || error); process.exit(1); });
"""


def render(payload, output):
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, *_):
            pass

    handler = partial(QuietHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = subprocess.run(
            ["node", "-e", NODE_SCRIPT, str(server.server_address[1]), str(output)],
            input=json.dumps(payload, ensure_ascii=False), capture_output=True, text=True,
            cwd=ROOT, timeout=120)
        if result.returncode:
            raise RuntimeError("Playwrightのサムネ撮影に失敗: " + result.stderr[-2000:])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True)
    args = parser.parse_args()
    if not EPISODE.fullmatch(args.episode):
        parser.error("episode の形式が不正です")
    episode = ROOT / "episodes" / args.episode
    output = ROOT / "output" / args.episode / "thumbnail"
    try:
        if episode.is_symlink() or not episode.is_dir():
            raise ValueError(f"エピソードがありません: {args.episode}")
        if output.exists():
            raise ValueError(f"出力先が既にあります: {output}")
        data = json.loads((episode / "thumbnail.json").read_text(encoding="utf-8"))
        characters = yaml.safe_load((ROOT / "config/characters.yaml").read_text(encoding="utf-8"))
        style = yaml.safe_load((ROOT / "config/thumbnail_style.yaml").read_text(encoding="utf-8"))
        payload = validate_input(data, characters, style)
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output.parent, prefix=".thumbnail-") as temporary:
            staging = Path(temporary) / "thumbnail"
            staging.mkdir()
            image = staging / "thumbnail.png"
            render(payload, image)
            verify_png(image)
            staging.rename(output)
        print(f"サムネ完成: {output / 'thumbnail.png'}")
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, subprocess.TimeoutExpired,
            json.JSONDecodeError, yaml.YAMLError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")


if __name__ == "__main__":
    main()
