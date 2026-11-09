"""Generate per-line WAV/timeline or MP3 samples of every available talking style."""
import argparse
import array
import csv
import io
import json
import math
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import warnings
import wave
from pathlib import Path

import yaml

from pipeline.engine_config import load_engine, validate_episode
from pipeline.script_parser import load_characters, parse_script

SAMPLE_TEXTS = (
    "結論から言うと、この会社はAIを売っているんじゃなくて、AIを動かす場所を貸しているんです",
    "え、それってつまり大家さんってことですか！？",
)


class SpeechEngine:
    def __init__(self, url, engine="voicevox"):
        self.url = url.rstrip("/")
        self.engine = engine

    def request(self, endpoint, *, params=None, body=None, method="GET", binary=False):
        url = self.url + endpoint
        if params:
            url += "?" + urllib.parse.urlencode(params)
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(url, data=data, method=method)
        if data is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                result = response.read()
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"{self.engine} {endpoint}: HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"{self.engine} {endpoint}: 接続失敗またはタイムアウト") from exc
        return result if binary else json.loads(result)

    def synthesize(self, text, speaker_id, speed, pitch, **settings):
        query = self.request("/audio_query", params={"text": text, "speaker": speaker_id}, method="POST")
        query.update(speedScale=speed, pitchScale=pitch, outputSamplingRate=24000, outputStereo=False,
                     intonationScale=settings.get("intonation", 1.0), volumeScale=settings.get("volume", 1.0),
                     prePhonemeLength=settings.get("pre_phoneme", 0.05),
                     postPhonemeLength=settings.get("post_phoneme", 0.05))
        if self.engine == "voicevox":
            for phrase in query.get("accent_phrases", []):
                pause = phrase.get("pause_mora")
                if pause is not None:
                    pause["vowel_length"] = min(0.5, pause["vowel_length"] * settings.get("pause_scale", 1.4))
        # AivisSpeech ignores mora durations; preserve its original kana/text.
        return self.request("/synthesis", params={"speaker": speaker_id}, body=query, method="POST", binary=True)


def voice_catalog(speakers):
    return [dict(name=speaker["name"], style=style["name"], id=style["id"])
            for speaker in speakers for style in speaker["styles"]
            if style.get("type", "talk") in ("talk", "streaming_talk")]


def normal_voice(catalog, name):
    for style in ("ノーマル", "通常"):
        for voice in catalog:
            if voice["name"] == name and voice["style"] == style:
                return voice
    raise ValueError(f"通常系スタイルが見つかりません: {name}")


def resolve_voice(config, catalog, speaker, engine="voicevox"):
    speaker_id = config.get("speaker_id")
    name = config.get("name")
    if speaker_id is not None:
        if type(speaker_id) is not int:
            raise ValueError(f"{speaker}: speaker_id は整数が必要です")
        matches = [voice for voice in catalog if voice["id"] == speaker_id]
    elif name:
        # Accept the canonical character(style) spelling and common separators.
        matches = [voice for voice in catalog if name in (
            f'{voice["name"]}（{voice["style"]}）', f'{voice["name"]}({voice["style"]})',
            f'{voice["name"]} {voice["style"]}', f'{voice["name"]}/{voice["style"]}',
            f'{voice["name"]}・{voice["style"]}')]
    else:
        if engine == "voicevox":
            voice = normal_voice(catalog, "No.7" if speaker == "ミライ" else "春日部つむぎ")
        else:
            normal = [item for item in catalog if item["style"] in ("ノーマル", "通常", "Normal")]
            choices = normal or catalog
            if not choices:
                raise ValueError("エンジンに利用可能な声がありません")
            voice = choices[0 if speaker == "ミライ" else min(1, len(choices) - 1)]
        warnings.warn(f'{speaker}: 声が未設定のため仮の声 {voice["name"]}（{voice["style"]}）を使います', stacklevel=2)
        return voice
    if len(matches) != 1:
        raise ValueError(f"{speaker}: 設定された声が一意に見つかりません（speaker_id={speaker_id}, name={name}）")
    return matches[0]


