"""Parse the production script without changing dialogue text."""
import argparse
import json
import re
import warnings
from pathlib import Path

import yaml


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
    for line_number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        def fail(message):
            raise ScriptError(f"{path}:{line_number}: {message}")

        match = re.fullmatch(r"\[スライド:\s*([0-9]+)\]", line)
        if match:
            number = int(match[1])
            if number < 1:
                fail("スライド番号は1以上にしてください")
            slide = f"{number:02d}"
            if check_slides and not (path.parent / "slides" / f"{slide}.png").is_file():
                fail(f"スライド画像がありません: slides/{slide}.png")
            continue
        match = re.fullmatch(r"([^「]+)「(.+)」(?:\{([^{}]+)\})?", line)
        if not match:
            fail("形式が不正です。話者「セリフ」{表情} または [スライド: 03] を使ってください")
        speaker, text, expression = match.groups()
        expression = expression or "通常"
        if speaker not in ("ミライ", "ひなた") or speaker not in characters:
            fail(f"不明な話者: {speaker}")
        if not text.strip():
            fail("セリフが空です")
        if expression not in characters[speaker]["expressions"]:
            fail(f"{speaker} の未定義の表情: {expression}")
        if len(text) > 40:
            warnings.warn(f"{path}:{line_number}: セリフが40字を超えています（{len(text)}字）", stacklevel=2)
        result.append(dict(line=line_number, speaker=speaker, text=text, expression=expression, slide=slide))
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
