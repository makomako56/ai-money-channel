"""各段階の前に、回の入力（台本・画面・meta.json・thumbnail.json）を確かめる。

エラーは終了コード2で止める。警告は止めずに --warnings-file に1行ずつ書く（Summary に出す）。
"""
import argparse
import json
from pathlib import Path
import re
import sys

import yaml

from pipeline.make_thumbnail import validate_input
from pipeline.script_parser import ScriptError, load_characters, parse_script

ROOT = Path(__file__).resolve().parent.parent
EPISODE = re.compile(r"ep[0-9]+_[\w-]+\Z")
META_FIELDS = {"title": str, "description": str, "tags": list, "category_id": str}
STAGES = ("voice", "video", "thumbnail", "all")


class PreflightError(ValueError):
    pass


def check_script(episode_dir, root=ROOT):
    """台本の形式と、[画面]/[スライド] のファイルの有無。セリフ数と画面数を返す。"""
    characters = load_characters(root / "config" / "characters.yaml")
    try:
        lines = parse_script(episode_dir / "script.txt", characters)
    except (ScriptError, OSError) as exc:
        raise PreflightError(f"台本: {exc}") from exc
    return len(lines), len({line["slide"] for line in lines if line["slide"]})


def check_meta(episode_dir):
    """YouTube に送るメタ情報の必須項目と長さ（タイトル100字・概要5000字の上限）。"""
    warnings = []
    path = episode_dir / "meta.json"
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreflightError(f"meta.json: 読めません（{exc}）") from exc
    if not isinstance(meta, dict):
        raise PreflightError("meta.json: オブジェクトが必要です")
    for key, kind in META_FIELDS.items():
        if not isinstance(meta.get(key), kind) or not meta[key]:
            raise PreflightError(f"meta.json: {key} が必要です")
    if len(meta["title"]) > 100:
        raise PreflightError(f"meta.json: title が100字を超えています（{len(meta['title'])}字）")
    if len(meta["description"]) > 5000:
        raise PreflightError(f"meta.json: description が5000字を超えています（{len(meta['description'])}字）")
    if "<" in meta["title"] or ">" in meta["title"] or "<" in meta["description"] or ">" in meta["description"]:
        raise PreflightError("meta.json: title / description に < > は使えません（YouTube の制限）")
    if not all(isinstance(tag, str) and tag for tag in meta["tags"]):
        raise PreflightError("meta.json: tags は文字列の配列が必要です")
    if sum(len(tag) for tag in meta["tags"]) > 450:
        warnings.append("meta.json: タグの合計が450字を超えています（YouTube の上限500字に近い）")
    if not meta["category_id"].isdigit():
        raise PreflightError("meta.json: category_id は数字の文字列が必要です")
    return warnings


def check_thumbnail(episode_dir, root=ROOT):
    try:
        data = json.loads((episode_dir / "thumbnail.json").read_text(encoding="utf-8"))
        characters = yaml.safe_load((root / "config" / "characters.yaml").read_text(encoding="utf-8"))
        style = yaml.safe_load((root / "config" / "thumbnail_style.yaml").read_text(encoding="utf-8"))
        validate_input(data, characters, style, root=root)
    except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError) as exc:
        raise PreflightError(f"thumbnail.json: {exc}") from exc


def run(episode, stage, root=ROOT):
    """段階に必要な入力だけを確かめる。(セリフ数, 画面数, 警告) を返す。"""
    if not EPISODE.fullmatch(episode):
        raise PreflightError("episode の形式が不正です")
    if stage not in STAGES:
        raise PreflightError(f"stage が不正です: {stage}")
    episode_dir = root / "episodes" / episode
    if episode_dir.is_symlink() or not episode_dir.is_dir():
        raise PreflightError(f"エピソードがありません: {episode}")
    warnings, lines, screens = [], 0, 0
    if stage in ("voice", "video", "all"):
        lines, screens = check_script(episode_dir, root)
    if stage in ("thumbnail", "all"):
        check_thumbnail(episode_dir, root)
    if stage == "all":
        warnings += check_meta(episode_dir)
    return lines, screens, warnings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--warnings-file")
    args = parser.parse_args(argv)
    try:
        lines, screens, warnings = run(args.episode, args.stage)
    except PreflightError as exc:
        print(f"::error::入力チェックで停止: {exc}")
        return 2
    if args.warnings_file:
        with open(args.warnings_file, "a", encoding="utf-8") as stream:
            stream.writelines(f"{warning}\n" for warning in warnings)
    for warning in warnings:
        print(f"::warning::{warning}")
    print(f"入力チェックOK: セリフ{lines}行、画面{screens}枚（stage={args.stage}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
