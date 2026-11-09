"""Publish only the selected review subtree to the fixed review-outputs branch."""
import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

BRANCH = "review-outputs"


def validate_source(source, episode, stage):
    if not re.fullmatch(r"ep[0-9]+_[\w-]+", episode) or stage not in ("voice", "voice_samples", "video", "thumbnail", "upload"):
        raise ValueError("確認用コピーのepisode/stageが不正です")
    source = Path(source)
    if source.is_symlink() or not source.is_dir():
        raise ValueError("確認用コピーのディレクトリがありません")
    files = []
    for path in source.rglob("*"):
        if path.is_symlink() or path.name == ".git":
            raise ValueError("確認用コピーにシンボリックリンクまたは.gitがあります")
        if path.is_file():
            if stage == "upload":
                if path.relative_to(source).as_posix() != "upload_result.json" or path.stat().st_size >= 100_000:
                    raise ValueError(f"投稿結果は100KB未満のupload_result.jsonだけ許可します: {path.name}")
                try:
                    result = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError) as exc:
                    raise ValueError("upload_result.jsonが不正です") from exc
                if not isinstance(result, dict) or not isinstance(result.get("video_id"), str) or not result["video_id"].strip():
                    raise ValueError("upload_result.jsonの動画IDが不正です")
            elif stage == "thumbnail":
                if path.relative_to(source).as_posix() != "thumbnail.png" or path.stat().st_size >= 2_000_000:
                    raise ValueError(f"サムネ確認用コピーは2MB未満のthumbnail.pngだけ許可します: {path.name}")
            elif stage == "video":
                name = path.relative_to(source).as_posix()
                limit = (100_000_000 if name == "video.mp4" else
                         2_000_000 if re.fullmatch(r"frames/[0-9]{2,3}-[0-9]{1,2}\.png", name) else
                         100_000 if re.fullmatch(r"broll_candidates/[0-9]{2,3}-[1-3]\.jpg", name) else
                         200_000 if name == "broll.json" else 0)
                if not limit or path.stat().st_size >= limit:
                    raise ValueError(
                        "動画確認用コピーは100MB未満のvideo.mp4、2MB未満のframes/NN-S.png、"
                        "100KB未満のbroll_candidates/NN-k.jpg、"
                        f"200KB未満のbroll.jsonだけ許可します: {name}"
                    )
                if name == "broll.json":
                    try:
                        manifest = json.loads(path.read_text(encoding="utf-8"))
                    except (OSError, ValueError) as exc:
                        raise ValueError("broll.jsonが不正です") from exc
                    if not isinstance(manifest, dict):
                        raise ValueError("broll.jsonが不正です")
            elif path.suffix not in (".mp3", ".json") or path.stat().st_size >= 100_000_000:
                raise ValueError(f"確認用コピーに許可されないファイルがあります: {path.name}")
            files.append(path)
    if stage == "upload":
        if len(files) != 1 or files[0].relative_to(source).as_posix() != "upload_result.json":
            raise ValueError("投稿結果にはupload_result.jsonだけが必要です")
    elif stage == "thumbnail":
        if len(files) != 1 or files[0].relative_to(source).as_posix() != "thumbnail.png":
            raise ValueError("サムネ確認用コピーにはthumbnail.pngだけが必要です")
    elif stage == "video":
        if not (source / "video.mp4").is_file():
            raise ValueError("動画確認用コピーにはvideo.mp4が必要です")
    else:
        required = "timeline.json" if stage == "voice" else "samples.json"
        if not files or not (source / required).is_file() or not any(p.suffix == ".mp3" for p in files):
            raise ValueError("確認用コピーの必須ファイルがありません")
    return source.resolve()


def publish(source, remote, episode, stage, *, env=None):
    source = validate_source(source, episode, stage)
    env = dict(os.environ if env is None else env)
    # A fresh working tree never checks out or pushes main. Existing other stages survive.
    with tempfile.TemporaryDirectory(prefix="review-publish-") as temporary:
        root = Path(temporary)

        def git(*args, check=True):
            return subprocess.run(["git", *args], cwd=root, env=env, check=check, capture_output=True, text=True)

        git("init", "--initial-branch", BRANCH)
        git("remote", "add", "origin", remote)
        git("config", "user.name", "github-actions[bot]")
        git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
        for attempt in range(3):
            exists = git("ls-remote", "--exit-code", "--heads", "origin", f"refs/heads/{BRANCH}", check=False)
            if exists.returncode == 0:
                git("fetch", "--depth=1", "origin", f"refs/heads/{BRANCH}")
                git("checkout", "-B", BRANCH, "FETCH_HEAD")
            elif exists.returncode != 2:
                raise RuntimeError("review-outputsの取得に失敗しました")
            elif attempt:
                raise RuntimeError("再試行中にreview-outputsが削除されました")
            destination = root / episode / stage
            if (root / episode).is_symlink() or destination.is_symlink():
                raise ValueError("保存先がシンボリックリンクです")
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(source, destination)
            git("add", "--all", "--", f"{episode}/{stage}")
            if git("diff", "--cached", "--quiet", check=False).returncode == 0:
                print("確認用コピーに変更なし")
                return
            git("commit", "-m", f"Review {episode}/{stage}")
            result = git("push", "origin", f"HEAD:refs/heads/{BRANCH}", check=False)
            if result.returncode == 0:
                print(f"確認用コピーを保存: {BRANCH}/{episode}/{stage}")
                return
            # A concurrent writer may advance the branch; refetch and replace only our subtree.
        raise RuntimeError("review-outputsへのpushに3回失敗しました。権限または同時更新を確認してください")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--stage", required=True)
    args = parser.parse_args()
    repository = os.environ["GITHUB_REPOSITORY"]
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repository):
        raise ValueError("GITHUB_REPOSITORYが不正です")
    token = os.environ["GH_TOKEN"]
    env = dict(os.environ)
    env.update(GIT_TERMINAL_PROMPT="0", GIT_CONFIG_COUNT="1",
               GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
               GIT_CONFIG_VALUE_0="AUTHORIZATION: basic " + base64.b64encode(f"x-access-token:{token}".encode()).decode())
    publish(args.source, f"https://github.com/{repository}.git", args.episode, args.stage, env=env)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
            stream.write(f"[確認用コピー](https://github.com/{repository}/tree/{BRANCH}/{args.episode}/{args.stage})\n")


if __name__ == "__main__":
    main()
