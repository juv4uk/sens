#!/usr/bin/env python3
"""One focused real Zig 0.16 migration-bridge test; transport only.

This is not a SENS evaluator or a semantic oracle. No repository files are
rewritten. An invalid T5 octet must be rejected rather than silently decoded.
"""
from __future__ import annotations

import hashlib
import inspect
import os
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

import zig_codec_bridge as bridge
import sens_t5_t5m_codec as t5m_reference

from zig_codec_bridge import (
    ZigCodecError, build_transport, carry_t5 as _carry_t5,
    verify_t5 as _verify_t5, _read_zig_output,
)


def carry_t5(*args, **kwargs):
    """Legacy T5 fixture helper; production bridge defaults to T5M."""
    kwargs.setdefault("codec", "t5")
    return _carry_t5(*args, **kwargs)


def verify_t5(*args, **kwargs):
    """Legacy T5 fixture helper; production bridge defaults to T5M."""
    kwargs.setdefault("codec", "t5")
    return _verify_t5(*args, **kwargs)


def test_default_bridge_codec_is_t5m() -> None:
    assert inspect.signature(_carry_t5).parameters["codec"].default == "t5m"
    assert inspect.signature(_verify_t5).parameters["codec"].default == "t5m"

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


def test_zig_transport_compiles_with_runtime_safety() -> None:
    """Inspect the REAL build_transport command; reject unsafe profile mutants."""
    with tempfile.TemporaryDirectory(prefix="sens-zig-release-safe-") as temp:
        calls: list[list[str]] = []

        def synthesize_binary(argv: list[str]) -> None:
            calls.append(argv)
            outputs = [arg.split("=", 1)[1] for arg in argv
                       if arg.startswith("-femit-bin=")]
            if len(outputs) != 1:
                raise AssertionError("ZIG_SAFE_BUILD_NO_EXACT_OUTPUT")
            Path(outputs[0]).write_bytes(b"synthetic-zig-profile-witness")

        with (patch.object(bridge, "pinned_compiler", return_value="zig-pinned-test"),
              patch.object(bridge, "_command", side_effect=synthesize_binary)):
            binary = bridge.build_transport(Path(temp))
            if not binary.is_file():
                raise AssertionError("ZIG_SAFE_BUILD_MISSING_OUTPUT")
        if len(calls) != 1:
            raise AssertionError("ZIG_SAFE_BUILD_CALL_COUNT")
        command = calls[0]

        def require_safe(argv: list[str]) -> None:
            if (argv[:2] != ["zig-pinned-test", "build-exe"]
                    or argv.count("-O") != 1
                    or argv[argv.index("-O") + 1] != "ReleaseSafe"
                    or "-lc" not in argv
                    or "-fno-stack-check" in argv
                    or "-fno-runtime-safety" in argv):
                raise AssertionError("ZIG_SAFE_BUILD_UNSAFE_PROFILE")

        require_safe(command)
        for label, mutant in (
            ("release-fast", [("ReleaseFast" if x == "ReleaseSafe" else x) for x in command]),
            ("remove-optimization", [x for x in command if x != "ReleaseSafe"]),
            ("disable-stack-check", command + ["-fno-stack-check"]),
        ):
            try:
                require_safe(mutant)
            except AssertionError as error:
                if "ZIG_SAFE_BUILD_UNSAFE_PROFILE" not in str(error):
                    raise
            else:
                raise AssertionError(f"ZIG_SAFE_BUILD_MUTANT_ACCEPTED label={label}")


