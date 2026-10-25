#!/usr/bin/env python3
"""Fail-closed regression for the migration \u2194 Zig preparation gate."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migration-zig-gate.py"


def load():
    spec = importlib.util.spec_from_file_location("migration_zig_gate", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class MigrationZigGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load()

    def test_zig_pin_matches_0160(self) -> None:
        report = self.mod.check_zig_pin()
        self.assertEqual(report["status"], "PASS")
        self.assertIn("0.16.0", report["detail"])

    def test_exact_domain_authority_uses_current_migrator_return_shape(self) -> None:
        report = self.mod.load_exact_domain_authority()
        self.assertEqual(report["step"], "migrate-exact-domain-authority")
        self.assertEqual(report["status"], "PASS")
        self.assertIn("surfaces=", report["detail"])

    def test_self_test_passes_without_zig_binary(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--self-test"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("verdict=SELF_TEST_ONLY", completed.stdout)
        self.assertNotIn("verdict=PASS", completed.stdout)

    def test_self_test_report_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "gate.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--self-test",
                    "--report",
                    str(report_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            data = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(data["schema"], "sens-migration-zig-gate/v1")
            self.assertEqual(data["verdict"], "SELF_TEST_ONLY")
            self.assertIs(data["transport_verified"], False)
            self.assertEqual(data["scope"], "SELF_TEST_NOT_PHYSICAL")
            self.assertEqual(data["zig_pin"], "0.16.0")
            self.assertIn("zig-is-turnstile-not-registry", data["axioms"])
            steps = {s["step"]: s["status"] for s in data["steps"]}
            self.assertEqual(steps.get("zig-pin"), "PASS")
            self.assertEqual(steps.get("ci_zig_purity"), "PASS")
            self.assertEqual(steps.get("check_rust_sens_corridor_coverage"), "PASS")
            self.assertEqual(steps.get("check_corridor_axiom_binding"), "PASS")
            self.assertEqual(steps.get("test_zig_codec_bridge"), "SKIP")


    def test_missing_or_failed_host_guards_fail_closed(self) -> None:
        passing = [{"step": name, "status": "PASS", "exit": 0}
                   for name in self.mod.REQUIRED_STEPS]
        self.assertEqual(self.mod.gate_verdict(
            passing, self_test=False, skip_ladder=False), "PASS")
        for guard in ("check_rust_sens_corridor_coverage", "check_corridor_axiom_binding"):
            with self.subTest(guard=guard):
                missing = [item for item in passing if item["step"] != guard]
                self.assertEqual(self.mod.gate_verdict(
                    missing, self_test=False, skip_ladder=False), "INCOMPLETE")
                negative = [dict(item) for item in passing]
                for item in negative:
                    if item["step"] == guard:
                        item["status"] = "FAIL"
                self.assertEqual(self.mod.gate_verdict(
                    negative, self_test=False, skip_ladder=False), "FAIL")

    def test_process_exit_truth_cannot_be_replaced_by_pass_label(self) -> None:
        # Process evidence is required for release readiness; this synthetic
        # gate test does NOT execute Zig or establish SENS semantic admission.
        baseline = [
            {"step": name, "status": "PASS", "exit": 0}
            for name in self.mod.REQUIRED_STEPS
        ]
        self.assertEqual(
            self.mod.gate_verdict(
                baseline, self_test=False, skip_ladder=False
            ), "PASS",
        )
        for guard in ("test_zig_codec_bridge",
                      "check_sterile_zig_corridor",
                      "check_rust_sens_zig_corridor"):
            with self.subTest(guard=guard):
                for exit_code in (1, 17, -9):
                    forged = [dict(step) for step in baseline]
                    next(step for step in forged
                         if step["step"] == guard)["exit"] = exit_code
                    self.assertEqual(
                        self.mod.gate_verdict(
                            forged, self_test=False, skip_ladder=False
                        ), "FAIL",
                        f"forged PASS with exit={exit_code} guard={guard}",
                    )
                for bad_exit in (None, "0", False):
                    invalid = [dict(step) for step in baseline]
                    next(step for step in invalid
                         if step["step"] == guard)["exit"] = bad_exit
                    self.assertEqual(
                        self.mod.gate_verdict(
                            invalid, self_test=False, skip_ladder=False
                        ), "INCOMPLETE",
                    )
                missing = [dict(step) for step in baseline]
                del next(step for step in missing if step["step"] == guard)["exit"]
                self.assertEqual(
                    self.mod.gate_verdict(
                        missing, self_test=False, skip_ladder=False
                    ), "INCOMPLETE",
                )
        self.assertEqual(
            self.mod.gate_verdict(
                baseline, self_test=True, skip_ladder=True
            ), "SELF_TEST_ONLY",
        )
        contradictory = [dict(step) for step in baseline]
        contradictory[-1]["exit"] = 2
        self.assertEqual(
            self.mod.gate_verdict(
                contradictory, self_test=True, skip_ladder=True
            ), "FAIL",
        )


    def test_full_gate_does_not_claim_pass_on_failing_guard(self) -> None:
        # Mocked orchestration, NOT an actual Zig codec or semantic receipt.
        def simulate(bad: str | None) -> tuple[int, dict, list[str]]:
            called = []
            def fake_step(name: str, argv: list[str], **kwargs) -> dict:
                called.append(name)
                return {"step": name, "status": "FAIL" if name == bad else "PASS",
                        "exit": 1 if name == bad else 0, "detail": "MOCK"}
            with tempfile.TemporaryDirectory() as folder:
                output = Path(folder) / "receipt.json"
                with (
                    mock.patch.object(self.mod, "run_step", side_effect=fake_step),
                    mock.patch.object(self.mod, "check_zig_pin", return_value={
                        "step": "zig-pin", "status": "PASS", "exit": 0, "detail": "MOCK"}),
                    mock.patch.object(self.mod, "load_exact_domain_authority", return_value={
                        "step": "migrate-exact-domain-authority",
                        "status": "PASS", "exit": 0, "detail": "MOCK"}),
                    mock.patch.object(sys, "argv", [str(SCRIPT), "--report", str(output)]),
                    redirect_stdout(StringIO()),
                ):
                    rc = self.mod.main()
                return rc, json.loads(output.read_text(encoding="utf-8")), called
        rc, result, called = simulate(None)
        self.assertEqual((rc, result["verdict"]), (0, "PASS"))
        for guard in ("check_rust_sens_corridor_coverage", "check_corridor_axiom_binding"):
            self.assertIn(guard, called)
            with self.subTest(guard=guard):
                rc, result, again = simulate(guard)
                self.assertIn(guard, again)
                self.assertEqual((rc, result["verdict"]), (1, "FAIL"))
                self.assertIs(result["transport_verified"], False)



class ZigBridgeReceiptEvidenceTests(unittest.TestCase):
    """Source-independent synthetic process receipts, never Zig execution."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load()

    def good_line(self) -> str:
        values = {
            **self.mod.BRIDGE_RECEIPT_EXACT,
            **{k: str(v) for k, v in self.mod.BRIDGE_RECEIPT_MINIMUM.items()},
            "zig_binary_sha256": "a" * 64,
        }
        return "ZIG_BRIDGE_PASS " + " ".join(
            f"{k}={v}" for k, v in values.items()
        )

    def simulated_step(self, stdout: str, *, stderr: str = "", rc: int = 0) -> dict:
        completed = subprocess.CompletedProcess(
            args=["python", "test_zig_codec_bridge.py"],
            returncode=rc, stdout=stdout, stderr=stderr,
        )
        with mock.patch.object(self.mod.subprocess, "run", return_value=completed):
            return self.mod.run_step("test_zig_codec_bridge", ["python", "fake.py"])

    def test_exact_zig_physical_receipt_passes_structural_gate(self):
        result = self.simulated_step(self.good_line() + "\n")
        self.assertEqual((result["status"], result["exit"]), ("PASS", 0))
        parsed = self.mod.verify_zig_bridge_receipt(self.good_line())
        self.assertEqual(parsed["external_trusted_sha_d10"], "INDEPENDENT_GOLDEN")
        self.assertEqual(parsed["external_trusted_sha_d1"], "INDEPENDENT_GOLDEN")
        self.assertEqual(parsed["canonical_d1_to_d2_same_length"],
                         "REJECTED_WITH_EXTERNAL_PIN")

    def test_stronger_independent_goldens_are_required_not_optional(self):
        for field, obsolete in (
            ("external_trusted_sha_d10=INDEPENDENT_GOLDEN",
             "external_trusted_sha_d10=REQUIRED_WHEN_SUPPLIED"),
            ("external_trusted_sha_d1=INDEPENDENT_GOLDEN",
             "external_trusted_sha_d1=REQUIRED_WHEN_SUPPLIED"),
            ("canonical_d1_to_d2_same_length=REJECTED_WITH_EXTERNAL_PIN",
             "canonical_d1_to_d2_same_length=NOT_TESTED"),
        ):
            with self.subTest(field=field):
                original = self.good_line()
                self.assertIn(field, original)
                for mutant in (original.replace(field, obsolete),
                               original.replace(" " + field, "")):
                    self.assertEqual(self.simulated_step(mutant)["status"], "FAIL")

    def test_transport_receipt_cannot_invent_owner_go_or_semantic_admission(self):
        for forged in ("owner_GO=YES", "release_admitted=YES",
                       "semantic_verified=YES", "release_tag=l0.42.0"):
            with self.subTest(field=forged):
                result = self.simulated_step(self.good_line() + " " + forged)
                self.assertEqual(result["status"], "FAIL")
                self.assertIn("unrecognized physical receipt fields", result["detail"])

    def test_bridge_failure_markers_cannot_be_overridden_by_final_pass(self):
        # One focused negative proof: zero-exit and a valid final receipt
        # cannot erase an explicit contradictory failure in the same stdout.
        clean = self.good_line() + "\n"
        self.assertEqual(self.simulated_step(clean)["status"], "PASS")
        for marker in ("ZIG_BRIDGE_FAIL", "ZIG_BRIDGE_BLOCKED"):
            with self.subTest(marker=marker):
                output = marker + " test_id=zig-migration-bridge-t5-exact-physical\n" + clean
                result = self.simulated_step(output)
                self.assertEqual((result["status"], result["exit"]), ("FAIL", 0))
                self.assertIn("contradictory Zig bridge receipt", result["detail"])

    def test_stderr_bridge_failure_cannot_be_hidden_by_stdout_pass(self):
        # A genuine final stdout receipt and zero exit are insufficient when
        # this same subprocess announces explicit transport failure on stderr.
        valid = self.good_line() + "\n"
        clean = self.simulated_step(valid, stderr="ordinary compiler notice\n")
        self.assertEqual((clean["status"], clean["exit"]), ("PASS", 0))
        for marker in ("ZIG_BRIDGE_FAIL", "ZIG_BRIDGE_BLOCKED"):
            with self.subTest(marker=marker):
                result = self.simulated_step(
                    valid,
                    stderr=marker + " test_id=zig-migration-bridge-t5-exact-physical\n",
                    rc=0,
                )
                self.assertEqual((result["status"], result["exit"]), ("FAIL", 0))
                self.assertIn("contradictory Zig bridge stderr status=" + marker,
                              result["detail"])

    def test_empty_stdout_exit_zero_is_not_physical_pass(self):
        result = self.simulated_step("")
        self.assertEqual((result["status"], result["exit"]), ("FAIL", 0))
        self.assertIn("ZIG_BRIDGE_RECEIPT_UNINFORMATIVE", result["detail"])
        self.assertIn("layer=transport", result["detail"])

    def test_receipt_in_stderr_only_is_not_a_valid_proof(self):
        result = self.simulated_step("", stderr=self.good_line())
        self.assertEqual(result["status"], "FAIL")

    def test_wrong_physical_sha_rejected(self):
        bad = self.good_line().replace(
            self.mod.BRIDGE_GOLDEN_SHA256, "0" * 64)
        self.assertEqual(self.simulated_step(bad)["status"], "FAIL")

    def test_unsupported_zig_version_rejected(self):
        bad = self.good_line().replace("zig=0.16.0", "zig=0.17.0")
        self.assertEqual(self.simulated_step(bad)["status"], "FAIL")

    def test_d10_executable_false_admission_rejected(self):
        bad = self.good_line().replace(
            "d10_executable=REJECTED", "d10_executable=ACCEPTED")
        self.assertEqual(self.simulated_step(bad)["status"], "FAIL")

    def test_wrong_sens_semantic_authority_rejected(self):
        bad = self.good_line().replace(
            "semantic_authority=SENS", "semantic_authority=Rust")
        self.assertEqual(self.simulated_step(bad)["status"], "FAIL")

    def test_untrusted_binary_sha_rejected(self):
        bad = self.good_line().replace("zig_binary_sha256=" + "a" * 64,
                                       "zig_binary_sha256=unverified")
        self.assertEqual(self.simulated_step(bad)["status"], "FAIL")

    def test_duplicate_receipt_rejected(self):
        line = self.good_line()
        self.assertEqual(self.simulated_step(line + "\n" + line)["status"], "FAIL")

    def test_lost_negative_controls_rejected(self):
        bad = self.good_line().replace("negative_gates=14", "negative_gates=0")
        self.assertEqual(self.simulated_step(bad)["status"], "FAIL")

    def test_incomplete_receipt_is_not_last_line(self):
        bad = self.good_line() + "\nUNVERIFIED-LATER"
        self.assertEqual(self.simulated_step(bad)["status"], "FAIL")

    def test_success_exit_cannot_override_missing_zig_proof_in_gate(self):
        result = self.simulated_step("")
        complete = [
            {"step": name, "status": "PASS"}
            for name in self.mod.REQUIRED_STEPS
            if name != "test_zig_codec_bridge"
        ] + [result]
        self.assertEqual(
            self.mod.gate_verdict(complete, self_test=False, skip_ladder=False),
            "FAIL",
        )

if __name__ == "__main__":
    unittest.main(verbosity=2)
