"""Fail-closed declaration parity for the sterile Zig ABI v2 corridor.

This is source/FFI contract evidence only, not SENS semantic authority,
physical byte parity, a native Zig build, or independent execution.
No new workflow: existing Python discovery may run this focused guard.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZIG_PATH = ROOT / "research/zig-codecs/transport_abi.zig"
RUST_PATH = ROOT / "crates/sens-cli/src/zig_transport.rs"
C_PATH = ROOT / "research/zig-codecs/host-c/zig_transport_v2.h"

# No semantic function identities, domain numbers, or host-specific layouts:
# these are the eight existing *physical* ABI v2 functions only.
EXPECTED = {
    "sens_zig_codec_abi_version": ((), "version"),
    "sens_zig_t5_validate": (("source", "length"), "status"),
    "sens_zig_t5_encode_be3": (("source", "length", "destination", "length"), "size"),
    "sens_zig_t5_decode_be3": (("source", "length", "destination", "length"), "size"),
    "sens_zig_e1_encode_be3": (("source", "length", "destination", "length"), "size"),
    "sens_zig_e1_decode_be3": (("source", "length", "destination", "length"), "size"),
    "sens_zig_f3c_pack": (("source", "length", "destination", "length"), "size"),
    "sens_zig_f3c_unpack": (("source", "length", "destination", "length"), "size"),
}
ZIG_DECL = re.compile(
    r"(?m)^[ \t]*pub[ \t]+export[ \t]+fn[ \t]+"
    r"(?P<name>sens_zig_[a-z0-9_]+)\s*\((?P<args>[^)]*)\)\s*"
    r"(?P<return>u32|c_int|isize)\s*\{"
)
RUST_DECL = re.compile(
    r"(?m)^[ \t]*fn[ \t]+(?P<name>sens_zig_[a-z0-9_]+)"
    r"\s*\((?P<args>[^)]*)\)\s*->\s*(?P<return>u32|i32|isize)\s*;"
)
C_DECL = re.compile(
    r"(?m)^[ \t]*(?P<return>uint32_t|int|ptrdiff_t)[ \t]+"
    r"(?P<name>sens_zig_[a-z0-9_]+)\s*\((?P<args>[^;]*?)\)\s*;"
)
RETURN_TYPES = {
    "zig": {"u32": "version", "c_int": "status", "isize": "size"},
    "rust": {"u32": "version", "i32": "status", "isize": "size"},
    "c": {"uint32_t": "version", "int": "status", "ptrdiff_t": "size"},
}


def fail(layer: str, reason: str) -> None:
    raise ValueError(f"ZIG_ABI_V2_DRIFT layer={layer} reason={reason}")


def parameter_role(text: str, language: str) -> str:
    item = " ".join(text.strip().split())
    if language in {"zig", "rust"}:
        if ":" not in item:
            fail(language, f"unnamed_parameter={item}")
        item = item.split(":", 1)[1].strip()
        return {
            "[*]const u8": "source",
            "*const u8": "source",
            "[*]u8": "destination",
            "*mut u8": "destination",
            "usize": "length",
        }.get(item, f"unknown_type={item}")
    if re.fullmatch(r"const uint8_t\s*\*\s*[a-z_][a-z0-9_]*", item):
        return "source"
    if re.fullmatch(r"uint8_t\s*\*\s*[a-z_][a-z0-9_]*", item):
        return "destination"
    if re.fullmatch(r"size_t\s+[a-z_][a-z0-9_]*", item):
        return "length"
    return f"unknown_type={item}"


def declarations(source: str, language: str) -> dict:
    pattern = {"zig": ZIG_DECL, "rust": RUST_DECL, "c": C_DECL}[language]
    found = {}
    for match in pattern.finditer(source):
        name = match.group("name")
        raw = match.group("args").strip()
        if not raw or raw == "void":
            parts = []
        else:
            parts = [part.strip() for part in raw.split(",")]
            # Zig allows a trailing comma in a multiline argument list.
            # Ignore that single separator, not empty parameters in the middle.
            if parts[-1] == "":
                parts.pop()
            if not parts or any(not part for part in parts):
                fail(language, f"empty_parameter={name}")
        args = tuple(parameter_role(part, language) for part in parts)
        result = RETURN_TYPES[language][match.group("return")]
        found.setdefault(name, []).append((args, result))
    for name, expected in EXPECTED.items():
        if len(found.get(name, ())) != 1:
            fail(language, f"missing_or_duplicate={name} count={len(found.get(name, ()))}")
        if found[name][0] != expected:
            fail(
                language,
                f"signature={name} expected={expected} actual={found[name][0]}",
            )
    unexpected = sorted(set(found) - set(EXPECTED))
    if unexpected:
        fail(language, f"unreviewed_exports={','.join(unexpected)}")
    return {name: found[name][0] for name in EXPECTED}


def check_contract(zig: str, rust: str, header: str) -> None:
    if 'unsafe extern "C" {' not in rust:
        fail("rust", "missing_C_abi_linkage")
    if 'extern "C" {' not in header:
        fail("c", "missing_C_plus_plus_linkage")
    if not re.search(
        r"pub export fn sens_zig_codec_abi_version\(\) u32"
        r"\s*\{\s*return 2;\s*\}",
        zig,
    ):
        fail("zig", "version_not_exactly_2")
    if not re.search(
        r"if\s+unsafe\s*\{\s*sens_zig_codec_abi_version\(\)\s*\}"
        r"\s*!=\s*2\b",
        rust,
    ):
        fail("rust", "version_check_not_fail_closed")
    if not re.search(r"\bSENS_ZIG_TRANSPORT_ABI_VERSION\s*=\s*2\b", header):
        fail("c", "header_version_not_2")
    declared = declarations(zig, "zig")
    if declarations(rust, "rust") != declared:
        fail("rust", "signature_set_differs_from_zig")
    if declarations(header, "c") != declared:
        fail("c", "signature_set_differs_from_zig")


class ZigAbiV2DeclarationContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.zig = ZIG_PATH.read_text(encoding="utf-8")
        cls.rust = RUST_PATH.read_text(encoding="utf-8")
        cls.header = C_PATH.read_text(encoding="utf-8")

    def test_current_zig_rust_c_physical_signatures_agree(self):
        check_contract(self.zig, self.rust, self.header)

    def test_missing_zig_export_is_rejected(self):
        mutated = self.zig.replace(
            "pub export fn sens_zig_t5_decode_be3",
            "fn sens_zig_t5_decode_be3",
            1,
        )
        self.assertNotEqual(mutated, self.zig)
        with self.assertRaisesRegex(ValueError, "missing_or_duplicate=sens_zig_t5_decode_be3"):
            check_contract(mutated, self.rust, self.header)

    def test_missing_rust_ingress_is_rejected(self):
        mutated = self.rust.replace(
            "fn sens_zig_e1_decode_be3", "fn no_e1_decode_be3", 1
        )
        self.assertNotEqual(mutated, self.rust)
        with self.assertRaisesRegex(ValueError, "missing_or_duplicate=sens_zig_e1_decode_be3"):
            check_contract(self.zig, mutated, self.header)

    def test_wrong_c_ffi_return_type_is_rejected(self):
        mutated = self.header.replace(
            "ptrdiff_t sens_zig_f3c_unpack", "int sens_zig_f3c_unpack", 1
        )
        self.assertNotEqual(mutated, self.header)
        with self.assertRaisesRegex(ValueError, "signature=sens_zig_f3c_unpack"):
            check_contract(self.zig, self.rust, mutated)

    def test_wrong_rust_pointer_constness_is_rejected(self):
        mutated = self.rust.replace(
            "input: *const u8, len: usize",
            "input: *mut u8, len: usize",
            1,
        )
        self.assertNotEqual(mutated, self.rust)
        with self.assertRaisesRegex(ValueError, "signature=sens_zig_t5_validate"):
            check_contract(self.zig, mutated, self.header)

    def test_zig_version_drift_is_rejected(self):
        mutated = self.zig.replace(
            "sens_zig_codec_abi_version() u32 { return 2; }",
            "sens_zig_codec_abi_version() u32 { return 3; }",
            1,
        )
        self.assertNotEqual(mutated, self.zig)
        with self.assertRaisesRegex(ValueError, "version_not_exactly_2"):
            check_contract(mutated, self.rust, self.header)

    def test_unreviewed_new_zig_export_is_rejected(self):
        mutated = self.zig + (
            "\npub export fn sens_zig_unreviewed() u32 { return 2; }\n"
        )
        with self.assertRaisesRegex(ValueError, "unreviewed_exports=sens_zig_unreviewed"):
            check_contract(mutated, self.rust, self.header)


if __name__ == "__main__":
    unittest.main()
