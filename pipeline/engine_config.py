"""One engine selection shared by Actions service startup and Python synthesis."""
import argparse
import json
import re
from pathlib import Path

import yaml

UUID_PATTERN = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def load_engine(path=Path("config/voice_engine.yaml")):
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    engine = data.get("engine")
    if engine not in ("voicevox", "aivisspeech"):
        raise ValueError("engine は voicevox または aivisspeech にしてください")
    config = data["engines"][engine]
    port = config["port"]
    image = config["image"]
    if type(port) is not int or not 1024 <= port <= 65535:
        raise ValueError("エンジンのportが不正です")
    prefix = {"voicevox": "voicevox/voicevox_engine:",
              "aivisspeech": "ghcr.io/aivis-project/aivisspeech-engine:"}[engine]
    if not isinstance(image, str) or not image.startswith(prefix + "cpu-") or not re.fullmatch(r"[\w./:@-]+", image):
        raise ValueError("エンジンには指定の公式CPU版Dockerイメージが必要です")
    extra_models = config.get("extra_models", [])
    if not isinstance(extra_models, list) or any(
            not isinstance(model, str) or not UUID_PATTERN.fullmatch(model) for model in extra_models):
        raise ValueError("extra_models はAivisHubのモデルUUIDの一覧にしてください")
    if len(extra_models) != len(set(extra_models)):
        raise ValueError("extra_models に同じモデルUUIDが重複しています")
    if engine != "aivisspeech" and extra_models:
        raise ValueError("extra_models はaivisspeechでのみ指定できます")
    return {"engine": engine, "image": image, "port": port, "url": f"http://127.0.0.1:{port}",
            "extra_models": extra_models}


def validate_episode(episode):
    if not re.fullmatch(r"ep[0-9]+_[\w-]+", episode):
        raise ValueError("episode は ep000_sample の形式で指定してください（パス不可）")
    return episode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    config = load_engine()
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as stream:
            for key, value in config.items():
                rendered = json.dumps(value, ensure_ascii=False, separators=(",", ":")) if isinstance(value, (list, dict)) else value
                stream.write(f"{key}={rendered}\n")
    print(json.dumps(config, ensure_ascii=False))
