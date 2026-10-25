#!/usr/bin/env python3
"""जीवन्मुक्त: materialize reviewed law-pair receipts; SENS owns all semantics."""
from pathlib import Path
import base64
import binascii
import subprocess


def root() -> Path:
    try:
        result = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        ).strip()
        return Path(result)
    except (OSError, subprocess.CalledProcessError):
        return Path(__file__).resolve().parents[1]


STEMS = (
    "d5-numberp-nonnumber-law",
    "d5-d12-zerop-law",
    "d5-d12-numberp-law",
    "d10-clips-printout-head-direct-law",
    "d10-clips-assert-head-direct-law",
    "d10-empty-queue-law",
)


def decode_receipt(path: Path, stem: str) -> bytes:
    try:
        payload = base64.b64decode(path.read_text(encoding="ascii").strip(), validate=True)
    except (OSError, UnicodeDecodeError, binascii.Error) as error:
        raise SystemExit(f"{stem}: invalid reviewed base64 receipt {path.name}: {error}") from error
    if not payload:
        raise SystemExit(f"{stem}: empty reviewed payload in {path.name}")
    return payload


def main() -> None:
    repository = root()
    source = repository / "knowledge" / "d11" / "restore" / "jivanmukta"
    semantic = repository / "tests" / "semantic"

    # Validate every receipt before writing any generated law pair.
    decoded = []
    for stem in STEMS:
        sens_bytes = decode_receipt(source / f"{stem}.sens.b64", stem)
        view_bytes = decode_receipt(source / f"{stem}.view.b64", stem)
        decoded.append((stem, sens_bytes, view_bytes))

    # Stage all outputs first so a malformed later receipt cannot leave a
    # partially refreshed set of physical witnesses.
    staged = []
    try:
        for stem, sens_bytes, view_bytes in decoded:
            for target, payload in (
                (semantic / f"{stem}.sens", sens_bytes),
                (semantic / stem, view_bytes),
            ):
                temporary = target.with_name(f".{target.name}.mint.tmp")
                temporary.write_bytes(payload)
                staged.append((temporary, target, len(payload)))
        for temporary, target, _length in staged:
            temporary.replace(target)
    except OSError as error:
        for temporary, _target, _length in staged:
            temporary.unlink(missing_ok=True)
        raise SystemExit(f"law-pair materialization failed before completion: {error}") from error

    for stem, sens_bytes, _view_bytes in decoded:
        print("minted", stem, len(sens_bytes))


if __name__ == "__main__":
    main()
