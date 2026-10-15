"""Fail-closed declaration parity for the sterile Zig ABI v2 corridor.

This is source/FFI contract evidence only, not SENS semantic authority,
physical byte parity, a native Zig build, or independent execution.
No new workflow: existing Python discovery may run this focused guard.
"""

import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZIG_PATH = ROOT / "research/zig-codecs/transport_abi.zig"
RUST_PATH = ROOT / "crates/sens-cli/src/zig_transport.rs"
C_PATH = ROOT / "research/zig-codecs/host-c/zig_transport_v2.h"
H2_C_PATH = ROOT / "research/zig-codecs/host-c/h2_t5_dump.c"

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



def strip_c_comments(source: str) -> str:
    """Remove // and /* */ without allowing comment-only ABI declarations.

    Preserve newlines for ^-anchored declaration matching and quoted strings
    (for example, a URL containing // is not a source comment). This is a
    lexical source guard, not a substitute for native compiler/linker evidence.
    """
    out = []
    index = 0
    mode = "code"
    while index < len(source):
        ch = source[index]
        nxt = source[index + 1] if index + 1 < len(source) else ""
        if mode == "code":
            if ch == '"':
                mode = "string"
                out.append(ch)
            elif ch == "/" and nxt in "/*":
                mode = "line" if nxt == "/" else "block"
                out.extend("  ")
                index += 2
                continue
            else:
                out.append(ch)
        elif mode == "string":
            out.append(ch)
            if ch == "\\" and nxt:
                out.append(nxt)
                index += 2
                continue
            if ch == '"':
                mode = "code"
        elif mode == "line":
            if ch == "\n":
                mode = "code"
                out.append("\n")
            else:
                out.append(" ")
        else:
            if ch == "*" and nxt == "/":
                mode = "code"
                out.extend("  ")
                index += 2
                continue
            out.append("\n" if ch == "\n" else " ")
        index += 1
    return "".join(out)


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


