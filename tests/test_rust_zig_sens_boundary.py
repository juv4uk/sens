#!/usr/bin/env python3
"""Fail-closed: published Rust↔Zig↔SENS boundary map is regenerable evidence (#5779).

The map names every production Rust contact with SENS (corridor / mixed / direct /
filesystem) and real file+SHA. Direct contacts are BYPASS debt — not greenwashed.
No semantic SENS admission.
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
        import json as _json
        if (not MAP_PATH.is_file()) or MAP_PATH.read_text(encoding="utf-8").strip() in ("", "PLACEHOLDER"):
            data = cls.mod.build_map(ROOT)
            MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
            MAP_PATH.write_text(
                _json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    def test_published_map_exists_and_matches_schema(self) -> None:
        self.assertTrue(
            MAP_PATH.is_file(),
            "boundary map must be published under research/zig-codecs/",
        )
        data = json.loads(MAP_PATH.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "sens-rust-zig-sens-boundary/v1")
        self.assertIn("#5777", data["owner_rule"])
        self.assertIn("contacts", data)
        self.assertIn("bypasses", data)
        self.assertIn("legend", data)
        for contact in data["contacts"]:
            self.assertIn("path", contact)
            self.assertIn("kind", contact)
            self.assertIn("sha256", contact)
            self.assertEqual(len(contact["sha256"]), 64)

    def test_regeneration_matches_published_structure(self) -> None:
        published = json.loads(MAP_PATH.read_text(encoding="utf-8"))
        fresh = self.mod.build_map(ROOT)
        pub_paths = sorted(c["path"] for c in published["contacts"])
        fresh_paths = sorted(c["path"] for c in fresh["contacts"])
        self.assertEqual(
            pub_paths,
            fresh_paths,
            "published boundary map drifted from live scan — regenerate and commit",
        )
        pub_kinds = {c["path"]: c["kind"] for c in published["contacts"]}
        fresh_kinds = {c["path"]: c["kind"] for c in fresh["contacts"]}
        self.assertEqual(pub_kinds, fresh_kinds)
        self.assertEqual(sorted(published["bypasses"]), sorted(fresh["bypasses"]))
        import hashlib
        for contact in fresh["contacts"]:
            live = (ROOT / contact["path"]).read_bytes()
            self.assertEqual(
                contact["sha256"],
                hashlib.sha256(live).hexdigest(),
                f"stale SHA for {contact['path']}",
            )

    def test_corridor_contacts_include_zig_entrypoints(self) -> None:
        data = self.mod.build_map(ROOT)
        corridorish = {c["path"] for c in data["contacts"] if c.get("corridor")}
        self.assertTrue(
            any("zig_transport" in p or "zig_corridor" in p for p in corridorish),
            f"expected zig transport/corridor among corridor contacts, got {corridorish}",
        )

    def test_check_fails_closed_on_direct_bypass(self) -> None:
        data = self.mod.build_map(ROOT)
        self.assertGreater(
            len(data["bypasses"]),
            0,
            "expected direct bypass debt until full Zig cutover",
        )
        import sys
        old = sys.argv[:]
        try:
            sys.argv = [
                "report_rust_zig_sens_boundary.py",
                str(ROOT),
                "--out",
                str(MAP_PATH),
                "--check",
            ]
            rc = self.mod.main()
        finally:
            sys.argv = old
        self.assertEqual(rc, 1, "--check must stay RED while direct bypasses remain")


    def test_mixed_zig_token_cannot_hide_direct_rust_semantic_bypass(self) -> None:
        # Synthetic source is structural evidence ONLY, not executable SENS.
        # Even a comment mentioning Zig may label a Rust file as "mixed";
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
            self.assertEqual(report["contacts"][0]["kind"], "mixed")
            self.assertEqual(report["bypasses"], [])  # legacy direct-only field
            self.assertEqual(rc, 1, output)
            self.assertIn("BOUNDARY_BYPASS_PRESENT", output)
            self.assertIn("kind=mixed", output)
            self.assertIn("crates/demo/src/lib.rs", output)

            # A real Zig transport reference with NO direct semantic source
            # is not a structural bypass. SENS owns semantic validity.
            rc, report, output = verify(
                "pub fn forward() { let _ = zig_transport::encode; }\n"
            )
            self.assertEqual(report["contacts"][0]["kind"], "corridor")
            self.assertEqual(report["bypasses"], [])
            self.assertEqual(rc, 0, output)



if __name__ == "__main__":
    unittest.main(verbosity=2)
