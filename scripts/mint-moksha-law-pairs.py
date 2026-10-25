#!/usr/bin/env python3
"""मोक्ष: validate reviewed T5M receipts before materializing law pairs."""
from pathlib import Path
import base64
import binascii
import subprocess


def root() -> Path:
    try:
        return Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        ).strip())
    except (OSError, subprocess.CalledProcessError):
        return Path(__file__).resolve().parents[1]


STEMS = (
    "d6-all-invalid-root-law",
    "d6-any-invalid-root-law",
    "d6-d12-ratio-normalizes-integer-law",
    "d4-append-general-proper-law",
    "d6-d12-integer-rational-law",
    "d6-let-letstar-preflight-law",
    "compiler-reverse-onto-proper-law",
    "d6-intersection-order-law",
)


def decode_receipt(path: Path, stem: str) -> bytes:
    try:
        payload = base64.b64decode(
            path.read_text(encoding="ascii").strip(), validate=True
        )
    except (OSError, UnicodeDecodeError, binascii.Error) as error:
        raise SystemExit(
            f"{stem}: invalid reviewed base64 receipt {path.name}: {error}"
        ) from error
    if not payload:
        raise SystemExit(f"{stem}: empty reviewed payload in {path.name}")
    return payload


def main() -> None:
    repository = root()
    source = repository / "knowledge" / "d11" / "restore" / "moksha"
    semantic = repository / "tests" / "semantic"

    # Validate every reviewed receipt before changing any generated witness.
    decoded = []
    for stem in STEMS:
        sens_bytes = decode_receipt(source / f"{stem}.sens.b64", stem)
        view_bytes = decode_receipt(source / f"{stem}.view.b64", stem)
        decoded.append((stem, sens_bytes, view_bytes))

    # Stage every output first; malformed or missing later receipts cannot leave
    # a partially refreshed set. Replacing each file only occurs after all
    # source receipts have passed strict validation and all temp writes succeed.
    staged = []
    try:
        for stem, sens_bytes, view_bytes in decoded:
            for target, payload in (
                (semantic / f"{stem}.sens", sens_bytes),
                (semantic / stem, view_bytes),
            ):
                temporary = target.with_name(f".{target.name}.mint.tmp")
                temporary.write_bytes(payload)
                staged.append((temporary, target))
        for temporary, target in staged:
            temporary.replace(target)
    except OSError as error:
        for temporary, _target in staged:
            temporary.unlink(missing_ok=True)
        raise SystemExit(
            f"law-pair materialization failed before completion: {error}"
        ) from error

    for stem, sens_bytes, _view_bytes in decoded:
        print("minted", stem, len(sens_bytes))


if __name__ == "__main__":
    main()
