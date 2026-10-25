#!/usr/bin/env python3
"""Guard: the Rust<->SENS link may cross ONLY the sterile Zig corridor (#5777/#5779).

Fail-closed STRUCTURAL / HOST-NEUTRAL checker. It does not run cargo or Zig.
Scope split with scripts/check_sterile_zig_corridor.py (the source-contract
guard): that guard owns `default=zig-transport`, `build-links-zig`, and the
Rust/C source routes; THIS guard owns the ABI's own purity, the pin, and
host-neutral parity. No rule is enforced only here and also there.

R3  research/zig-codecs/transport_abi.zig: exports ONLY physical `sens_zig_*`
    functions (default T5M + explicit legacy T5 + E1 + F3C physical ops),
    imports ONLY physical codec modules (`std`, t5m.zig, t5/ + f3c/ + transport/)
    and never a registry/host/
    semantic module, and declares no host `extern`/padded structs.
R4  `.zig-version` is a concrete X.Y.Z string (not `latest` or a branch).
R5  HOST-NEUTRAL: every host crosses the SAME corridor. The C header
    research/zig-codecs/host-c/zig_transport_v2.h must declare the same
    physical ops as the Zig ABI (no host-invented ops, no missing ops),
    the ABI version must match, and every Rust-free host in host-c/*.c
    must only call corridor ops (no rogue sens_zig_* invents). At least
    one host must fail-closed reject invalid T5 via F3C pack (...)=-1
    (same physical contract as Rust zig_transport::encode_f3), and must fail the witness if Zig returns anything other than -1.

Exit 0 = CORRIDOR_OK; exit 1 = CORRIDOR_BLOCKED.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ABI = "research/zig-codecs/transport_abi.zig"
ZIGVER = ".zig-version"
C_HEADER = "research/zig-codecs/host-c/zig_transport_v2.h"
C_HOST_DIR = "research/zig-codecs/host-c"

PHYSICAL_IMPORT_PREFIXES = ("t5m.zig", "t5/", "f3c/", "transport/")
FORBIDDEN_IMPORT_RE = re.compile(r"registry|semantic|host|sens", re.I)
REQUIRED_ABI_EXPORTS = (
    "sens_zig_bitpack_fields",
    "sens_zig_t5m_validate",
    "sens_zig_t5m_encode_be3",
    "sens_zig_t5m_decode_be3",
    "sens_zig_t5m_encode_words",
    "sens_zig_t5m_decode_words",
    "sens_zig_t5_validate",
    "sens_zig_t5_encode_be3",
    "sens_zig_t5_decode_be3",
    "sens_zig_e1_encode_be3",
    "sens_zig_e1_decode_be3",
    "sens_zig_f3c_pack",
    "sens_zig_f3c_unpack",
)

# ABI v2 is an *enumerated physical entrypoint surface*, not an open
# "sens_zig_*" namespace for host-assigned semantic registry functions.
# Coordinate-only T5 validation is physical D10 carriage, not execution.
APPROVED_ABI_EXPORTS = frozenset((
    *REQUIRED_ABI_EXPORTS,
    "sens_zig_codec_abi_version",
    "sens_zig_t5_validate_coordinates",
))

EXPORT_RE = re.compile(r"pub export fn\s+([A-Za-z0-9_]+)")
CALL_RE = re.compile(r"\b(sens_zig_[a-z0-9_]+)\s*\(")
# Exclude non-code tokens so strings/comments cannot forge C→Zig call evidence.
C_NONCODE_RE = re.compile(
    r"""//[^\n]*|/\*.*?\*/|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'""",
    re.S,
)

# Guard against ignored Zig return values and C comma-operator false proofs.
# check_number must compare the ABI status with -1 and fail the witness on
# mismatch. C_NONCODE_RE strips comments and string literals before matching.
F3C_FAIL_CLOSED_RE = re.compile(
    r"\bif\s*\(\s*!\s*check_number\s*\(\s*[^,;()]{0,160},\s*"
    r"sens_zig_f3c_pack\s*\([^();]{1,220}\)\s*,\s*-1\s*\)"
    r"\s*\)\s*return\s+0\s*;"
)