def compiled_c_declarations(header: str) -> dict:
    """The C preprocessor, not source regex, decides the active Zig ABI surface.

    No library links and no SENS semantic interpretation: this is the
    physically visible declaration contract under the existing C11 toolchain.
    """
    cc = shutil.which("cc")
    if cc is None:
        fail("toolchain", "missing_cc_for_preprocessed_abi")
    try:
        result = subprocess.run(
            [cc, "-std=c11", "-E", "-P", "-x", "c", "-"],
            input=header, text=True, capture_output=True, cwd=ROOT,
            check=False, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        fail("toolchain", f"preprocess_unavailable={type(exc).__name__}")
    if result.returncode != 0:
        fail("c", f"preprocess_failed_exit={result.returncode} stderr={result.stderr[-800:]}")
    return declarations(result.stdout, "c")


def check_contract(zig: str, rust: str, header: str) -> None:
    zig, rust, header = (strip_c_comments(source) for source in (zig, rust, header))
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



def check_h2_host_contract(source: str) -> None:
    """Only the canonical Zig v2 header may define H2 C-host declarations."""
    clean = strip_c_comments(source)
    if not re.search(r'(?m)^[ \t]*#[ \t]*include[ \t]+"zig_transport_v2\.h"[ \t]*$', clean):
        fail("h2-c", "missing_canonical_zig_header")
    if re.search(
        r"\bextern\s+(?:uint32_t|int|ptrdiff_t)\s+sens_zig_[a-z0-9_]+\s*\(",
        clean,
    ):
        fail("h2-c", "shadow_zig_abi_declaration")
    if not re.search(
        r"\bsens_zig_codec_abi_version\(\)\s*!=\s*SENS_ZIG_TRANSPORT_ABI_VERSION\b",
        clean,
    ):
        fail("h2-c", "noncanonical_abi_version_check")


class ZigAbiV2DeclarationContractTest(unittest.TestCase):
    def test_h2_c_host_uses_only_shared_zig_v2_header(self):
        source = H2_C_PATH.read_text(encoding="utf-8")
        check_h2_host_contract(source)

    def test_h2_c_host_rejects_shadow_extern_prototype(self):
        source = H2_C_PATH.read_text(encoding="utf-8")
        mutant = source + "\nextern ptrdiff_t sens_zig_t5_encode_be3(" \
            "const uint8_t *src, size_t len, uint8_t *dst, size_t cap);\n"
        with self.assertRaisesRegex(ValueError, "shadow_zig_abi_declaration"):
            check_h2_host_contract(mutant)

    def test_h2_c_host_rejects_missing_shared_header(self):
        source = H2_C_PATH.read_text(encoding="utf-8")
        mutant = source.replace(
            '#include "zig_transport_v2.h"', '#include <stdint.h>', 1,
        )
        self.assertNotEqual(mutant, source)
        with self.assertRaisesRegex(ValueError, "missing_canonical_zig_header"):
            check_h2_host_contract(mutant)

    def test_h2_c_host_rejects_literal_abi_version(self):
        source = H2_C_PATH.read_text(encoding="utf-8")
        mutant = source.replace(
            "!= SENS_ZIG_TRANSPORT_ABI_VERSION", "!= 2u", 1,
        )
        self.assertNotEqual(mutant, source)
        with self.assertRaisesRegex(ValueError, "noncanonical_abi_version_check"):
            check_h2_host_contract(mutant)

    def test_h2_c_host_compiles_c11_with_shared_zig_abi_header(self):
        compiler = shutil.which("cc")
        self.assertIsNotNone(compiler, "ZIG_ABI_V2_DRIFT layer=toolchain missing=cc")
        result = subprocess.run(
            [compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
             "-fsyntax-only", str(H2_C_PATH)],
            cwd=ROOT, capture_output=True, text=True, timeout=30, check=False,
        )
        self.assertEqual(
            result.returncode, 0,
            "ZIG_ABI_V2_DRIFT layer=h2-c reason=compile_shared_abi "
            f"returncode={result.returncode} stderr={result.stderr}",
        )

    @classmethod
    def setUpClass(cls):
        cls.zig = ZIG_PATH.read_text(encoding="utf-8")
        cls.rust = RUST_PATH.read_text(encoding="utf-8")
        cls.header = C_PATH.read_text(encoding="utf-8")

    def test_preprocessed_c11_abi_matches_zig_and_rejects_if0_ghost(self):
        """A C prototype hidden under #if 0 must never count as Zig ABI v2."""
        visible = compiled_c_declarations(self.header)
        self.assertEqual(visible, declarations(strip_c_comments(self.header), "c"))
        self.assertEqual(visible, declarations(strip_c_comments(self.zig), "zig"))
        self.assertEqual(visible, declarations(strip_c_comments(self.rust), "rust"))

        # A source-only regex sees this prototype, but C11 does NOT.
        match = re.search(
            r"(?ms)^ptrdiff_t sens_zig_f3c_unpack\\([^;]*?;", self.header,
        )
        self.assertIsNotNone(match, "canonical C F3C prototype missing")
        original = match.group(0)
        mutant = self.header.replace(
            original, "#if 0\n" + original + "\n#endif", 1,
        )
        self.assertNotEqual(mutant, self.header)
        self.assertEqual(
            declarations(strip_c_comments(mutant), "c"),
            declarations(strip_c_comments(self.header), "c"),
            "precondition: raw source guard must still see ghost declaration",
        )
        with self.assertRaisesRegex(
            ValueError, r"missing_or_duplicate=sens_zig_f3c_unpack",
        ):
            compiled_c_declarations(mutant)

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


    def test_zig_export_hidden_in_block_comment_does_not_count(self):
        match = re.search(
            r"(?ms)^pub export fn sens_zig_t5_decode_be3\(.*?^\}",
            self.zig,
        )
        self.assertIsNotNone(match)
        original = match.group(0)
        mutated = self.zig.replace(original, "/*\n" + original + "\n*/", 1)
        # The historical regex alone would see this ghost signature.
        self.assertIsNotNone(ZIG_DECL.search(mutated))
        with self.assertRaisesRegex(ValueError, "missing_or_duplicate=sens_zig_t5_decode_be3"):
            check_contract(mutated, self.rust, self.header)

    def test_rust_version_check_hidden_in_comment_does_not_count(self):
        match = re.search(
            r"if\s+unsafe\s*\{\s*sens_zig_codec_abi_version\(\)\s*\}"
            r"\s*!=\s*2\b",
            self.rust,
        )
        self.assertIsNotNone(match)
        mutated = self.rust.replace(match.group(0), "/* " + match.group(0) + " */", 1)
        with self.assertRaisesRegex(ValueError, "version_check_not_fail_closed"):
            check_contract(self.zig, mutated, self.header)

    def test_c_header_prototype_hidden_in_line_comment_does_not_count(self):
        match = re.search(
            r"(?ms)^ptrdiff_t sens_zig_f3c_unpack\([^;]*?;",
            self.header,
        )
        self.assertIsNotNone(match)
        prototype = match.group(0)
        # Comment every line so even a multiline declaration is not visible.
        mutated = self.header.replace(
            prototype, "".join("// " + line for line in prototype.splitlines(True)), 1,
        )
        with self.assertRaisesRegex(ValueError, "missing_or_duplicate=sens_zig_f3c_unpack"):
            check_contract(self.zig, self.rust, mutated)

    def test_c_header_version_hidden_in_comment_does_not_count(self):
        marker = "SENS_ZIG_TRANSPORT_ABI_VERSION = 2"
        self.assertIn(marker, self.header)
        mutated = self.header.replace(marker, "/* " + marker + " */", 1)
        with self.assertRaisesRegex(ValueError, "header_version_not_2"):
            check_contract(self.zig, self.rust, mutated)

    def test_comment_markers_inside_quoted_string_are_not_comments(self):
        source = 'const uri = "https://example.test/a/*still-string*/";\n'
        self.assertEqual(strip_c_comments(source), source)



if __name__ == "__main__":
    unittest.main()