def test_zig_output_readback_guard() -> None:
    """One transport-only witness: regular accepted; missing/alias rejected."""
    with tempfile.TemporaryDirectory(prefix="sens-zig-output-guard-") as directory:
        root = Path(directory)
        physical = root / "ordinary.sens"
        physical.write_bytes(bytes.fromhex("a1"))
        if _read_zig_output(physical, command="synthetic") != bytes.fromhex("a1"):
            raise AssertionError("ZIG_OUTPUT_READBACK_REGULAR_DRIFT")

        for label, candidate, expected_error in (
            ("missing", root / "missing.sens", "ZIG_CODEC_OUTPUT_UNREADABLE"),
            ("symlink", root / "alias.sens", "ZIG_CODEC_OUTPUT_NOT_REGULAR"),
            ("dangling-symlink", root / "dangling.sens", "ZIG_CODEC_OUTPUT_NOT_REGULAR"),
        ):
            if label in ("symlink", "dangling-symlink"):
                candidate.symlink_to(
                    physical if label == "symlink" else root / "missing-target.sens"
                )
            try:
                _read_zig_output(candidate, command="synthetic")
            except ZigCodecError as error:
                if expected_error not in str(error):
                    raise AssertionError(
                        f"ZIG_OUTPUT_GUARD_WRONG_REJECTION label={label} error={error}"
                    ) from error
            else:
                raise AssertionError(
                    f"ZIG_OUTPUT_GUARD_FALSE_ACCEPT label={label}"
                )

        # Regular same-inode aliases are not freshly produced by Zig.
        alias = root / "hardlink.sens"
        os.link(physical, alias)
        try:
            _read_zig_output(alias, command="synthetic")
        except ZigCodecError as error:
            if "ZIG_CODEC_OUTPUT_LINKED" not in str(error):
                raise AssertionError(f"ZIG_OUTPUT_HARDLINK_WRONG_ERROR {error}") from error
        else:
            raise AssertionError("ZIG_OUTPUT_HARDLINK_FALSE_ACCEPT")
        finally:
            alias.unlink()
        if physical.read_bytes() != bytes.fromhex("a1"):
            raise AssertionError("ZIG_OUTPUT_HARDLINK_SOURCE_CHANGED")

        # lstat() follows a symlink in a PARENT directory; a one-link
        # physical result beneath that alias used to pass the inode guard.
        real_parent = root / "regular-parent"
        real_parent.mkdir()
        nested = real_parent / "proof.sens"
        nested.write_bytes(bytes.fromhex("a1"))
        if _read_zig_output(nested, command="synthetic") != bytes.fromhex("a1"):
            raise AssertionError("ZIG_OUTPUT_REGULAR_PARENT_DRIFT")
        parent_alias = root / "linked-parent"
        parent_alias.symlink_to(real_parent, target_is_directory=True)
        try:
            _read_zig_output(parent_alias / "proof.sens", command="synthetic")
        except ZigCodecError as error:
            if "ZIG_CODEC_OUTPUT_LINKED_PARENT" not in str(error):
                raise AssertionError(f"ZIG_OUTPUT_PARENT_LINK_WRONG_ERROR {error}") from error
        else:
            raise AssertionError("ZIG_OUTPUT_PARENT_LINK_FALSE_ACCEPT")
        if nested.read_bytes() != bytes.fromhex("a1"):
            raise AssertionError("ZIG_OUTPUT_PARENT_LINK_SOURCE_CHANGED")


def main() -> None:
    test_default_bridge_codec_is_t5m()
    test_zig_transport_compiles_with_runtime_safety()
    test_zig_output_readback_guard()
    with tempfile.TemporaryDirectory(prefix="sens-zig-migration-smoke-") as temp:
        executable = build_transport(Path(temp))
        # The unqualified public bridge path must mint and verify T5M bytes.
        t5m_view = "1\n"
        t5m_expected = t5m_reference.encode_t5m_projection(t5m_view)
        t5m_actual = bridge.carry_t5(
            executable, t5m_view,
            trusted_source_sha256=sha(t5m_expected),
        )
        assert t5m_actual == t5m_expected
        t5m_receipt = bridge.verify_t5(
            executable, t5m_actual,
            trusted_source_sha256=sha(t5m_expected),
        )
        assert t5m_receipt["codec"] == "T5M"

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

        # Physical byte authorship belongs to Zig, not the Python parity oracle.
        carry_vectors = {
            "d1_one": ("1" + chr(10), bytes.fromhex("a1")),
            "d2_01": ("01" + chr(10), bytes.fromhex("35")),
            "mixed": ("10 110 00" + chr(10), bytes.fromhex("6738")),
            "d10_coordinate": ("0000000000" + chr(10), bytes.fromhex("0000")),
        }
        for label, (view, expected_physical) in carry_vectors.items():
            actual = carry_t5(executable, view,
                              trusted_source_sha256=sha(expected_physical))
            if actual != expected_physical:
                raise AssertionError(
                    f"ZIG_CARRY_MISMATCH test_id={label} layer=transport "
                    f"expected_sha256={sha(expected_physical)} "
                    f"actual_sha256={sha(actual)} "
                    "reproduce='python3 scripts/test_zig_codec_bridge.py'"
                )
        for malformed in ("", "1", "1" + chr(10) * 2,
                          "1  01" + chr(10), "1" + chr(9) + "01" + chr(10),
                          "102" + chr(10)):
            try:
                carry_t5(executable, malformed)
            except ZigCodecError as exc:
                if "ZIG_CARRY_NONCANONICAL_VIEW" not in str(exc):
                    raise
            else:
                raise AssertionError(f"ZIG_CARRY_INVALID_VIEW_ACCEPTED {malformed!r}")
        for invalid_trits in (b"1022", b"20", b"00000000000", b"12"):
            source = Path(temp) / "invalid.trits"
            output = Path(temp) / "invalid.sens"
            output.unlink(missing_ok=True)
            source.write_bytes(invalid_trits)
            result = subprocess.run(
                [str(executable), "t5-carry", str(source), str(output)],
                capture_output=True, text=True, check=False,
            )
            if result.returncode == 0 or output.exists():
                raise AssertionError(
                    "ZIG_CARRY_FALSE_ACCEPT layer=transport "
                    f"input_sha256={sha(invalid_trits)} "
                    f"status={result.returncode} output_exists={output.exists()}"
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
          f"zig_binary_sha256={binary_sha} "
          "d1_d2_distinct=YES d2_zero_and_one=YES "
          "canonical_truncation_requires_external_sha=YES "
          "semantic_authority=SENS")


if __name__ == "__main__":
    main()
