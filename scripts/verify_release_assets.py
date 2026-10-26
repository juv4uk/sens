"""Fail-closed byte verification for tagged release staging and draft replay.

Packaging integrity is established by exact byte comparison of independently
downloaded files and the immutable Git commit identity. No digest sidecars or
checksum manifests are created.
"""

import json
import re
import sys
from pathlib import Path


def _expected(tag):
    if re.fullmatch(r"l(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)", tag) is None:
        raise ValueError("RELEASE_BLOCKED: malformed release tag")
    version = tag[1:]
    return {
        f"sens-cli_{version}_linux_amd64",
        f"sens-cli_{version}_windows_x64.exe",
        f"sens-cli_{version}_windows_x64.msi",
        f"sens-cli_{version}_macos_x64",
        f"sens-cli_{version}_macos_arm64",
        "sens-cli-web.html",
        "my-lisp-cli-web.html",
        "islands-manifest-v1.json",
        "install.sh",
    }


def _check_files(root, names):
    if not root.is_dir() or root.is_symlink():
        raise ValueError("RELEASE_BLOCKED: no valid artifact directory")
    actual = {p.name for p in root.iterdir()}
    if actual != names:
        raise ValueError(
            f"RELEASE_BLOCKED: asset set mismatch missing={sorted(names - actual)} "
            f"extra={sorted(actual - names)}"
        )
    for name in sorted(names):
        path = root / name
        if not path.is_file() or path.is_symlink() or path.stat().st_size == 0:
            raise ValueError(f"RELEASE_BLOCKED: invalid, missing or empty asset {name}")
    if (root / "my-lisp-cli-web.html").read_bytes() != (root / "sens-cli-web.html").read_bytes():
        raise ValueError("RELEASE_BLOCKED: web compatibility alias differs from canonical HTML")


def _check_git_commit(commit):
    if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise ValueError("RELEASE_BLOCKED: malformed Git commit identity")


def prepare(root, tag, commit):
    root = Path(root)
    _check_git_commit(commit)
    names = _expected(tag)
    _check_files(root, names)
    manifest = {
        "schema": "sens-release-assets/v1",
        "tag": tag,
        "commit": commit,
        "contract": "12.0",
        "assets": [
            {"name": name, "bytes": (root / name).stat().st_size}
            for name in sorted(names)
        ],
    }
    (root / "release-provenance.json").write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\\n",
        encoding="utf-8",
    )
    _check_files(root, names | {"release-provenance.json"})
    return manifest


def _reject_duplicate_json_keys(pairs):
    unique = {}
    for key, value in pairs:
        if key in unique:
            raise ValueError(f"RELEASE_BLOCKED: duplicate provenance JSON key {key!r}")
        unique[key] = value
    return unique


def verify_replay(staged, downloaded, tag, commit):
    staged, downloaded = Path(staged), Path(downloaded)
    _check_git_commit(commit)
    if staged.resolve() == downloaded.resolve():
        raise ValueError("RELEASE_BLOCKED: replay requires independent download directory")
    names = _expected(tag)
    all_names = names | {"release-provenance.json"}
    _check_files(staged, all_names)
    _check_files(downloaded, all_names)
    for name in sorted(all_names):
        staged_stat = (staged / name).stat()
        downloaded_stat = (downloaded / name).stat()
        if (staged_stat.st_dev == downloaded_stat.st_dev and
                staged_stat.st_ino == downloaded_stat.st_ino):
            raise ValueError(
                f"RELEASE_BLOCKED: replay asset not independently downloaded: {name}"
            )
    manifest = json.loads(
        downloaded.joinpath("release-provenance.json").read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_json_keys,
    )
    if not isinstance(manifest, dict):
        raise ValueError("RELEASE_BLOCKED: malformed provenance object")
    if (manifest.get("schema") != "sens-release-assets/v1" or
            manifest.get("tag") != tag or manifest.get("commit") != commit or
            manifest.get("contract") != "12.0"):
        raise ValueError("RELEASE_BLOCKED: provenance identity mismatch")
    expected_records = [
        {"name": name, "bytes": (downloaded / name).stat().st_size}
        for name in sorted(names)
    ]
    if manifest.get("assets") != expected_records:
        raise ValueError("RELEASE_BLOCKED: asset names/size mismatch")
    for name in sorted(all_names):
        if (staged / name).read_bytes() != (downloaded / name).read_bytes():
            raise ValueError(f"RELEASE_BLOCKED: staged/replayed bytes differ: {name}")
    return len(names)


def main(argv):
    if len(argv) == 5 and argv[1] == "prepare":
        result = prepare(argv[2], argv[3], argv[4])
        print(f"RELEASE_STAGE_PASS count={len(result['assets'])} commit={result['commit']}")
    elif len(argv) == 6 and argv[1] == "replay":
        n = verify_replay(argv[2], argv[3], argv[4], argv[5])
        print(f"RELEASE_REPLAY_PASS count={n} commit={argv[5]}")
    else:
        raise SystemExit("usage: verify_release_assets.py prepare DIR TAG COMMIT | replay STAGED DOWNLOADED TAG COMMIT")


if __name__ == "__main__":
    try:
        main(sys.argv)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc
