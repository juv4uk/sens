"""Fail-closed release tag/version check; never rely on Python assert.

The semantic contract is independent of package version; this guard checks
only the release tag and the CLI package version in the pinned checkout.
"""

import re
import sys
import tomllib
from pathlib import Path


def verify_release_tag(tag: str, root: Path) -> str:
    if re.fullmatch(r"s(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", tag) is None:
        raise ValueError(f"RELEASE_BLOCKED: invalid release tag {tag!r}")
    manifest = root / "crates" / "sens-cli" / "Cargo.toml"
    version = tomllib.loads(manifest.read_text(encoding="utf-8"))["package"]["version"]
    if tag != f"s{version}":
        raise ValueError(
            f"RELEASE_BLOCKED: tag {tag} does not match sens-cli package version {version}"
        )
    return version


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: verify_release_tag.py RELEASE_TAG", file=sys.stderr)
        return 2
    try:
        version = verify_release_tag(argv[1], Path(__file__).resolve().parents[1])
    except (ValueError, OSError, KeyError, tomllib.TOMLDecodeError) as exc:
        print(f"RELEASE_BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(f"RELEASE_TAG_VERSION_PASS version={version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
