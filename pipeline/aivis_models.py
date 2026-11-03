"""Download configured AivisHub AIVMX files atomically for the Actions cache."""
import argparse
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path

from pipeline.engine_config import load_engine

DOWNLOAD_URL = "https://api.aivis-project.com/v1/aivm-models/{uuid}/download?model_type=AIVMX"


def download_models(model_uuids, output, attempts=3):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for model_uuid in model_uuids:
        target = output / f"{model_uuid}.aivmx"
        if target.is_file() and target.stat().st_size > 0:
            print(f"キャッシュ利用: {target.name}")
            continue
        temporary = target.with_suffix(".aivmx.part")
        temporary.unlink(missing_ok=True)
        last_error = None
        for attempt in range(1, attempts + 1):
            try:
                request = urllib.request.Request(
                    DOWNLOAD_URL.format(uuid=model_uuid), headers={"User-Agent": "ai-money-channel-actions/1.0"})
                with urllib.request.urlopen(request, timeout=300) as response, temporary.open("wb") as stream:
                    shutil.copyfileobj(response, stream)
                if temporary.stat().st_size == 0:
                    raise OSError("ダウンロード結果が空です")
                temporary.replace(target)
                print(f"ダウンロード完了: {target.name} ({target.stat().st_size} bytes)")
                break
            except (OSError, urllib.error.URLError) as exc:
                temporary.unlink(missing_ok=True)
                last_error = exc
                if attempt < attempts:
                    time.sleep(attempt * 2)
        else:
            raise RuntimeError(f"AIVMXのダウンロードに失敗しました: {model_uuid}") from last_error


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    engine = load_engine()
    if engine["engine"] != "aivisspeech":
        print("AivisSpeech以外のため追加モデルはありません")
    else:
        download_models(engine["extra_models"], args.output)