ZIG_VERSION_RE = re.compile(r"sens_zig_codec_abi_version\(\)\s*u32\s*\{\s*return\s+(\d+)")
HEADER_VERSION_RE = re.compile(r"SENS_ZIG_TRANSPORT_ABI_VERSION\s*=\s*(\d+)")



def _live_c_code(source: str) -> str:
    """Strip C comments/strings and literal preprocessor-inactive branches.

    This is a conservative structural scan, not a compiler or semantic oracle.
    For unknown #if expressions, keep both branches as possible live code.
    """
    source = C_NONCODE_RE.sub(" ", source)
    stack: list[dict[str, object]] = []
    visible = True
    output: list[str] = []
    for line in source.splitlines(keepends=True):
        match = re.match(r"^\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b(.*)$", line)
        if match:
            op, arg = match.groups()
            literal = arg.strip() if op in ("if", "elif") else ""
            predicate = (literal == "1") if literal in ("0", "1") else None
            if op in ("if", "ifdef", "ifndef"):
                stack.append({"outer": visible, "known": predicate is not None,
                              "taken": predicate is True})
                visible = visible and predicate is not False
            elif op == "elif" and stack:
                frame = stack[-1]
                outer = bool(frame["outer"])
                if frame["known"]:
                    if predicate is None:
                        frame["known"] = False
                        visible = outer and not bool(frame["taken"])
                    else:
                        visible = outer and not bool(frame["taken"]) and predicate
                        frame["taken"] = bool(frame["taken"]) or predicate
                else:
                    visible = outer
            elif op == "else" and stack:
                frame = stack[-1]
                visible = bool(frame["outer"]) and (
                    not bool(frame["taken"]) if frame["known"] else True
                )
                frame["taken"] = True
            elif op == "endif" and stack:
                visible = bool(stack.pop()["outer"])
            output.append("\n")
            continue
        output.append(line if visible else "\n")
    return "".join(output)


