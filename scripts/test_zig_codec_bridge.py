#!/usr/bin/env python3
"""One focused real Zig 0.16 migration-bridge test; transport only.

This is not a SENS evaluator or a semantic oracle. No repository files are
rewritten. An invalid T5 octet must be rejected rather than silently decoded.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import tempfile

from zig_codec_bridge import (
    ZigCodecError,
    build_transport,
    encode_t5,
    require_parity,
    verify_t5,
)

REPO = Path(__file__).resolve().parents[1]
# #5812: the corridor MINTS these exact bytes from the extensionless spaced-bit
# view. Both files are committed fixtures; the .sens sha is pinned independently.
BRANCH_FIXTURE = REPO / "tests/fixtures/migration-d1-cond-cohort/branch"
BRANCH_SENS_SHA256 = "6568d9888039c0e33ace2378a39f0201f7d4ed67c71f23a6bb61605353976904"

GOLDEN_T5 = bytes.fromhex("638906a1")  # Known canonical T5 bytes for QUOTE.
# These fixture digests are fixed independently of the input under test.
# A production release must supply its own trusted source digest/provenance.
GOLDEN_D10_ZERO_SHA256 = "96a296d224f285c67bee93c30f8a309157f0daa35dc5b87e410b78630a09cfc7"
GOLDEN_D1_ONE_SHA256 = "8a8950f7623663222542c9469c73be3c4c81bbdf019e2c577590a61f2ce9a157"

# Independently pinned physical vectors. Width is part of each word's identity:
# D1:1 != D2:01, and D2:00/11 must survive without trimmed leading bits.
GOLDEN_WIDTH_VECTORS = {
    "d1_zero": "50",
    "d1_one": "a1",
    "d2_zero_zero": "1a",
    "d2_zero_one": "35",
    "d2_one_zero": "6b",
    "d2_one_one": "86",
    "d2_d3_d2_multiple_words": "663b",
    "d9_leading_zero_width": "5102",
    "d10_zero_coordinate": "0000",
}
NEGATIVE_PHYSICAL = {
    "invalid_byte_243": "f3",
    "empty": "",
    "all_padding": "f2",
    "empty_domain_word": "a2",
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def assert_physical_roundtrip(executable: Path, name: str, raw: bytes) -> None:
    proof = verify_t5(executable, raw)
    expected = sha(raw)
    if (proof.get("physical_sha256") != expected or
            proof.get("profile") != "D1-D10_COORDINATES_NOT_EXECUTION" or
            proof.get("zig_version") != "0.16.0"):
        raise AssertionError(
            f"ZIG_T5_GOLDEN_MISMATCH test_id=zig-migration-bridge-t5-exact-physical "
            f"layer=transport fixture={name} expected_sha256={expected} "
            f"actual={proof!r} first_difference=UNKNOWN "
            "reproduce='python3 scripts/test_zig_codec_bridge.py'"
        )


def assert_physical_rejected(executable: Path, name: str, raw: bytes) -> None:
    try:
        verify_t5(executable, raw)
    except ZigCodecError as exc:
        if "ZIG_CODEC_FAILURE" not in str(exc):
            raise AssertionError(
                f"ZIG_T5_REJECT_HARNESS_ERROR test_id=zig-migration-bridge-t5-exact-physical "
                f"layer=transport fixture={name} fixture_sha256={sha(raw)} "
                f"expected=physical_reject actual={exc!s}"
            ) from exc
    else:
        raise AssertionError(
            f"ZIG_T5_FALSE_ACCEPT test_id=zig-migration-bridge-t5-exact-physical "
            f"layer=transport fixture={name} fixture_sha256={sha(raw)} "
            "expected=physical_reject actual=accepted first_difference=NA "
            "reproduce='python3 scripts/test_zig_codec_bridge.py'"
        )


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="sens-zig-migration-smoke-") as temp:
        executable = build_transport(Path(temp))
        evidence = verify_t5(executable, GOLDEN_T5)
        expected = hashlib.sha256(GOLDEN_T5).hexdigest()
        binary_sha = sha(executable.read_bytes())
        if (evidence["physical_sha256"] != expected or
                evidence["zig_version"] != "0.16.0" or
                evidence.get("zig_binary_sha256") != binary_sha):
            raise AssertionError(
                f"ZIG_BRIDGE_MISMATCH id=zig-migration-bridge-t5-exact-physical "
                f"layer=transport expected_sha256={expected} actual={evidence}"
            )
        for name, hex_bytes in GOLDEN_WIDTH_VECTORS.items():
            assert_physical_roundtrip(executable, name, bytes.fromhex(hex_bytes))
        for name, hex_bytes in NEGATIVE_PHYSICAL.items():
            assert_physical_rejected(executable, name, bytes.fromhex(hex_bytes))
        # Negative control: a non-Zig program can copy input bytes and exit 0;
        # the bridge must refuse it BEFORE invoking either fake command.
        fake = Path(temp) / "fake-zig"
        fake.write_text(
            '#!/bin/sh\n'
            'if [ "$1" = "t5-coordinates-roundtrip" ]; then cp "$2" "$3"; fi\n'
            'exit 0\n', encoding="utf-8"
        )
        fake.chmod(0o755)
        try:
            verify_t5(fake, GOLDEN_T5)
        except ZigCodecError as exc:
            if "ZIG_CODEC_UNATTESTED_BINARY" not in str(exc):
                raise AssertionError(f"wrong fake binary rejection: {exc}") from exc
        else:
            raise AssertionError("ZIG_CODEC_FAKE_BINARY_RECEIPT accepted foreign executable")

        # A symlink to a genuine build must not silently impersonate it.
        linked = Path(temp) / "linked-zig"
        linked.symlink_to(executable)
        try:
            verify_t5(linked, GOLDEN_T5)
        except ZigCodecError as exc:
            if "ZIG_CODEC_BINARY_NOT_REGULAR" not in str(exc):
                raise AssertionError(f"wrong link rejection: {exc}") from exc
        else:
            raise AssertionError("ZIG_CODEC_LINKED_BINARY_RECEIPT accepted symlink")

        # Linking a DIRECTORY to the already trusted build leaves both the
        # ELF bytes and sha256 unchanged. Never accept this alias as provenance.
        linked_dir = Path(temp) / "linked-build-directory"
        linked_dir.symlink_to(executable.parent, target_is_directory=True)
        redirected = linked_dir / executable.name
        if sha(redirected.read_bytes()) != binary_sha:
            raise AssertionError("ZIG_CODEC_LINKED_PARENT_TEST_FIXTURE_DRIFT")
        try:
            verify_t5(redirected, GOLDEN_T5)
        except ZigCodecError as exc:
            if "ZIG_CODEC_BINARY_NOT_REGULAR" not in str(exc):
                raise AssertionError(f"wrong linked parent rejection: {exc}") from exc
        else:
            raise AssertionError("ZIG_CODEC_LINKED_PARENT_RECEIPT accepted symlink parent")

        # Distinct widths produce distinct canonical bytes, even with a common
        # low-order value. Physical bytes never imply function callability.
        if bytes.fromhex(GOLDEN_WIDTH_VECTORS["d1_one"]) == bytes.fromhex(
            GOLDEN_WIDTH_VECTORS["d2_zero_one"]
        ):
            raise AssertionError("D1_D2_WIDTH_COLLISION")
        # Canonical truncation can become another valid word: D10:0000000000
        # has two physical zero bytes; its one-byte prefix is D5:00000.
        # T5 cannot detect this without a pinned original length + SHA.
        assert_physical_roundtrip(executable, "canonical_d5_prefix_of_d10", b"\x00")

        # Exact ten-bit D10 zero coordinate: TWO 0x00 bytes. This is not an
        # executable D1..D9 word, but migration must preserve its physical bits.
        d10 = bytes([0x00, 0x00])
        proof = verify_t5(executable, d10)
        if proof["physical_sha256"] != hashlib.sha256(d10).hexdigest() or (
            proof["profile"] != "D1-D10_COORDINATES_NOT_EXECUTION"
        ):
            raise AssertionError("D10_COORDINATES_NOT_PRESERVED")
        # Release/migration fail-closed: an EXTERNALLY pinned original D10
        # prevents its valid-but-different one-byte D5 canonical truncation.
        trusted_d10_sha = GOLDEN_D10_ZERO_SHA256
        if sha(d10) != trusted_d10_sha:
            raise AssertionError("ZIG_D10_INDEPENDENT_SOURCE_GOLDEN_DRIFT")
        pinned = verify_t5(
            executable, d10, trusted_source_sha256=trusted_d10_sha
        )
        if pinned.get("source_pin_status") != "MATCHED_CALLER_SUPPLIED_SHA256":
            raise AssertionError("ZIG_EXTERNAL_SOURCE_PIN_NOT_RECORDED")
        if proof.get("source_pin_status") != "NOT_SUPPLIED":
            raise AssertionError("ZIG_EXTERNAL_SOURCE_PIN_INVENTED")
        # The missing executable MUST NOT be examined: reject the altered
        # source before launching or even attesting Zig.
        missing_zig = Path(temp) / "not-a-zig-binary"
        try:
            verify_t5(
                missing_zig, b"\x00", trusted_source_sha256=trusted_d10_sha
            )
        except ZigCodecError as exc:
            if "ZIG_CODEC_EXTERNAL_SOURCE_SHA_MISMATCH" not in str(exc):
                raise AssertionError(f"wrong source-truncation reject: {exc}") from exc
        else:
            raise AssertionError("D10_TO_D5_EXTERNAL_SHA_TRUNCATION_ACCEPTED")
        # Same-length, differently typed canonical words must not alias.
        # D1:1 and D2:01 both occupy ONE physical byte, yet remain distinct.
        d1_one = bytes.fromhex(GOLDEN_WIDTH_VECTORS["d1_one"])
        d2_one = bytes.fromhex(GOLDEN_WIDTH_VECTORS["d2_zero_one"])
        if (len(d1_one) != len(d2_one) or d1_one == d2_one or
                sha(d1_one) != GOLDEN_D1_ONE_SHA256):
            raise AssertionError("ZIG_D1_D2_INDEPENDENT_WIDTH_GOLDEN_DRIFT")
        d1_pinned = verify_t5(
            executable, d1_one, trusted_source_sha256=GOLDEN_D1_ONE_SHA256
        )
        if d1_pinned.get("source_pin_status") != "MATCHED_CALLER_SUPPLIED_SHA256":
            raise AssertionError("ZIG_D1_EXTERNAL_SOURCE_PIN_NOT_RECORDED")
        try:
            verify_t5(
                missing_zig, d2_one,
                trusted_source_sha256=GOLDEN_D1_ONE_SHA256,
            )
        except ZigCodecError as exc:
            diagnostic = str(exc)
            if ("ZIG_CODEC_EXTERNAL_SOURCE_SHA_MISMATCH" not in diagnostic or
                    f"expected_sha256={GOLDEN_D1_ONE_SHA256}" not in diagnostic or
                    f"actual_sha256={sha(d2_one)}" not in diagnostic):
                raise AssertionError(
                    f"wrong D1-to-D2 same-length source reject: {exc}"
                ) from exc
        else:
            raise AssertionError("D1_TO_D2_SAME_LENGTH_EXTERNAL_SHA_ACCEPTED")
        for label, bad_pin in (
            ("empty", ""), ("short", "0" * 63),
            ("uppercase", "A" * 64), ("nonhex", "g" * 64),
        ):
            try:
                verify_t5(
                    missing_zig, d10, trusted_source_sha256=bad_pin
                )
            except ZigCodecError as exc:
                if "ZIG_CODEC_EXTERNAL_SOURCE_SHA_INVALID" not in str(exc):
                    raise AssertionError(
                        f"wrong external SHA format rejection {label}: {exc}"
                    ) from exc
            else:
                raise AssertionError(f"EXTERNAL_SOURCE_SHA_{label}_ACCEPTED")
        d10_path = Path(temp) / "d10.sens"
        d10_path.write_bytes(d10)
        runnable = subprocess.run(
            [str(executable), "t5-check", str(d10_path)],
            capture_output=True, text=True, check=False
        )
        if runnable.returncode == 0:
            raise AssertionError(
                "D10_WRONG_EXECUTION_ADMISSION expected=reject actual=accepted"
            )
        try:
            verify_t5(executable, bytes([0, 0, 0]))  # Unsupported D15.
        except ZigCodecError as exc:
            if "ZIG_CODEC_FAILURE" not in str(exc):
                raise
        else:
            raise AssertionError(
                "OVERWIDTH_COORDINATE_ACCEPTED expected=reject actual=accepted"
            )
        try:
            verify_t5(executable, bytes([255]))  # Outside base-3 T5 byte range.
        except ZigCodecError as exc:
            if "ZIG_CODEC_FAILURE" not in str(exc):
                raise
        else:
            raise AssertionError(
                "ZIG_BRIDGE_INVALID_ACCEPTED id=zig-migration-bridge-t5-exact-physical "
                "layer=transport expected=reject-ff actual=accepted"
            )

        # --- #5812: the corridor MINTS physical bytes; Python is parity only ---
        # Byte-exact against the committed corpus fixture (issue verification #2).
        golden_branch = BRANCH_FIXTURE.with_suffix(".sens").read_bytes()
        branch_view = BRANCH_FIXTURE.read_text(encoding="ascii")
        if sha(golden_branch) != BRANCH_SENS_SHA256:
            raise AssertionError("ZIG_CORRIDOR_MINT_FIXTURE_DRIFT")
        minted = encode_t5(executable, branch_view)
        if minted != golden_branch:
            raise AssertionError(
                f"ZIG_CORRIDOR_MINT_MISMATCH expected_sha256={sha(golden_branch)} "
                f"actual_sha256={sha(minted)} actual_hex={minted.hex()}"
            )
        # The Python codec agrees exactly and is used only as a parity control.
        require_parity(minted, golden_branch)
        try:
            require_parity(minted, bytes([0x00]))
        except ZigCodecError as exc:
            if "ZIG_CODEC_PARITY_MISMATCH" not in str(exc):
                raise AssertionError(f"wrong parity rejection: {exc}") from exc
        else:
            raise AssertionError("ZIG_CODEC_PARITY_MISMATCH_ACCEPTED")
        # The carrier passes width through as opaque payload (no domain decision):
        # an 11-bit token IS minted, but the D1..D10 coordinate check fails closed.
        wide = encode_t5(executable, "11111111111\n")
        if not wide:
            raise AssertionError("ZIG_CORRIDOR_DROPPED_WIDTH_PAYLOAD")
        try:
            verify_t5(executable, wide)
        except ZigCodecError as exc:
            if "ZIG_CODEC_FAILURE" not in str(exc):
                raise AssertionError(f"wrong overwidth corridor reject: {exc}") from exc
        else:
            raise AssertionError("OVERWIDTH_TOKEN_ADMITTED_BY_COORDINATE_CHECK")
        # Non-[01] byte and an empty view fail closed at the corridor boundary.
        for label, bad_view in (("bad_char", "10 x2 00\n"), ("empty", "")):
            try:
                encode_t5(executable, bad_view)
            except ZigCodecError as exc:
                if "ZIG_CODEC_FAILURE" not in str(exc):
                    raise AssertionError(
                        f"wrong corridor input reject {label}: {exc}"
                    ) from exc
            else:
                raise AssertionError(f"ZIG_CORRIDOR_ACCEPTED_BAD_VIEW_{label}")

        # Negative control: modification AFTER Zig built the executable must
        # invalidate the session receipt before executing any byte fixture.
        with executable.open("ab") as stream:
            stream.write(b"\n")
        try:
            verify_t5(executable, GOLDEN_T5)
        except ZigCodecError as exc:
            if "ZIG_CODEC_BINARY_CHANGED" not in str(exc):
                raise AssertionError(f"wrong mutated binary rejection: {exc}") from exc
        else:
            raise AssertionError("ZIG_CODEC_MUTATED_BINARY_RECEIPT accepted changed executable")
    print(f"ZIG_BRIDGE_PASS id=zig-migration-bridge-t5-exact-physical "
          f"layer=transport zig=0.16.0 physical_sha256={expected} "
          "first_difference=NONE malformed_ff=REJECTED d10_transport=ACCEPTED "
          "d10_executable=REJECTED overwidth_d15=REJECTED "
          f"width_goldens={len(GOLDEN_WIDTH_VECTORS)} "
          f"negative_gates={len(NEGATIVE_PHYSICAL) + 11} "
          "external_trusted_sha_d10=INDEPENDENT_GOLDEN "
          "external_trusted_sha_d1=INDEPENDENT_GOLDEN "
          "canonical_d1_to_d2_same_length=REJECTED_WITH_EXTERNAL_PIN "
          "canonical_d10_to_d5_truncation=REJECTED_WITH_EXTERNAL_PIN "
          "corridor_mints_bytes=YES branch_view_byte_exact=YES "
          "python_parity_control=REQUIRED overwidth_passthrough=YES "
          "overwidth_coordinate_check=REJECTED "
          f"zig_binary_sha256={binary_sha} "
          "d1_d2_distinct=YES d2_zero_and_one=YES "
          "canonical_truncation_requires_external_sha=YES "
          "semantic_authority=SENS")


if __name__ == "__main__":
    main()
