"""Fail-closed byte verification for tagged release staging and draft replay.

This validates packaging only; semantic admission comes from upstream CI.
"""

import hashlib
import json
import re
import sys
from pathlib import Path


def _expected(tag):
    if re.fullmatch(r"l(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", tag) is None:
        raise ValueError("RELEASE_BLOCKED: malformed release tag")
    version = tag[1:]
    return {
        f"sens-cli_{version}_linux_amd64",
        f"sens-cli_{version}_windows_x64.exe",
        f"sens-cli_{version}_windows_x64.msi",
        f"sens-cli_{version}_macos_x64",
        f"sens-cli_{version}_macos_arm64",
        "sens-cli-web.html",
        "islands-manifest-v1.json",
        "install.sh",
    }


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for part in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(part)
    return digest.hexdigest()


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


def _check_sha(sha):
    if re.fullmatch(r"[0-9a-f]{40}", sha) is None:
        raise ValueError("RELEASE_BLOCKED: malformed source SHA")


def prepare(root, tag, sha):
    root = Path(root)
    _check_sha(sha)
    names = _expected(tag)
    _check_files(root, names)
    records = [
        {"name": name, "sha256": _sha256(root / name), "bytes": (root / name).stat().st_size}
        for name in sorted(names)
    ]
    manifest = {"schema": "sens-release-assets/v1", "tag": tag, "commit": sha,
                "contract": "11.9", "assets": records}
    (root / "release-provenance.json").write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    names.add("release-provenance.json")
    lines = [f"{_sha256(root / name)}  {name}\n" for name in sorted(names)]
    (root / "SHA256SUMS").write_text("".join(lines), encoding="ascii")
    _check_files(root, names | {"SHA256SUMS"})
    return manifest


def verify_replay(staged, downloaded, tag, sha):
    staged, downloaded = Path(staged), Path(downloaded)
    _check_sha(sha)
    names = _expected(tag)
    all_names = names | {"release-provenance.json", "SHA256SUMS"}
    _check_files(staged, all_names)
    _check_files(downloaded, all_names)
    manifest = json.loads(downloaded.joinpath("release-provenance.json").read_text(encoding="utf-8"))
    if (manifest.get("schema") != "sens-release-assets/v1" or
            manifest.get("tag") != tag or manifest.get("commit") != sha or
            manifest.get("contract") != "11.9"):
        raise ValueError("RELEASE_BLOCKED: provenance identity mismatch")
    expected_records = [
        {"name": name, "sha256": _sha256(downloaded / name),
         "bytes": (downloaded / name).stat().st_size}
        for name in sorted(names)
    ]
    if manifest.get("assets") != expected_records:
        raise ValueError("RELEASE_BLOCKED: manifest digest/size mismatch")
    checksummed = names | {"release-provenance.json"}
    expected_lines = "".join(
        f"{_sha256(downloaded / name)}  {name}\n" for name in sorted(checksummed)
    )
    if downloaded.joinpath("SHA256SUMS").read_text(encoding="ascii") != expected_lines:
        raise ValueError("RELEASE_BLOCKED: SHA256SUMS mismatch")
    for name in sorted(all_names):
        if _sha256(staged / name) != _sha256(downloaded / name):
            raise ValueError(f"RELEASE_BLOCKED: staged/replayed bytes differ: {name}")
    return len(names)


def main(argv):
    if len(argv) == 5 and argv[1] == "prepare":
        result = prepare(argv[2], argv[3], argv[4])
        print(f"RELEASE_STAGE_PASS count={len(result['assets'])} sha={result['commit']}")
    elif len(argv) == 6 and argv[1] == "replay":
        n = verify_replay(argv[2], argv[3], argv[4], argv[5])
        print(f"RELEASE_REPLAY_PASS count={n} sha={argv[5]}")
    else:
        raise SystemExit("usage: verify_release_assets.py prepare DIR TAG SHA | replay STAGED DOWNLOADED TAG SHA")


if __name__ == "__main__":
    try:
        main(sys.argv)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc
