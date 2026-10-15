#!/usr/bin/env python3
"""Negative controls for the Rust<->SENS sterile-Zig-corridor guard (#5777/#5779).

Each invariant must fail CLOSED: mutating it in a mirror of the real corridor
files must make the checker report at least one problem.
"""
from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_rust_sens_zig_corridor.py"

CORRIDOR_FILES = (
    "crates/sens-cli/Cargo.toml",
    "crates/sens-cli/build.rs",
    "research/zig-codecs/transport_abi.zig",
    ".zig-version",
)
HOST_C = "research/zig-codecs/host-c"


def load_checker():
    spec = importlib.util.spec_from_file_location("sens_zig_corridor_guard", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def mirror(dst: Path) -> None:
    for rel in CORRIDOR_FILES:
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, target)
    host_dir = dst / HOST_C
    host_dir.mkdir(parents=True, exist_ok=True)
    for host in (ROOT / HOST_C).glob("*"):
        if host.is_file():
            shutil.copyfile(host, host_dir / host.name)


def mutate(root: Path, rel: str, old: str, new: str) -> None:
    path = root / rel
    text = path.read_text(encoding="utf-8")
    assert old in text, f"mutation anchor not found in {rel}: {old!r}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


class CorridorGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        mirror(self.root)
        self.module = load_checker()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_real_corridor_passes(self) -> None:
        self.assertEqual(self.module.check(self.root), [])

    def test_version_only_c_host_and_comment_ghost_is_blocked(self) -> None:
        # A version getter does not prove that C uses the Zig physical corridor.
        host_dir = self.root / HOST_C
        for source in host_dir.glob("*.c"):
            source.unlink()
        (host_dir / "corridor_v2.c").write_text(
            """int main(void) {
  // sens_zig_t5_encode_be3(src, n, dst, cap);
  /* sens_zig_t5_decode_be3(src, n, dst, cap); */
  return sens_zig_codec_abi_version() == 2 ? 0 : 1;
}
""",
            encoding="utf-8",
        )
        problems = self.module.check(self.root)
        self.assertTrue(
            any("no Rust-free host" in problem for problem in problems), problems
        )

    def test_c_string_literal_ghost_is_blocked(self) -> None:
        # A function name inside a string is data, not a Zig transport call.
        host_dir = self.root / HOST_C
        for source in host_dir.glob("*.c"):
            source.unlink()
        (host_dir / "corridor_v2.c").write_text(
            '''int main(void) {
  const char *ghost = "sens_zig_t5_encode_be3(";
  const char *url = "https://ziglang.org/doc";
  return sens_zig_codec_abi_version() == 2 ? 0 : 1;
}
''',
            encoding="utf-8",
        )
        problems = self.module.check(self.root)
        self.assertTrue(
            any("no Rust-free host" in problem for problem in problems), problems
        )

    def test_c_string_comment_delimiters_do_not_hide_real_call(self) -> None:
        # Textual /* and */ in C strings cannot consume a live physical call.
        host_dir = self.root / HOST_C
        for source in host_dir.glob("*.c"):
            source.unlink()
        (host_dir / "corridor_v2.c").write_text(
            '''#include "zig_transport_v2.h"
int main(void) {
  const char *prefix = "/*";
  const unsigned char input[] = {0};
  int rc = sens_zig_t5_validate(input, sizeof input);
  const char *suffix = "*/";
  return rc == 0 && prefix[0] && suffix[0] ? 0 : 1;
}
''',
            encoding="utf-8",
        )
        self.assertEqual(self.module.check(self.root), [])

    # --- R1..R4 (structural corridor) -------------------------------------
    def test_default_without_zig_transport_is_blocked(self) -> None:
        mutate(self.root, "crates/sens-cli/Cargo.toml", 'default = ["zig-transport"]', "default = []")
        self.assertTrue(self.module.check(self.root))

    def test_missing_feature_gate_is_blocked(self) -> None:
        mutate(
            self.root,
            "crates/sens-cli/build.rs",
            "CARGO_FEATURE_ZIG_TRANSPORT",
            "CARGO_FEATURE_SOMETHING_ELSE",
        )
        self.assertTrue(self.module.check(self.root))

    def test_semantic_import_in_abi_is_blocked(self) -> None:
        mutate(
            self.root,
            "research/zig-codecs/transport_abi.zig",
            '@import("t5/t5.zig")',
            '@import("semantic-registry.zig")',
        )
        self.assertTrue(self.module.check(self.root))

    def test_nonphysical_export_is_blocked(self) -> None:
        mutate(
            self.root,
            "research/zig-codecs/transport_abi.zig",
            "pub export fn sens_zig_codec_abi_version",
            "pub export fn host_opcode",
        )
        self.assertTrue(self.module.check(self.root))

    def test_unpinned_zig_version_is_blocked(self) -> None:
        (self.root / ".zig-version").write_text("stable\n", encoding="utf-8")
        self.assertTrue(self.module.check(self.root))

    # --- R5 (host-neutral: one corridor for all hosts) --------------------
    def test_header_missing_op_is_blocked(self) -> None:
        mutate(
            self.root,
            "research/zig-codecs/host-c/zig_transport_v2.h",
            "int sens_zig_t5_validate(const uint8_t *src, size_t len);",
            "/* removed corridor op */",
        )
        self.assertTrue(self.module.check(self.root))

    def test_header_extra_op_is_blocked(self) -> None:
        mutate(
            self.root,
            "research/zig-codecs/host-c/zig_transport_v2.h",
            "uint32_t sens_zig_codec_abi_version(void);",
            "uint32_t sens_zig_codec_abi_version(void);\n"
            "ptrdiff_t sens_zig_bogus(const uint8_t *src, size_t len);",
        )
        self.assertTrue(self.module.check(self.root))

    def test_abi_version_mismatch_is_blocked(self) -> None:
        mutate(
            self.root,
            "research/zig-codecs/host-c/zig_transport_v2.h",
            "SENS_ZIG_TRANSPORT_ABI_VERSION = 2",
            "SENS_ZIG_TRANSPORT_ABI_VERSION = 3",
        )
        self.assertTrue(self.module.check(self.root))

    def test_host_rogue_op_is_blocked(self) -> None:
        mutate(
            self.root,
            "research/zig-codecs/host-c/corridor_v2.c",
            "sens_zig_codec_abi_version",
            "sens_zig_fake_version",
        )
        self.assertTrue(self.module.check(self.root))


if __name__ == "__main__":
    unittest.main()