def register_dictionary(client, path):
    path = Path(path)
    header = ["表記", "読み", "アクセント位置"]
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(",".join(header) + "\n", encoding="utf-8")
    entries = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != header:
            raise ValueError(f"{path}:1: CSVヘッダーは {','.join(header)} が必要です")
        for row in reader:
            try:
                surface, pronunciation = row["表記"].strip(), row["読み"].strip()
                accent = int(row["アクセント位置"])
                if not surface or not pronunciation or accent < 0 or None in row:
                    raise ValueError()
            except (ValueError, AttributeError, TypeError) as exc:
                raise ValueError(f"{path}:{reader.line_num}: 辞書の行が不正です") from exc
            entries.append((reader.line_num, dict(surface=surface, pronunciation=pronunciation, accent_type=accent)))
    for line, params in entries:
        try:
            client.request("/user_dict_word", method="POST", params=params)
        except RuntimeError as exc:
            raise RuntimeError(f"{path}:{line}: 辞書登録に失敗: {exc}") from exc
    print(f"読み辞書: {len(entries)}語を登録")


def inspect_wav(data):
    """Return exact PCM duration and 30fps RMS envelope, scaled to full scale."""
    with wave.open(io.BytesIO(data), "rb") as wav:
        if wav.getsampwidth() != 2 or wav.getnchannels() != 1 or wav.getcomptype() != "NONE":
            raise ValueError("音声は16bit mono PCM WAVが必要です")
        rate, frames = wav.getframerate(), wav.getnframes()
        pcm = wav.readframes(frames)
    if not frames or len(pcm) != frames * 2:
        raise ValueError("WAVが空または不完全です")
    samples = array.array("h", pcm)
    if sys.byteorder != "little":
        samples.byteswap()
    envelope = []
    for i in range(math.ceil(frames * 30 / rate)):
        chunk = samples[i * rate // 30:min((i + 1) * rate // 30, frames)]
        envelope.append(round(math.sqrt(sum(v * v for v in chunk) / len(chunk)) / 32768, 6))
    return frames / rate, envelope


def finite_number(value, label, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f"{label}: {minimum}〜{maximum} の有限数が必要です")
    return float(value)


def load_gaps(path):
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    audio = data["audio"]
    return (finite_number(audio["dialogue_gap_seconds"], "dialogue_gap_seconds", 0, 60),
            finite_number(audio["slide_gap_seconds"], "slide_gap_seconds", 0, 60))


def voice_settings(config, speaker):
    defaults = {"intonation": 1.2 if speaker == "ミライ" else 1.3, "volume": 1.0,
                "pre_phoneme": 0.05, "post_phoneme": 0.05, "pause_scale": 1.4}
    limits = {"intonation": (0, 2), "volume": (0, 2), "pre_phoneme": (0, 2),
              "post_phoneme": (0, 2), "pause_scale": (0, 10)}
    return {key: finite_number(config.get(key, default), f"{speaker}.{key}", *limits[key])
            for key, default in defaults.items()}


def make_voice(lines, characters, catalog, client, output, gaps, engine="voicevox"):
    resolved = {}
    if engine == "aivisspeech":
        warnings.warn("AivisSpeechはモーラ長の変更に非対応のためpause_scaleは適用しません。句読点の自然な間はエンジンに任せます", stacklevel=2)
    for speaker, character in characters.items():
        config = character["voice"]
        selection = config.get("voices", {}).get(engine, {})
        # Read older VOICEVOX-only configuration without reusing its IDs in AivisSpeech.
        if "voices" not in config and engine == "voicevox":
            selection = config
        settings_config = {**config, **selection}
        resolved[speaker] = (resolve_voice(selection, catalog, speaker, engine),
                             finite_number(settings_config.get("speed", 1), f"{speaker}.speed", 0.1, 4),
                             finite_number(settings_config.get("pitch", 0), f"{speaker}.pitch", -0.15, 0.15),
                             voice_settings(settings_config, speaker))
    timeline = []
    end = 0.0
    previous_slide = None
    (output / "wav").mkdir()
    for index, line in enumerate(lines, 1):
        voice, speed, pitch, settings = resolved[line["speaker"]]
        gap = 0 if index == 1 else gaps[int(line["slide"] != previous_slide)]
        start = end + gap
        try:
            audio = client.synthesize(line.get("speech_text", line["text"]), voice["id"], speed, pitch, **settings)
            duration, envelope = inspect_wav(audio)
        except (ValueError, RuntimeError, wave.Error) as exc:
            raise RuntimeError(f'script.txt:{line["line"]}: 音声生成失敗: {exc}') from exc
        relative = f"wav/{index:04d}.wav"
        (output / relative).write_bytes(audio)
        end = start + duration
        timeline.append({**line, "start": start, "end": end, "wav": relative,
                         "envelope_fps": 30, "envelope": envelope, "voice": voice, "engine": engine})
        previous_slide = line["slide"]
        print(f'音声 {index}/{len(lines)}: 行{line["line"]}, {duration:.3f}秒')
    (output / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_samples(catalog, client, output, gap):
    samples = []
    for voice in catalog:
        segments = [client.synthesize(text, voice["id"], 1.0, 0.0) for text in SAMPLE_TEXTS]
        for segment in segments:
            inspect_wav(segment)
        with tempfile.TemporaryDirectory() as temporary:
            combined = Path(temporary) / "combined.wav"
            with wave.open(str(combined), "wb") as target:
                target.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
                for index, segment in enumerate(segments):
                    with wave.open(io.BytesIO(segment), "rb") as source:
                        if source.getframerate() != 24000:
                            raise ValueError("サンプル音声のサンプルレートが不正です")
                        if index:
                            target.writeframes(b"\0\0" * round(24000 * gap))
                        target.writeframes(source.readframes(source.getnframes()))
            label = re.sub(r"[^\w.（）()-]+", "_", f'{voice["name"]}_{voice["style"]}')[:100]
            filename = f'{label}_{voice["id"]}.mp3' 
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                            "-i", str(combined), "-codec:a", "libmp3lame", "-q:a", "2", str(output / filename)], check=True)
        samples.append({**voice, "mp3": filename})
        print(f"サンプル: {filename}（同じ2文、話速1.0・音高0.0）", flush=True)
    (output / "samples.json").write_text(json.dumps({"texts": SAMPLE_TEXTS, "voices": samples}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def engine_credit(engine, names):
    return ("音声：AivisSpeech（" + "・".join(names) + "）" if engine == "aivisspeech"
            else " / ".join("VOICEVOX:" + name for name in names))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--stage", choices=("voice", "voice_samples"), default="voice")
    parser.add_argument("--engine-url", help="ローカル検証用URL。通常はvoice_engine.yamlから決定")
    parser.add_argument("--no-slide-check", action="store_true")
    args = parser.parse_args()
    try:
        validate_episode(args.episode)
        episode = Path("episodes") / args.episode
        if not episode.is_dir() or episode.is_symlink():
            raise ValueError(f"エピソードがありません: {episode}")
        characters = load_characters("config/characters.yaml")
        gaps = load_gaps("config/style.yaml")
        lines = parse_script(episode / "script.txt", characters, check_slides=not args.no_slide_check) if args.stage == "voice" else None
        engine = load_engine()
        client = SpeechEngine(args.engine_url or engine["url"], engine["engine"])
        catalog = voice_catalog(client.request("/speakers"))
        if not catalog or len({voice["id"] for voice in catalog}) != len(catalog):
            raise ValueError("エンジンの話者一覧が空、またはスタイルIDが重複しています")
        register_dictionary(client, "config/reading_dict.csv")
        output = Path("output") / args.episode / args.stage
        # Do not mix stale or partial outputs from a previous invocation.
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            raise ValueError(f"出力先が既に存在します。別の場所に退避してから再実行してください: {output}")
        with tempfile.TemporaryDirectory(dir=output.parent, prefix=".voice-") as temporary:
            staging = Path(temporary) / args.stage
            staging.mkdir()
            if args.stage == "voice":
                make_voice(lines, characters, catalog, client, staging, gaps, engine["engine"])
            else:
                make_samples(catalog, client, staging, gaps[0])
            if args.stage == "voice":
                timeline = json.loads((staging / "timeline.json").read_text(encoding="utf-8"))
                used_names = list(dict.fromkeys(item["voice"]["name"] for speaker in characters for item in timeline if item["speaker"] == speaker))
            else:
                used_names = list(dict.fromkeys(item["name"] for item in catalog))
            credit = engine_credit(engine["engine"], used_names)
            (staging / "engine.json").write_text(json.dumps({**engine, "version": client.request("/version"), "catalog": catalog,
                                                          "credit": credit}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            staging.rename(output)
        print(f"完了: {output}")
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, yaml.YAMLError, subprocess.CalledProcessError, wave.Error) as exc:
        parser.exit(1, f"ERROR: {exc}\n")


if __name__ == "__main__":
    main()
