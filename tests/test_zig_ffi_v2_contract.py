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
ASSET_ZIG_PATH = ROOT / "zig_transport_root.zig"
ASSET_RUST_PATH = ROOT / "crates/sens-cli/src/zig_transport_assets.rs"

# No semantic function identities, domain numbers, or host-specific layouts:
# ten reviewed *physical* ABI v2 functions; D10 validator is coordinate-only.
EXPECTED = {
    "sens_zig_codec_abi_version": ((), "version"),
    "sens_zig_bitpack_fields": (("source", "length", "destination", "length"), "size"),
    "sens_zig_t5_validate": (("source", "length"), "status"),
    # Reviewed #5777: physical D1..D10 coordinate profile (NO execution).
    "sens_zig_t5_validate_coordinates": (("source", "length"), "status"),
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



# Root Zig source asset-copy exports are NOT codec ABI v2. Keep the
# inventories exact: adding an unreviewed FFI declaration cannot silently
# expand the physical nine-function v2 contract.
ASSET_NAMES = ("sens_zig_linter_bytes_copy", "sens_zig_contract_bytes_copy", "sens_zig_sanskrit_bytes_copy", "sens_zig_ukr_bytes_copy", "sens_zig_uk_bytes_copy", "sens_zig_islands_manifest_bytes_copy", "sens_zig_uk_docs_bytes_copy", "sens_zig_unify_bytes_copy", "sens_zig_reason_bytes_copy", "sens_zig_forward_bytes_copy", "sens_zig_knowledge_bytes_copy", "sens_zig_persistent_map_bytes_copy", "sens_zig_world_bytes_copy", "sens_zig_content_store_bytes_copy", "sens_zig_lisp_fs_bytes_copy")
REPL_LOCAL_NAMES = ("sens_zig_repl_persistent_vector_bytes_copy", "sens_zig_repl_time_bytes_copy", "sens_zig_repl_epistemic_bytes_copy")
LIVE_FILE_NAMES = ("sens_zig_guard_reference_bytes_copy",)
ASSET_ZIG_EXPORT = re.compile(
    r"(?m)^[ \t]*pub[ \t]+export[ \t]+fn[ \t]+"
    r"(sens_zig_[a-z0-9_]+)\s*\(([^)]*)\)\s*isize\s*\{"
)
ASSET_RUST_DECL = re.compile(
    r"(?m)^[ \t]*pub\(super\)[ \t]+fn[ \t]+"
    r"(sens_zig_[a-z0-9_]+)\s*\(([^)]*)\)\s*->\s*isize\s*;"
)


def check_root_asset_corridor(
    zig_root: str, rust_assets: str, rust_transport: str,
    repl_source: str | None = None,
) -> None:
    """Exact external byte-copy signatures without pretending they are ABI v2.

    Does not validate Lisp semantics or classify source/domain identities.
    Rejects ghost comments, swapped pointer constness, unreviewed exports,
    missing linkage and Rust-side project-source embedding.
    """
    zig_root, rust_assets, rust_transport = (
        strip_c_comments(source) for source in (zig_root, rust_assets, rust_transport)
    )
    if '#[path = "zig_transport_assets.rs"]' not in rust_transport or not re.search(
        r"(?m)^mod\s+asset_ffi\s*;", rust_transport
    ):
        fail("asset-rust", "missing_root_asset_adapter")
    if 'unsafe extern "C" {' not in rust_assets:
        fail("asset-rust", "missing_C_linkage")
    for name, asset in (
        ("sens_zig_linter_bytes_copy", "lib/linter.lisp"),
        ("sens_zig_contract_bytes_copy", "language-contract.lisp"),
        ("sens_zig_sanskrit_bytes_copy", "lib/surface/sa.lisp"),
        ("sens_zig_ukr_bytes_copy", "lib/surface/ukr.lisp"),
        ("sens_zig_uk_bytes_copy", "lib/surface/uk.lisp"),
        ("sens_zig_islands_manifest_bytes_copy", "packaging/islands-manifest-v1.json"),
        ("sens_zig_uk_docs_bytes_copy", "lib/surface/uk-docs.lisp"),
        ("sens_zig_unify_bytes_copy", "lib/unify.lisp"),
        ("sens_zig_reason_bytes_copy", "lib/reason.lisp"),
        ("sens_zig_forward_bytes_copy", "lib/forward.lisp"),
        ("sens_zig_knowledge_bytes_copy", "lib/knowledge.lisp"),
        ("sens_zig_persistent_map_bytes_copy", "lib/persistent-map.lisp"),
        ("sens_zig_world_bytes_copy", "lib/world.lisp"),
        ("sens_zig_content_store_bytes_copy", "lib/content-store.lisp"),
        ("sens_zig_lisp_fs_bytes_copy", "lib/lisp-fs.lisp"),
    ):
        expected_embed = f'@embedFile("{asset}")'
        if expected_embed not in zig_root:
            fail("asset-zig", f"missing_opaque_embed={asset}")
        # Exact 2-call handshake: size query (capacity=0) then checked copy.
        # A surviving second call must not hide a deleted first call.
        if rust_transport.count(f"asset_ffi::{name}(") != 2:
            fail("asset-rust", f"missing_opaque_call={name}")

    # Bind each reviewed export to its one source. A declaration-only guard
    # would miss accidental asset cross-wiring while the ABI stays unchanged.
    # This is exact-byte transport evidence, never a SENS semantic verdict.
    for name, asset, binding in (
        ("sens_zig_linter_bytes_copy", "lib/linter.lisp", "linter_asset"),
        ("sens_zig_contract_bytes_copy", "language-contract.lisp", "contract_asset"),
        ("sens_zig_sanskrit_bytes_copy", "lib/surface/sa.lisp", "sanskrit_asset"),
        ("sens_zig_ukr_bytes_copy", "lib/surface/ukr.lisp", "ukr_asset"),
        ("sens_zig_uk_bytes_copy", "lib/surface/uk.lisp", "uk_asset"),
        ("sens_zig_islands_manifest_bytes_copy", "packaging/islands-manifest-v1.json", "islands_manifest_asset"),
        ("sens_zig_uk_docs_bytes_copy", "lib/surface/uk-docs.lisp", "uk_docs_asset"),
        ("sens_zig_unify_bytes_copy", "lib/unify.lisp", "unify_asset"),
        ("sens_zig_reason_bytes_copy", "lib/reason.lisp", "reason_asset"),
        ("sens_zig_forward_bytes_copy", "lib/forward.lisp", "forward_asset"),
        ("sens_zig_knowledge_bytes_copy", "lib/knowledge.lisp", "knowledge_asset"),
        ("sens_zig_persistent_map_bytes_copy", "lib/persistent-map.lisp", "persistent_map_asset"),
        ("sens_zig_world_bytes_copy", "lib/world.lisp", "world_asset"),
        ("sens_zig_content_store_bytes_copy", "lib/content-store.lisp", "content_store_asset"),
        ("sens_zig_lisp_fs_bytes_copy", "lib/lisp-fs.lisp", "lisp_fs_asset"),
    ):
        const_line = f'const {binding} = @embedFile("{asset}");'
        if len(re.findall(r"(?m)^[ \t]*" + re.escape(const_line) + r"[ \t]*$", zig_root)) != 1:
            fail("asset-zig", f"wrong_asset_binding={name} expected={asset}")
        pattern = (
            r"(?ms)^[ \t]*pub export fn " + re.escape(name)
            + r"\(dst: \[\*\]u8, capacity: usize\) isize \{(?P<body>.*?)^[ \t]*\}"
        )
        match = re.search(pattern, zig_root)
        if match is None:
            fail("asset-zig", f"missing_copy_body={name}")
        expected_body = " ".join((
            f"if ({binding}.len == 0) return -1;",
            f"if (capacity == 0) return @intCast({binding}.len);",
            f"if (capacity < {binding}.len) return -2;",
            f"@memcpy(dst[0..{binding}.len], {binding}[0..{binding}.len]);",
            f"return @intCast({binding}.len);",
        ))
        actual_body = " ".join(match.group("body").split())
        if actual_body != expected_body:
            first = next(
                (i for i, (left, right) in enumerate(zip(expected_body, actual_body))
                 if left != right),
                min(len(expected_body), len(actual_body)),
            )
            fail("asset-zig", f"wrong_copy_body={name} first_mismatch={first} "
                 "path=zig_transport_root.zig "
                 "repro='python3 -m unittest discover -s tests -p test_zig_ffi_v2_contract.py'")


    # REPL source files are separate byte carriers, not new codec ABI-v2
    # functions. The guard-reference file is a dynamic runtime read and has a
    # separately reviewed contract below; it is not an embedded asset.
    reviewed_sources = (
        ("sens_zig_repl_core_bytes_copy", "lib/repl-core.lisp", "repl_core_asset"),
        ("sens_zig_meta_eval_bytes_copy", "lib/meta-eval.lisp", "meta_eval_asset"),
    )
    for name, asset, binding in reviewed_sources:
        const = f'const {binding} = @embedFile("{asset}");'
        if len(re.findall(r"(?m)^[ \t]*" + re.escape(const) + r"[ \t]*$", zig_root)) != 1:
            fail("asset-zig", f"wrong_asset_binding={name} expected={asset}")
        pattern = (
            r"(?ms)^[ \t]*pub export fn " + re.escape(name)
            + r"\(dst: \[\*\]u8, capacity: usize\) isize \{(?P<body>.*?)^[ \t]*\}"
        )
        match = re.search(pattern, zig_root)
        if match is None:
            fail("asset-zig", f"missing_copy_body={name}")
        expected = " ".join((
            f"if ({binding}.len == 0) return -1;",
            f"if (capacity == 0) return @intCast({binding}.len);",
            f"if (capacity < {binding}.len) return -2;",
            f"@memcpy(dst[0..{binding}.len], {binding}[0..{binding}.len]);",
            f"return @intCast({binding}.len);",
        ))
        if " ".join(match.group("body").split()) != expected:
            fail("asset-zig", f"wrong_copy_body={name}")

    # The Rust host can request unmodified bytes. It must not synthesize a
    # registry, reinterpret a width, or bypass length checking on the copy.
    if not re.search(
        r"(?s)pub fn repl_core_source_bytes\(\) -> Result<Vec<u8>, String> \{\s*"
        r'opaque_zig_asset\(asset_ffi::sens_zig_repl_core_bytes_copy, "ZIG_SENS_REPL"\)\s*\}',
        rust_transport,
    ):
        fail("asset-rust", "missing_repl_core_carrier")
    shared_start = rust_transport.find("fn opaque_zig_asset(")
    shared_end = rust_transport.find("\npub fn repl_core_source_bytes()", shared_start)
    shared = rust_transport[shared_start:shared_end] if shared_start >= 0 and shared_end > shared_start else ""
    if not all(token in shared for token in (
        "version()?;", "copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)",
        "copy(bytes.as_mut_ptr(), len)", "if copied != required", "Ok(bytes)",
    )):
        fail("asset-rust", "missing_shared_opaque_byte_guard")
    guard_source = re.search(
        r"(?s)pub fn guard_reference_source_bytes\(\) -> Result<Vec<u8>, String> \{"
        r"(?P<body>.*?)\n\}",
        rust_transport,
    )
    if guard_source is None or not all(token in guard_source.group("body") for token in (
        "opaque_zig_asset(", "asset_ffi::sens_zig_guard_reference_bytes_copy",
        '"ZIG_GUARD_REFERENCE"',
    )):
        fail("asset-rust", "missing_guard_reference_carrier")
    guard_export = re.search(
        r"(?ms)^[ \t]*pub export fn sens_zig_guard_reference_bytes_copy"
        r"\(dst: \[\*\]u8, capacity: usize\) isize \{(?P<body>.*?)^[ \t]*\}",
        zig_root,
    )
    if guard_export is None:
        fail("asset-zig", "missing_guard_reference_dynamic_export")
    guard_body = " ".join(guard_export.group("body").split())
    if not all(token in zig_root for token in (
        '"knowledge/guard-reference.lisp"', '"../../knowledge/guard-reference.lisp"',
    )) or not all(token in guard_body for token in (
        "fopen(", "fseek(", "ftell(", "guard_reference_read_limit",
        "fread(", "fclose(", "@memcpy(dst[0..len], temporary)",
    )):
        fail("asset-zig", "incomplete_guard_reference_bounded_reader")
    if "const guard_reference_read_limit: usize = 8 * 1024 * 1024;" not in zig_root:
        fail("asset-zig", "wrong_guard_reference_read_limit")
    if '@embedFile("knowledge/guard-reference.lisp")' in zig_root:
        fail("asset-zig", "guard_reference_must_remain_dynamic")

    repl_source = strip_c_comments(
        (ROOT / "crates/sens-cli/src/repl.rs").read_text(encoding="utf-8")
        if repl_source is None else repl_source
    )
    for name in ("sens_zig_meta_eval_bytes_copy",):
        if repl_source.count(f"fn {name}(dst: *mut u8, cap: usize) -> isize;") != 1:
            fail("repl-rust", f"missing_meta_ffi={name}")
        if repl_source.count(f"repl_zig_source({name},") != 1:
            fail("repl-rust", f"missing_meta_live_copy={name}")

    expected_zig = "dst: [*]u8, capacity: usize"
    expected_rust = "output: *mut u8, capacity: usize"
    for source, matcher, expected, layer in (
        (zig_root, ASSET_ZIG_EXPORT, expected_zig, "asset-zig"),
        (rust_assets, ASSET_RUST_DECL, expected_rust, "asset-rust"),
    ):
        entries = {}
        for match in matcher.finditer(source):
            entries.setdefault(match.group(1), []).append(
                " ".join(match.group(2).split())
            )
        reviewed_extra = ({name for name, _, _ in reviewed_sources} | set(LIVE_FILE_NAMES)
                          if layer == "asset-zig" else
                          {"sens_zig_repl_core_bytes_copy"} | set(LIVE_FILE_NAMES))
        extra = sorted(set(entries) - set(ASSET_NAMES) - reviewed_extra
                       - (set(REPL_LOCAL_NAMES) if layer == "asset-zig" else set()))
        if extra:
            fail(layer, f"unreviewed_asset_exports={','.join(extra)}")
        for name in ASSET_NAMES:
            actual = entries.get(name, [])
            if actual != [expected]:
                fail(layer, f"asset_signature={name} expected={expected} actual={actual!r}")

        reviewed_signatures = (
            {
                "sens_zig_repl_core_bytes_copy": expected_zig,
                "sens_zig_meta_eval_bytes_copy": expected_zig,
            } if layer == "asset-zig" else {
                "sens_zig_repl_core_bytes_copy": expected_rust,
            }
        )
        if layer == "asset-zig":
            reviewed_signatures[LIVE_FILE_NAMES[0]] = expected_zig
        else:
            reviewed_signatures[LIVE_FILE_NAMES[0]] = expected_rust
        for name, signature in reviewed_signatures.items():
            actual = entries.get(name, [])
            if actual != [signature]:
                fail(layer, f"asset_signature={name} expected={signature} actual={actual!r}")


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
        cls.asset_zig = ASSET_ZIG_PATH.read_text(encoding="utf-8")
        cls.asset_rust = ASSET_RUST_PATH.read_text(encoding="utf-8")

    def test_preprocessed_c11_abi_matches_zig_and_rejects_if0_ghost(self):
        """A C prototype hidden under #if 0 must never count as Zig ABI v2."""
        visible = compiled_c_declarations(self.header)
        self.assertEqual(visible, declarations(strip_c_comments(self.header), "c"))
        self.assertEqual(visible, declarations(strip_c_comments(self.zig), "zig"))
        self.assertEqual(visible, declarations(strip_c_comments(self.rust), "rust"))

        # A source-only regex sees this prototype, but C11 does NOT.
        match = re.search(
            r"(?ms)^ptrdiff_t sens_zig_f3c_unpack\([^;]*?;", self.header,
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


    def test_root_asset_copy_is_separate_from_ten_function_abi_v2(self):
        check_root_asset_corridor(self.asset_zig, self.asset_rust, self.rust)
        self.assertEqual(len(EXPECTED), 10)
        self.assertEqual(set(declarations(strip_c_comments(self.rust), "rust")), set(EXPECTED))

    def test_unify_repl_uses_physical_t5m_asset_and_keeps_root_load_order(self):
        source = (ROOT / "crates/sens-cli/src/repl.rs").read_text(encoding="utf-8")
        self.assertNotIn('include_str!("../../../lib/unify.lisp")', source)
        self.assertNotIn("unify_surface_source", source)
        self.assertIn("repl_reasoning_t5m_assets()?", source)
        self.assertIn('"unify",', RUST_PATH.read_text())
        self.assertIn('lib/unify.sens', (ROOT / "zig_transport_root.zig").read_text())
        self.assertIn("D4 DEFINE reasoning programs must cross Zig as ordered root T5M pairs", source)
        build = (ROOT / "crates/sens-cli/build.rs").read_text(encoding="utf-8")
        self.assertIn("cargo:rerun-if-changed=../../lib/unify.sens", build)

    def test_unify_asset_cross_wiring_is_rejected_before_release(self):
        old = "@memcpy(dst[0..unify_asset.len], unify_asset[0..unify_asset.len]);"
        mutant = self.asset_zig.replace(
            old, "@memcpy(dst[0..unify_asset.len], uk_asset[0..unify_asset.len]);", 1,
        )
        self.assertNotEqual(mutant, self.asset_zig)
        with self.assertRaisesRegex(ValueError, "wrong_copy_body=sens_zig_unify_bytes_copy"):
            check_root_asset_corridor(mutant, self.asset_rust, self.rust)

    def test_unify_asset_ghost_export_is_rejected(self):
        mutant = self.asset_zig.replace(
            "pub export fn sens_zig_unify_bytes_copy",
            "fn sens_zig_unify_bytes_copy", 1,
        )
        self.assertNotEqual(mutant, self.asset_zig)
        with self.assertRaisesRegex(ValueError, "missing_copy_body=sens_zig_unify_bytes_copy"):
            check_root_asset_corridor(mutant, self.asset_rust, self.rust)

    def test_reason_repl_uses_ordered_physical_t5m_prerequisites(self):
        source = (ROOT / "crates/sens-cli/src/repl.rs").read_text(encoding="utf-8")
        self.assertNotIn('include_str!("../../../lib/reason.lisp")', source)
        self.assertNotIn("reason_surface_source", source)
        self.assertIn("repl_reasoning_t5m_assets()?", source)
        transport = RUST_PATH.read_text(encoding="utf-8")
        ordered_assets = transport[transport.index("pub fn repl_reasoning_t5m_assets"):
                                   transport.index("/// Opaque D9 witness", transport.index("pub fn repl_reasoning_t5m_assets"))]
        self.assertLess(ordered_assets.index('"unify"'), ordered_assets.index('"reason"'))
        self.assertLess(ordered_assets.index('"reason"'), ordered_assets.index('"forward"'))
        self.assertLess(ordered_assets.index('"forward"'), ordered_assets.index('"knowledge"'))
        self.assertIn('lib/reason.sens', (ROOT / "zig_transport_root.zig").read_text())
        build = (ROOT / "crates/sens-cli/build.rs").read_text(encoding="utf-8")
        self.assertIn("cargo:rerun-if-changed=../../lib/reason.sens", build)

    def test_reason_asset_crosswired_to_different_bytes_rejected(self):
        old = "@memcpy(dst[0..reason_asset.len], reason_asset[0..reason_asset.len]);"
        mutant = self.asset_zig.replace(
            old, "@memcpy(dst[0..reason_asset.len], uk_asset[0..reason_asset.len]);", 1)
        self.assertNotEqual(mutant, self.asset_zig)
        with self.assertRaisesRegex(ValueError, "wrong_copy_body=sens_zig_reason_bytes_copy"):
            check_root_asset_corridor(mutant, self.asset_rust, self.rust)

    def test_reason_asset_ghost_export_rejected(self):
        mutant = self.asset_zig.replace(
            "pub export fn sens_zig_reason_bytes_copy",
            "fn sens_zig_reason_bytes_copy", 1)
        self.assertNotEqual(mutant, self.asset_zig)
        with self.assertRaisesRegex(ValueError, "missing_copy_body=sens_zig_reason_bytes_copy"):
            check_root_asset_corridor(mutant, self.asset_rust, self.rust)

    def test_forward_repl_uses_physical_t5m_before_projection_layer(self):
        source = (ROOT / "crates/sens-cli/src/repl.rs").read_text(encoding="utf-8")
        self.assertNotIn('include_str!("../../../lib/forward.lisp")', source)
        self.assertNotIn("forward_surface_source", source)
        self.assertIn("repl_reasoning_t5m_assets()?", source)
        self.assertIn("execute_zig_t5m_asset(&physical, name, &mut root)?", source)
        transport = RUST_PATH.read_text(encoding="utf-8")
        ordered_assets = transport[transport.index("pub fn repl_reasoning_t5m_assets"):
                                   transport.index("/// Opaque D9 witness", transport.index("pub fn repl_reasoning_t5m_assets"))]
        self.assertLess(ordered_assets.index('"reason"'), ordered_assets.index('"forward"'))
        build = (ROOT / "crates/sens-cli/build.rs").read_text(encoding="utf-8")
        self.assertIn("cargo:rerun-if-changed=../../lib/forward.sens", build)

    def test_forward_asset_crosswired_bytes_rejected_before_release(self):
        old = "@memcpy(dst[0..forward_asset.len], forward_asset[0..forward_asset.len]);"
        mutant = self.asset_zig.replace(
            old, "@memcpy(dst[0..forward_asset.len], reason_asset[0..forward_asset.len]);", 1,
        )
        self.assertNotEqual(mutant, self.asset_zig)
        with self.assertRaisesRegex(ValueError, "wrong_copy_body=sens_zig_forward_bytes_copy"):
            check_root_asset_corridor(mutant, self.asset_rust, self.rust)

    def test_forward_asset_ghost_export_rejected(self):
        mutant = self.asset_zig.replace(
            "pub export fn sens_zig_forward_bytes_copy",
            "fn sens_zig_forward_bytes_copy", 1)
        self.assertNotEqual(mutant, self.asset_zig)
        with self.assertRaisesRegex(ValueError, "missing_copy_body=sens_zig_forward_bytes_copy"):
            check_root_asset_corridor(mutant, self.asset_rust, self.rust)

    def test_f6_binaries_use_aggregate_core4_t5m_not_separate_sources(self):
        for binary in (
            "crates/sens-cli/src/bin/wsm-fs-record-producer.rs",
            "crates/sens-cli/src/bin/wsm-fs-record-consumer.rs",
        ):
            source = (ROOT / binary).read_text(encoding="utf-8")
            self.assertIn("load_core_library(&mut session)", source)
            self.assertNotIn("bootstrap_f6_libraries", source)
            self.assertNotIn("zig_bootstrap_sources", source)
            self.assertNotIn("String::from_utf8", source)
            self.assertNotIn("eval_pinned_reasoning_source", source)
        bootstrap = (ROOT / "bootstrap_t5m.zig").read_text(encoding="utf-8")
        self.assertIn('.physical = @embedFile("lib/core4.sens")', bootstrap)
        build = (ROOT / "crates/sens/build.rs").read_text(encoding="utf-8")
        self.assertIn('"lib/core4.sens"', build)

    def test_world_byte_source_rejects_crosswire_mutant(self):
        check_root_asset_corridor(self.asset_zig, self.asset_rust, self.rust)
        old = "@memcpy(dst[0..world_asset.len], world_asset[0..world_asset.len]);"
        mutant = self.asset_zig.replace(
            old, "@memcpy(dst[0..world_asset.len], knowledge_asset[0..world_asset.len]);", 1
        )
        self.assertNotEqual(mutant, self.asset_zig)
        with self.assertRaisesRegex(ValueError, "wrong_copy_body=sens_zig_world_bytes_copy"):
            check_root_asset_corridor(mutant, self.asset_rust, self.rust)

    def test_content_store_byte_source_positive_and_crosswired_negative(self):
        check_root_asset_corridor(self.asset_zig, self.asset_rust, self.rust)
        old = "@memcpy(dst[0..content_store_asset.len], content_store_asset[0..content_store_asset.len]);"
        mutant = self.asset_zig.replace(
            old, "@memcpy(dst[0..content_store_asset.len], knowledge_asset[0..content_store_asset.len]);", 1
        )
        self.assertNotEqual(mutant, self.asset_zig)
        with self.assertRaisesRegex(ValueError, "wrong_copy_body=sens_zig_content_store_bytes_copy"):
            check_root_asset_corridor(mutant, self.asset_rust, self.rust)

    def test_persistent_map_byte_source_positive_and_crosswired_negative(self):
        check_root_asset_corridor(self.asset_zig, self.asset_rust, self.rust)
        old = "@memcpy(dst[0..persistent_map_asset.len], persistent_map_asset[0..persistent_map_asset.len]);"
        mutant = self.asset_zig.replace(
            old, "@memcpy(dst[0..persistent_map_asset.len], knowledge_asset[0..persistent_map_asset.len]);", 1
        )
        self.assertNotEqual(mutant, self.asset_zig)
        with self.assertRaisesRegex(ValueError, "wrong_copy_body=sens_zig_persistent_map_bytes_copy"):
            check_root_asset_corridor(mutant, self.asset_rust, self.rust)

    def test_knowledge_asset_crosswired_copy_refused(self):
        old = "@memcpy(dst[0..knowledge_asset.len], knowledge_asset[0..knowledge_asset.len]);"
        changed = self.asset_zig.replace(
            old, "@memcpy(dst[0..knowledge_asset.len], forward_asset[0..knowledge_asset.len]);", 1)
        self.assertNotEqual(changed, self.asset_zig)
        with self.assertRaisesRegex(ValueError, "wrong_copy_body=sens_zig_knowledge_bytes_copy"):
            check_root_asset_corridor(changed, self.asset_rust, self.rust)

    def test_knowledge_ghost_export_refused(self):
        changed = self.asset_zig.replace(
            "pub export fn sens_zig_knowledge_bytes_copy",
            "fn sens_zig_knowledge_bytes_copy", 1)
        self.assertNotEqual(changed, self.asset_zig)
        with self.assertRaisesRegex(ValueError, "missing_copy_body=sens_zig_knowledge_bytes_copy"):
            check_root_asset_corridor(changed, self.asset_rust, self.rust)

    def test_uk_docs_source_stays_inside_sterile_zig_corridor(self):
        """Live REPL docs must not reintroduce Rust project-source embedding."""
        source = (ROOT / "crates/sens-cli/src/repl/surface_catalog.rs").read_text(encoding="utf-8")
        self.assertNotIn('include_str!("../../../../lib/surface/uk-docs.lisp")', source)
        self.assertIn("crate::zig_transport::uk_docs_source_bytes()", source)
        self.assertIn('RUST_ZIG_ONLY: uk-docs requires Zig; no Rust source fallback', source)
        build = (ROOT / "crates/sens-cli/build.rs").read_text(encoding="utf-8")
        self.assertIn('cargo:rerun-if-changed=../../lib/surface/uk-docs.lisp', build)

    def test_uk_docs_rejects_crosswired_zig_bytes(self):
        old = "@memcpy(dst[0..uk_docs_asset.len], uk_docs_asset[0..uk_docs_asset.len]);"
        mutant = self.asset_zig.replace(
            old,
            "@memcpy(dst[0..uk_docs_asset.len], uk_asset[0..uk_docs_asset.len]);", 1,
        )
        self.assertNotEqual(mutant, self.asset_zig)
        with self.assertRaisesRegex(ValueError, "wrong_copy_body=sens_zig_uk_docs_bytes_copy"):
            check_root_asset_corridor(mutant, self.asset_rust, self.rust)

    def test_sens_repl_meta_ffi_missing_is_rejected(self):
        repl = (ROOT / "crates/sens-cli/src/repl.rs").read_text(encoding="utf-8")
        needle = "fn sens_zig_meta_eval_bytes_copy(dst: *mut u8, cap: usize) -> isize;"
        self.assertEqual(repl.count(needle), 1)
        with self.assertRaisesRegex(ValueError, "missing_meta_ffi=sens_zig_meta_eval_bytes_copy"):
            check_root_asset_corridor(self.asset_zig, self.asset_rust, self.rust,
                                      repl_source=repl.replace(needle, "", 1))

    def test_sens_repl_meta_wrong_byte_asset_is_rejected(self):
        needle = "@memcpy(dst[0..meta_eval_asset.len], meta_eval_asset[0..meta_eval_asset.len]);"
        mutant = self.asset_zig.replace(
            needle, "@memcpy(dst[0..meta_eval_asset.len], repl_core_asset[0..meta_eval_asset.len]);", 1
        )
        self.assertNotEqual(mutant, self.asset_zig)
        with self.assertRaisesRegex(ValueError, "wrong_copy_body=sens_zig_meta_eval_bytes_copy"):
            check_root_asset_corridor(mutant, self.asset_rust, self.rust)

    def test_guard_reference_dynamic_reader_is_reviewed_and_bounded(self):
        check_root_asset_corridor(self.asset_zig, self.asset_rust, self.rust)
        self.assertIn("LIVE_FILE_NAMES = (\"sens_zig_guard_reference_bytes_copy\",)",
                      Path(__file__).read_text(encoding="utf-8"))
        mutant = self.asset_zig.replace("8 * 1024 * 1024", "64 * 1024 * 1024", 1)
        self.assertNotEqual(mutant, self.asset_zig)
        with self.assertRaisesRegex(ValueError, "wrong_guard_reference_read_limit"):
            check_root_asset_corridor(mutant, self.asset_rust, self.rust)

    def test_root_asset_copy_missing_zig_export_is_rejected(self):
        mutated = self.asset_zig.replace(
            "pub export fn sens_zig_linter_bytes_copy",
            "fn sens_zig_linter_bytes_copy", 1,
        )
        self.assertNotEqual(mutated, self.asset_zig)
        with self.assertRaisesRegex(ValueError, "missing_copy_body=sens_zig_linter_bytes_copy"):
            check_root_asset_corridor(mutated, self.asset_rust, self.rust)

    def test_root_asset_copy_wrong_rust_pointer_constness_rejected(self):
        mutated = self.asset_rust.replace("output: *mut u8", "output: *const u8", 1)
        self.assertNotEqual(mutated, self.asset_rust)
        with self.assertRaisesRegex(ValueError, "asset_signature=sens_zig_linter_bytes_copy"):
            check_root_asset_corridor(self.asset_zig, mutated, self.rust)

    def test_root_asset_copy_missing_adapter_use_is_rejected(self):
        mutated = self.rust.replace(
            "asset_ffi::sens_zig_contract_bytes_copy(",
            "sens_zig_contract_bytes_copy(", 1,
        )
        self.assertNotEqual(mutated, self.rust)
        with self.assertRaisesRegex(ValueError, "missing_opaque_call=sens_zig_contract_bytes_copy"):
            check_root_asset_corridor(self.asset_zig, self.asset_rust, mutated)

    def test_root_asset_copy_unreviewed_extra_export_is_rejected(self):
        mutated = self.asset_zig + (
            "\\npub export fn sens_zig_unreviewed_bytes_copy(dst: [*]u8, capacity: usize) isize { return -1; }\\n"
        ).replace("\\n", "\n")
        with self.assertRaisesRegex(ValueError, "unreviewed_asset_exports=sens_zig_unreviewed_bytes_copy"):
            check_root_asset_corridor(mutated, self.asset_rust, self.rust)

    def test_root_asset_cross_wired_release_manifest_is_rejected(self):
        old = "@memcpy(dst[0..islands_manifest_asset.len], islands_manifest_asset[0..islands_manifest_asset.len]);"
        mutant = self.asset_zig.replace(
            old,
            "@memcpy(dst[0..islands_manifest_asset.len], uk_asset[0..islands_manifest_asset.len]);",
            1,
        )
        self.assertNotEqual(mutant, self.asset_zig)
        with self.assertRaisesRegex(
            ValueError, "wrong_copy_body=sens_zig_islands_manifest_bytes_copy"
        ):
            check_root_asset_corridor(mutant, self.asset_rust, self.rust)

    def test_root_asset_manifest_embed_rebound_while_path_still_exists_is_rejected(self):
        original = 'const islands_manifest_asset = @embedFile("packaging/islands-manifest-v1.json");'
        mutant = self.asset_zig.replace(
            original,
            'const islands_manifest_asset = @embedFile("lib/surface/uk.lisp");\n'
            'const unused_manifest = @embedFile("packaging/islands-manifest-v1.json");',
            1,
        )
        self.assertNotEqual(mutant, self.asset_zig)
        with self.assertRaisesRegex(
            ValueError, "wrong_asset_binding=sens_zig_islands_manifest_bytes_copy"
        ):
            check_root_asset_corridor(mutant, self.asset_rust, self.rust)

    def test_root_asset_copy_comment_ghost_does_not_count(self):
        mutated = self.asset_rust.replace(
            "    pub(super) fn sens_zig_linter_bytes_copy",
            "    // pub(super) fn sens_zig_linter_bytes_copy", 1,
        )
        self.assertNotEqual(mutated, self.asset_rust)
        with self.assertRaisesRegex(ValueError, "asset_signature=sens_zig_linter_bytes_copy"):
            check_root_asset_corridor(self.asset_zig, mutated, self.rust)

    def test_missing_zig_export_is_rejected(self):
        mutated = self.zig.replace(
            "pub export fn sens_zig_t5_decode_be3",
            "fn sens_zig_t5_decode_be3",
            1,
        )
        self.assertNotEqual(mutated, self.zig)
        with self.assertRaisesRegex(ValueError, "missing_or_duplicate=sens_zig_t5_decode_be3"):
            check_contract(mutated, self.rust, self.header)

    def test_coordinate_validator_is_reviewed_physical_only_abi(self):
        name = "sens_zig_t5_validate_coordinates"
        self.assertEqual(EXPECTED[name], (("source", "length"), "status"))
        # The same actual native declaration must exist in every host.
        for source, language in ((self.zig, "zig"), (self.rust, "rust"),
                                 (self.header, "c")):
            declared = declarations(strip_c_comments(source), language)
            self.assertEqual(declared[name], EXPECTED[name])

    def test_missing_rust_coordinate_validator_is_blocked(self):
        old = "    fn sens_zig_t5_validate_coordinates(input: *const u8, len: usize) -> i32;"
        self.assertIn(old, self.rust)
        altered = self.rust.replace(old, "", 1)
        with self.assertRaisesRegex(
            ValueError, "missing_or_duplicate=sens_zig_t5_validate_coordinates"
        ):
            check_contract(self.zig, altered, self.header)

    def test_coordinate_validator_wrong_return_type_is_blocked(self):
        old = "int sens_zig_t5_validate_coordinates("
        self.assertIn(old, self.header)
        altered = self.header.replace(old, "ptrdiff_t sens_zig_t5_validate_coordinates(", 1)
        with self.assertRaisesRegex(
            ValueError, "signature=sens_zig_t5_validate_coordinates"
        ):
            check_contract(self.zig, self.rust, altered)

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
