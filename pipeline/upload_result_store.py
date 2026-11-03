"""Restore and persist upload_result.json on the review-outputs branch."""
import argparse
import base64
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from pipeline.publish_review import BRANCH, publish


class ResultStoreError(RuntimeError):
    pass


def _validate_episode(episode: str) -> None:
    if not re.fullmatch(r"ep[0-9]+_[\w-]+", episode):
        raise ValueError("episode名が不正です")


def fetch(remote: str, episode: str, destination: Path, *, env=None) -> bool:
    """Fetch a prior result. Missing branch/file is allowed; transport failure is not."""
    _validate_episode(episode)
    destination = Path(destination)
    env = dict(os.environ if env is None else env)
    with tempfile.TemporaryDirectory(prefix="upload-result-fetch-") as temporary:
        root = Path(temporary)

        def git(*args, check=True):
            result = subprocess.run(["git", *args], cwd=root, env=env, check=False,
                                    capture_output=True, text=True)
            if check and result.returncode:
                raise ResultStoreError("review-outputsから過去の投稿結果を取得できません")
            return result

        git("init", "--initial-branch", BRANCH)
        git("remote", "add", "origin", remote)
        exists = git("ls-remote", "--exit-code", "--heads", "origin", f"refs/heads/{BRANCH}", check=False)
        if exists.returncode == 2:
            print("過去の投稿結果なし（review-outputsブランチ未作成）")
            return False
        if exists.returncode != 0:
            raise ResultStoreError("review-outputsを確認できないため投稿しません")
        git("fetch", "--depth=1", "origin", f"refs/heads/{BRANCH}")
        relative = f"{episode}/upload/upload_result.json"
        listing = git("ls-tree", "--name-only", "FETCH_HEAD", "--", relative)
        if not listing.stdout.strip():
            print("過去の投稿結果なし")
            return False
        raw = git("show", f"FETCH_HEAD:{relative}").stdout
        try:
            result = json.loads(raw)
        except ValueError as exc:
            raise ResultStoreError("保存済みのupload_result.jsonが不正です") from exc
        video_id = result.get("video_id") if isinstance(result, dict) else None
        if not isinstance(video_id, str) or not video_id.strip():
            raise ResultStoreError("保存済みのupload_result.jsonに動画IDがありません")
        if destination.is_symlink():
            raise ResultStoreError("投稿結果の保存先がシンボリックリンクです")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(raw, encoding="utf-8")
        print(f"過去の投稿結果を復元: {video_id}")
        return True


def authenticated_env(token: str) -> dict:
    if not token:
        raise ResultStoreError("GitHubトークンがありません。過去の投稿結果を確認できないため投稿しません")
    env = dict(os.environ)
    header = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    env.update(GIT_TERMINAL_PROMPT="0", GIT_CONFIG_COUNT="1",
               GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
               GIT_CONFIG_VALUE_0=f"AUTHORIZATION: basic {header}")
    return env


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("fetch", "publish"))
    parser.add_argument("--episode", required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repository):
        raise ResultStoreError("GITHUB_REPOSITORYが不正です")
    remote = f"https://github.com/{repository}.git"
    env = authenticated_env(os.environ.get("GH_TOKEN", ""))
    result_dir = args.root / "output" / args.episode / "upload"
    if args.action == "fetch":
        fetch(remote, args.episode, result_dir / "upload_result.json", env=env)
    else:
        publish(result_dir, remote, args.episode, "upload", env=env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
