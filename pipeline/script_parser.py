"""Parse the production script without changing dialogue text."""
import argparse
import json
import re
import warnings
from pathlib import Path

import yaml


MOTIONS = {"ぴょん", "びくっ", "うんうん", "かしげ", "ずいっ", "しょんぼり"}


class ScriptError(ValueError):
    """Invalid script, with source path and line number."""


def load_characters(path):
    with Path(path).open(encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: キャラ設定はマッピングが必要です")
    result = {}
    for key in ("mirai", "hinata"):
        item = data.get(key, {})
        expected = {"mirai": "ミライ", "hinata": "ひなた"}[key]
        if item.get("display_name") != expected or "通常" not in item.get("expressions", {}):
            raise ValueError(f"{path}: {key} の display_name / expressions.通常 を確認してください")
        result[expected] = item
    return result


def parse_script(path, characters, *, check_slides=True):
    """Return dialogue dicts; slide directives apply to following dialogue.

    slide is a zero-padded string, or None before the first directive.
    Expressions with null image assets are valid declared expressions.
    """
    path = Path(path)
    result = []
    slide = None
    screen_kind = None
    broll_keyword = None
    broll_note = None
    broll_id = None
    telop = None
    chapter = None
    for line_number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw.strip()
        if line.startswith("# ── "):
            chapter = line.removeprefix("# ── ").strip()
            continue
        if not line or line.startswith("#"):
            continue

        def fail(message):
            raise ScriptError(f"{path}:{line_number}: {message}")

        match = re.fullmatch(r"\[(スライド|画面):\s*([0-9]+)\]", line)
        if match:
            kind, digits = match.groups()
            number = int(digits)
            if number < 1:
                fail(f"{kind}番号は1以上にしてください")
            slide = f"{number:02d}"
            asset = (Path("slides") / f"{slide}.png" if kind == "スライド"
                     else Path("pages") / f"{slide}.html")
            if check_slides and not (path.parent / asset).is_file():
                fail(f"{kind}ファイルがありません: {asset}")
            screen_kind = kind
            broll_keyword = broll_note = broll_id = None
            continue
        match = re.fullmatch(r"\[映像:\s*(.*?)\s*\]", line)
        if match:
            parts = [part.strip() for part in match.group(1).split("|")]
            if len(parts) not in (2, 3):
                fail("映像タグには英語キーワードと日本語メモ、任意で id=数字 が必要です")
            broll_keyword, broll_note = parts[:2]
            broll_id = None
            if not broll_keyword or not broll_note:
                fail("映像タグには英語キーワードと日本語メモが必要です")
            if len(parts) == 3:
                id_match = re.fullmatch(r"id=([1-9][0-9]*)", parts[2])
                if not id_match:
                    fail("映像タグの素材指定は id=数字 にしてください")
                broll_id = int(id_match.group(1))
            slide = None
            screen_kind = "映像"
            continue
        match = re.fullmatch(r"\[テロップ:\s*([^\]]+?)\s*\]", line)
        if match:
            telop = match.group(1).strip()
            if not telop:
                fail("テロップの言葉が空です")
            continue
        if line == "[表示]":
            continue
        match = re.fullmatch(r"([^「]+)「(.+)」(?:\{([^{}]+)\})?", line)
        if not match:
            fail("形式が不正です。話者「セリフ」{表情} または [スライド: 03] を使ってください")
        speaker, text, tag = match.groups()
        expression = tag or "通常"
        if "|" in expression:
            expression, motion = expression.split("|", 1)
            if motion not in MOTIONS:
                fail(f"未定義の動き: {motion}")
        if speaker not in ("ミライ", "ひなた") or speaker not in characters:
            fail(f"不明な話者: {speaker}")
        if not text.strip():
            fail("セリフが空です")
        speech_text = re.sub(r"【([^【】]+)】", r"\1", text)
        if "【" in speech_text or "】" in speech_text:
            fail("強調は空でない文字を【】で囲んでください")
        if expression not in characters[speaker]["expressions"]:
            fail(f"{speaker} の未定義の表情: {expression}")
        if len(text) > 40:
            warnings.warn(f"{path}:{line_number}: セリフが40字を超えています（{len(text)}字）", stacklevel=2)
        item = dict(line=line_number, speaker=speaker, text=text, expression=expression, slide=slide)
        if speech_text != text:
            item["speech_text"] = speech_text
        if screen_kind:
            item["screen_kind"] = screen_kind
        if broll_keyword:
            item.update(broll_keyword=broll_keyword, broll_note=broll_note)
            if broll_id is not None:
                item["broll_id"] = broll_id
        if telop:
            item["telop"] = telop
        if chapter:
            item["chapter"] = chapter
        result.append(item)
        telop = None
    if not result:
        raise ScriptError(f"{path}:1: セリフがありません")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", type=Path)
    parser.add_argument("--characters", type=Path, default=Path("config/characters.yaml"))
    parser.add_argument("--no-slide-check", action="store_true")
    args = parser.parse_args()
    try:
        lines = parse_script(args.script, load_characters(args.characters), check_slides=not args.no_slide_check)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")
    print(json.dumps(lines, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
