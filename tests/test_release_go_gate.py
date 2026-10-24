#!/usr/bin/env python3
"""Controls for the release GO-gate aggregator (#4196)."""
from __future__ import annotations

import importlib.util
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "release_go_gate.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("sens_release_go_gate", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GoGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "scripts").mkdir(parents=True, exist_ok=True)
        self.module = load_checker()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write(self, name: str, rc: int, msg: str) -> None:
        path = self.root / "scripts" / name
        if path.suffix == ".sh":
            path.write_text(
                "#!/usr/bin/env bash\n"
                f"printf '%s\\n' {shlex.quote(msg)}\n"
                f"exit {rc}\n",
                encoding="utf-8",
            )
        else:
            path.write_text(
                f"import sys\nprint({msg!r})\nsys.exit({rc})\n", encoding="utf-8")

    def _all_receipts(self) -> None:
        # The existing checkers emit these independently named success tokens.
        for _, script, _ in self.module.GATES:
            self._write(
                Path(script).name, 0,
                self.module.SUCCESS_MARKERS[script] + " exact-corridor-evidence",
            )

    def _run_gate(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CHECKER), str(self.root)],
            capture_output=True, text=True, check=False,
        )

    def test_shell_gate_runs_with_bash(self) -> None:
        script = "scripts/check_rust_isolated_only_zig.sh"
        marker = self.module.SUCCESS_MARKERS[script]
        checker = self.root / script
        checker.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "[[ \"${BASH_VERSION:-}\" != \"\" ]]\n"
            f"printf '%s\\n' {marker!r}\n",
            encoding="utf-8",
        )
        verdict, note = self.module.run_gate(self.root, script)
        self.assertEqual(verdict, "GO", note)
        self.assertIn(marker, note)

    def test_all_structural_checks_green_is_not_an_artificial_red(self) -> None:
        self._all_receipts()
        proc = self._run_gate()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("RELEASE_STRUCTURAL_GATES_GO 10/10", proc.stdout)
        self.assertIn("RELEASE_ADMISSION_UNVERIFIED", proc.stdout)
        self.assertNotIn("RELEASE_GATE_GO every", proc.stdout)

    def test_all_structural_checks_green_json_still_reports_release_block(self) -> None:
        import json
        self._all_receipts()
        receipt = self.root / "structural-only.json"
        proc = subprocess.run(
            [sys.executable, str(CHECKER), str(self.root), "--json", str(receipt)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(proc.returncode, 0)
        report = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual(report["go"], report["total"])
        self.assertIs(report["release_go"], False)
        self.assertEqual(report["release_admission"], "NOT_VERIFIED")

    def test_structural_only_can_pass_without_claiming_release_go(self) -> None:
        import json
        self._all_receipts()
        receipt = self.root / "preflight.json"
        proc = subprocess.run(
            [sys.executable, str(CHECKER), str(self.root),
             "--structural-only", "--json", str(receipt)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("RELEASE_STRUCTURAL_ONLY_PASS", proc.stdout)
        self.assertNotIn("RELEASE_GATE_GO every", proc.stdout)
        report = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertFalse(report["release_go"])
        self.assertEqual(report["release_admission"], "NOT_VERIFIED")

    def test_structural_only_does_not_hide_a_red_corridor(self) -> None:
        self._all_receipts()
        self._write("check_rust_isolated_only_zig.sh", 1, "RED")
        proc = subprocess.run(
            [sys.executable, str(CHECKER), str(self.root), "--structural-only"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("RELEASE_GATE_NO_GO", proc.stdout)
        self.assertNotIn("RELEASE_STRUCTURAL_ONLY_PASS", proc.stdout)

    def test_one_red_is_no_go(self) -> None:
        self._all_receipts()
        self._write("check_rust_isolated_only_zig.sh", 1, "RED")
        proc = subprocess.run([sys.executable, str(CHECKER), str(self.root)],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("RELEASE_GATE_NO_GO", proc.stdout)
        self.assertIn("rust-isolated", proc.stdout)

    def test_missing_script_is_unverified_not_pass(self) -> None:
        # only one gate present -> the rest are UNVERIFIED, never a fake PASS
        self._write("check_numeric_domain_exclusive.py", 0, "OK")
        proc = subprocess.run([sys.executable, str(CHECKER), str(self.root)],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("UNVERIFIED", proc.stdout)
        self.assertIn("RELEASE_GATE_PARTIAL", proc.stdout)



    def test_zero_exit_silent_guard_is_not_structural_proof(self) -> None:
        self._all_receipts()
        self._write("check_sterile_zig_corridor.py", 0, "")
        result = self._run_gate()
        self.assertEqual(result.returncode, 1)
        self.assertIn("UNVERIFIED", result.stdout)
        self.assertIn("STERILE_ZIG_CORRIDOR_PASS", result.stdout)
        self.assertNotIn("RELEASE_GATE_GO every", result.stdout)

    def test_zero_exit_wrong_corridor_receipt_is_not_proof(self) -> None:
        self._all_receipts()
        self._write("check_migration_zig_only_path.py", 0, "CORRIDOR_OK")
        result = self._run_gate()
        self.assertEqual(result.returncode, 1)
        self.assertIn("MIGRATION_ZIG_ONLY_PATH_OK", result.stdout)
        self.assertIn("UNVERIFIED", result.stdout)

    def test_success_marker_must_be_unique_and_last(self) -> None:
        self._all_receipts()
        checker = self.root / "scripts" / "check_sterile_zig_corridor.py"
        marker = self.module.SUCCESS_MARKERS["scripts/check_sterile_zig_corridor.py"]
        for source in (
            f"print({marker!r})\nprint('INCOMPLETE')\n",
            f"print({marker!r})\nprint({marker!r})\n",
        ):
            with self.subTest(source=source):
                checker.write_text(source, encoding="utf-8")
                result = self._run_gate()
                self.assertEqual(result.returncode, 1)
                self.assertIn("UNVERIFIED", result.stdout)

    def test_symlinked_corridor_checker_cannot_fake_proof(self) -> None:
        self._all_receipts()
        fake = self.root / "fake.py"
        marker = self.module.SUCCESS_MARKERS["scripts/check_sterile_zig_corridor.py"]
        fake.write_text(f"print({marker!r})\n", encoding="utf-8")
        checker = self.root / "scripts" / "check_sterile_zig_corridor.py"
        checker.unlink()
        checker.symlink_to(fake)
        result = self._run_gate()
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing regular checker script", result.stdout)
        self.assertIn("UNVERIFIED", result.stdout)

    def test_failing_guard_cannot_claim_go_with_valid_marker(self) -> None:
        self._all_receipts()
        script = "scripts/check_rust_sens_zig_corridor.py"
        self._write(Path(script).name, 1, self.module.SUCCESS_MARKERS[script])
        result = self._run_gate()
        self.assertEqual(result.returncode, 1)
        self.assertIn("corridor-structural", result.stdout)
        self.assertIn("RELEASE_GATE_NO_GO", result.stdout)


if __name__ == "__main__":
    unittest.main()
