#!/usr/bin/env python3
"""Fail-closed exact-SHA Rust↔Zig↔SENS boundary artifact tests (#5779).

The tracked JSON marker is NOT a live map. Tests build fresh evidence in a
temporary directory and MUST NOT rewrite repository files, including on RED.
This is source/provenance evidence, never native SENS semantic admission.
"""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "report_rust_zig_sens_boundary.py"
MAP_PATH = ROOT / "research" / "zig-codecs" / "rust_zig_sens_boundary.json"


def load_module():
    spec = importlib.util.spec_from_file_location("report_rust_zig_sens_boundary", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class RustZigSensBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load_module()
        cls.report_dir = tempfile.TemporaryDirectory(prefix="sens-boundary-receipt-")
        cls.addClassCleanup(cls.report_dir.cleanup)
        cls.generated_map = Path(cls.report_dir.name) / "boundary.json"
        cls.generated_map.write_text(
            json.dumps(cls.mod.build_map(ROOT), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_generated_map_exists_and_matches_schema(self) -> None:
        self.assertTrue(self.generated_map.is_file(), "generated receipt is missing")
        data = json.loads(self.generated_map.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "sens-rust-zig-sens-boundary/v1")
        self.assertIn("#5777", data["owner_rule"])
        self.assertIn("contacts", data)
        self.assertIn("bypasses", data)
        self.assertIn("unresolved_bypasses", data)
        self.assertEqual(
            sorted(c["path"] for c in data["unresolved_bypasses"]),
            sorted(c["path"] for c in data["contacts"]
                   if c["kind"] in ("direct", "mixed")),
        )
        self.assertIn("legend", data)
        for contact in data["contacts"]:
            self.assertIn("path", contact)
            self.assertIn("kind", contact)
            self.assertIn("sha256", contact)
            self.assertEqual(len(contact["sha256"]), 64)

    def test_regeneration_matches_generated_structure(self) -> None:
        published = json.loads(self.generated_map.read_text(encoding="utf-8"))
        fresh = self.mod.build_map(ROOT)
        pub_paths = sorted(c["path"] for c in published["contacts"])
        fresh_paths = sorted(c["path"] for c in fresh["contacts"])
        self.assertEqual(
            pub_paths,
            fresh_paths,
            "generated boundary receipt drifted from live scan",
        )
        pub_kinds = {c["path"]: c["kind"] for c in published["contacts"]}
        fresh_kinds = {c["path"]: c["kind"] for c in fresh["contacts"]}
        self.assertEqual(pub_kinds, fresh_kinds)
        self.assertEqual(sorted(published["bypasses"]), sorted(fresh["bypasses"]))
        self.assertEqual(
            sorted(published["unresolved_bypasses"], key=lambda c: c["path"]),
            sorted(fresh["unresolved_bypasses"], key=lambda c: c["path"]),
        )
        import hashlib
        for contact in fresh["contacts"]:
            live = (ROOT / contact["path"]).read_bytes()
            self.assertEqual(
                contact["sha256"],
                hashlib.sha256(live).hexdigest(),
                f"stale SHA for {contact['path']}",
            )

    def test_cli_generates_receipt_without_mutating_tracked_marker(self) -> None:
        import subprocess
        import sys

        before = MAP_PATH.read_bytes() if MAP_PATH.is_file() else None
        with tempfile.TemporaryDirectory(prefix="sens-boundary-cli-") as tmp:
            destination = Path(tmp) / "receipt.json"
            run = subprocess.run(
                [sys.executable, str(SCRIPT), str(ROOT),
                 "--out", str(destination)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            receipt = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(receipt, self.mod.build_map(ROOT))
            self.assertTrue(all(len(c["sha256"]) == 64
                                for c in receipt["contacts"]))
        after = MAP_PATH.read_bytes() if MAP_PATH.is_file() else None
        self.assertEqual(after, before, "test/CLI mutated tracked repository marker")
        # A placeholder is not publication or release evidence.
        if before is not None and before.strip() == b"PLACEHOLDER":
            self.assertNotEqual(before, self.generated_map.read_bytes())

    def test_corridor_contacts_include_zig_entrypoints(self) -> None:
        data = self.mod.build_map(ROOT)
        corridorish = {c["path"] for c in data["contacts"] if c.get("corridor")}
        self.assertTrue(
            any("zig_transport" in p or "zig_corridor" in p for p in corridorish),
            f"expected zig transport/corridor among corridor contacts, got {corridorish}",
        )

    def test_check_fails_closed_on_any_unresolved_bypass(self) -> None:
        data = self.mod.build_map(ROOT)
        import sys
        old = sys.argv[:]
        try:
            sys.argv = [
                "report_rust_zig_sens_boundary.py",
                str(ROOT),
                "--out",
                str(self.generated_map),
                "--check",
            ]
            rc = self.mod.main()
        finally:
            sys.argv = old
        self.assertEqual(rc, int(bool(data["unresolved_bypasses"])),
                         "--check must reflect actual direct/mixed bypass debt")


    def test_mixed_zig_token_cannot_hide_direct_rust_semantic_bypass(self) -> None:
        # Synthetic source is structural evidence ONLY, not executable SENS.
        # A comment mentioning Zig must NOT label a direct Rust source as mixed;
        # release preflight must still see the direct Rust semantic path.
        import subprocess
        import sys

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            crate = root / "crates" / "demo" / "src"
            crate.mkdir(parents=True)
            source = crate / "lib.rs"

            def verify(content: str) -> tuple[int, dict, str]:
                source.write_text(content, encoding="utf-8")
                mapped = self.mod.build_map(root)
                run = subprocess.run(
                    [
                        sys.executable, str(SCRIPT), str(root),
                        "--out", "boundary.json", "--check",
                    ],
                    capture_output=True, text=True, check=False,
                )
                return run.returncode, mapped, run.stdout

            rc, report, output = verify(
                "// zig_transport appears in a comment ONLY\n"
                "pub fn bypass() { let _ = eval::execute; }\n"
            )
            self.assertEqual(report["contacts"][0]["kind"], "direct")
            self.assertEqual(report["bypasses"], ["crates/demo/src/lib.rs"])
            self.assertEqual(
                [(c["path"], c["kind"]) for c in report["unresolved_bypasses"]],
                [("crates/demo/src/lib.rs", "direct")],
            )
            self.assertEqual(
                report["unresolved_bypasses"][0]["sha256"],
                self.mod._sha(root, "crates/demo/src/lib.rs"),
            )
            self.assertEqual(rc, 1, output)
            self.assertIn("BOUNDARY_BYPASS_PRESENT", output)
            self.assertIn("kind=direct", output)
            self.assertIn("sha256=", output)
            self.assertIn("crates/demo/src/lib.rs", output)

            # A real Zig transport reference with NO direct semantic source
            # is not a structural bypass. SENS owns semantic validity.
            rc, report, output = verify(
                "pub fn forward() { let _ = zig_transport::encode; }\n"
            )
            self.assertEqual(report["contacts"][0]["kind"], "corridor")
            self.assertEqual(report["bypasses"], [])
            self.assertEqual(report["unresolved_bypasses"], [])
            self.assertEqual(rc, 0, output)

            # A real direct source is listed in BOTH compatible fields.
            rc, report, output = verify(
                "pub fn bypass() { let _ = eval::execute; }\n"
            )
            self.assertEqual(report["contacts"][0]["kind"], "direct")
            self.assertEqual(report["bypasses"], ["crates/demo/src/lib.rs"])
            self.assertEqual(
                [(c["path"], c["kind"]) for c in report["unresolved_bypasses"]],
                [("crates/demo/src/lib.rs", "direct")],
            )
            self.assertEqual(rc, 1, output)



    def test_only_live_rust_tokens_can_claim_zig_corridor(self) -> None:
        # A stale commented Zig call, quoted token or nested block comment
        # cannot be counted as an active Rust -> Zig physical route.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "crates" / "demo" / "src"
            folder.mkdir(parents=True)
            path = folder / "lib.rs"

            def classify(source: str) -> tuple[str, bool]:
                path.write_text(source, encoding="utf-8")
                records = self.mod.build_map(root)["contacts"]
                self.assertEqual(len(records), 1, records)
                return records[0]["kind"], records[0]["corridor"]

            for ghost in (
                "// zig_transport::encode_t5_direct()\n",
                "/* zig_transport::encode_t5_direct() */\n",
                "/* outer /* zig_transport::encode_t5_direct() */ still */\n",
                'const EXAMPLE: &str = "zig_transport::encode_t5_direct()";\n',
                'const EXAMPLE: &str = r##"zig_transport::encode_t5_direct()"##;\n',
                'const EXAMPLE: &str = br#"sens_zig_t5_validate()"#;\n',
            ):
                with self.subTest(ghost=ghost):
                    self.assertEqual(
                        classify(ghost + 'fn physical() { let _ = ".sens"; }\n'),
                        ("filesystem", False),
                    )

            # A real live imported symbol remains transport-only evidence.
            self.assertEqual(
                classify("use crate::zig_transport;\n"
                         'fn physical() { let _ = ".sens"; '
                         "let _ = zig_transport::encode_t5_direct; }\n"),
                ("corridor", True),
            )
            # Even when a Zig import is real, direct Rust evaluation stays
            # in the independently reported unresolved bypass list.
            path.write_text(
                "use crate::zig_transport;\n"
                "fn bypass() { let _ = eval::execute; }\n",
                encoding="utf-8",
            )
            record = self.mod.build_map(root)
            self.assertEqual(record["contacts"][0]["kind"], "mixed")
            self.assertEqual(
                [row["kind"] for row in record["unresolved_bypasses"]],
                ["mixed"],
            )



if __name__ == "__main__":
    unittest.main(verbosity=2)