def check(root: Path) -> list[str]:
    problems: list[str] = []

    abi = (root / ABI).read_text(encoding="utf-8")
    zigver = (root / ZIGVER).read_text(encoding="utf-8").strip()

    # R3 -- the corridor ABI is physical-only and semantics-free.
    exports = EXPORT_RE.findall(abi)
    if not exports:
        problems.append("R3: transport_abi.zig exports no `pub export fn` (no corridor ABI)")
    for name in exports:
        if name not in APPROVED_ABI_EXPORTS:
            problems.append(
                f"R3: ABI export `{name}` is not an approved ABI v2 physical operation"
            )
    for required in REQUIRED_ABI_EXPORTS:
        if required not in exports:
            problems.append(f"R3: corridor ABI is missing the physical op `{required}`")
    for imported in re.findall(r'@import\("([^"]+)"\)', abi):
        if imported == "std":
            continue
        if FORBIDDEN_IMPORT_RE.search(imported):
            problems.append(
                f"R3: ABI imports `{imported}` -- a semantic/host/registry module "
                "must not cross the sterile corridor"
            )
        elif not any(imported.startswith(p) for p in PHYSICAL_IMPORT_PREFIXES):
            problems.append(
                f"R3: ABI imports `{imported}` -- only physical codec modules "
                f"{list(PHYSICAL_IMPORT_PREFIXES)} may cross the corridor"
            )
    if re.search(r"\bextern\b", abi):
        problems.append(
            "R3: ABI declares `extern`/host struct -- the corridor must use "
            "caller-owned triplets, no padded host structs"
        )

    # R4 -- concrete Zig pin.
    if not re.fullmatch(r"\d+\.\d+\.\d+", zigver):
        problems.append(f"R4: `.zig-version` is not a concrete version string: {zigver!r}")

    # R5 -- host-neutral: every host crosses the SAME corridor.
    header_path = root / C_HEADER
    if not header_path.is_file():
        problems.append(f"R5: C header `{C_HEADER}` is missing (no host-neutral ABI source)")
    else:
        header = header_path.read_text(encoding="utf-8")
        header_ops = set(re.findall(r"\b(sens_zig_[a-z0-9_]+)\s*\(", header))
        header_ops |= set(re.findall(r"\b(sens_zig_[a-z0-9_]+)\s*;", header))
        zig_ops = set(exports)
        missing_in_header = sorted(zig_ops - header_ops)
        extra_in_header = sorted(header_ops - zig_ops - {"sens_zig_codec_abi_version"})
        if "sens_zig_codec_abi_version" in exports and "sens_zig_codec_abi_version" not in header_ops:
            missing_in_header = sorted(set(missing_in_header) | {"sens_zig_codec_abi_version"})
        if missing_in_header:
            problems.append(
                "R5: C header declares fewer ops than the Zig ABI; missing: "
                + ", ".join(missing_in_header)
            )
        if extra_in_header:
            problems.append(
                "R5: C header declares ops not in the Zig ABI (host-invented op): "
                + ", ".join(extra_in_header)
            )
        zig_version = ZIG_VERSION_RE.search(abi)
        hdr_version = HEADER_VERSION_RE.search(header)
        if not zig_version or not hdr_version:
            problems.append("R5: corridor ABI version is not declared on both sides (Zig + C header)")
        elif zig_version.group(1) != hdr_version.group(1):
            problems.append(
                f"R5: ABI version mismatch -- Zig returns {zig_version.group(1)}, "
                f"C header declares {hdr_version.group(1)}"
            )

    host_dir = root / C_HOST_DIR
    if host_dir.is_dir():
        called_physical = False
        physical_exports = set(exports) - {"sens_zig_codec_abi_version"}
        for host in sorted(host_dir.glob("*.c")):
            src = host.read_text(encoding="utf-8")
            src = _live_c_code(src)
            calls = set(CALL_RE.findall(src))
            if not calls:
                continue
            if calls & physical_exports:
                called_physical = True
            rogue = sorted(c for c in calls if c not in set(exports) | {"sens_zig_codec_abi_version"})
            if rogue:
                problems.append(
                    f"R5: host `{host.name}` calls ops outside the corridor: "
                    + ", ".join(rogue)
                )
        if not called_physical:
            problems.append(
                "R5: no Rust-free host in host-c/*.c calls a physical Zig transport op "
                "(version-only and commented calls are not evidence)"
            )

        # R5 F3C fail-closed (G6/G7/S2): require the C host to PROPAGATE
        # the rejected Zig status. In C, a comma operator silently discards
        # the F3C result: if (sens_zig_f3c_pack(...), -1) is not evidence.
        # This regex is only structural; a native C+Zig run is still necessary.
        f3c_invalid_reject = False
        for host in sorted(host_dir.glob("*.c")):
            src = _live_c_code(host.read_text(encoding="utf-8"))
            if F3C_FAIL_CLOSED_RE.search(src):
                f3c_invalid_reject = True
                break
        if not f3c_invalid_reject:
            problems.append(
                "R5: no Rust-free host exercises F3C pack rejection of invalid T5 "
                "(required: if (!check_number(..., sens_zig_f3c_pack(...), -1)) "
                "return 0; a comma/ignored result is not evidence)"
            )

    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    problems = check(root)
    if problems:
        print("CORRIDOR_BLOCKED:", file=sys.stderr)
        for item in problems:
            print(f"  - {item}", file=sys.stderr)
        return 1
    print(
        "CORRIDOR_OK Rust<->SENS crosses only the sterile Zig corridor "
        "(physical-only ABI, pinned corridor, host-neutral; default/build are the sterile guard's)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
