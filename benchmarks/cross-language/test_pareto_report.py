#!/usr/bin/env python3
"""Fast deterministic checks for pareto_report.py accounting boundaries."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "pareto_report.py"


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


class ParetoReportSmoke(unittest.TestCase):
    def make_inputs(self, root: Path) -> tuple[Path, Path, Path]:
        external = root / "external.tsv"
        sens = root / "sens.tsv"
        footprint = root / "footprint.tsv"

        exec_fields = [
            "semantic_generation",
            "runtime",
            "workload",
            "phase",
            "i_refs",
            "wall_s",
        ]
        write_tsv(
            external,
            exec_fields,
            [
                {
                    "semantic_generation": "external-control-v2",
                    "runtime": "cpython",
                    "workload": "fib",
                    "phase": "full",
                    "i_refs": 100,
                    "wall_s": 1.0,
                },
                {
                    "semantic_generation": "external-control-v2",
                    "runtime": "cpython",
                    "workload": "ackermann",
                    "phase": "full",
                    "i_refs": 200,
                    "wall_s": 2.0,
                },
            ],
        )
        write_tsv(
            sens,
            exec_fields,
            [
                {
                    "semantic_generation": "contract-11-6-exact-d1-d7",
                    "runtime": "sens-exact",
                    "workload": "fib",
                    "phase": "full",
                    "i_refs": 150,
                    "wall_s": 1.1,
                },
                {
                    "semantic_generation": "contract-11-6-exact-d1-d7",
                    "runtime": "sens-exact",
                    "workload": "ackermann",
                    "phase": "full",
                    "i_refs": 180,
                    "wall_s": 1.8,
                },
            ],
        )
        footprint_fields = [
            "runtime",
            "workload",
            "artifact_bytes",
            "text_section_bytes",
            "rss_bytes",
            "program_source_bytes",
        ]
        # Deliberately only fib. Ackermann must remain N/A after the join.
        write_tsv(
            footprint,
            footprint_fields,
            [
                {
                    "semantic_generation": "external-control-v2",
                    "runtime": "cpython",
                    "workload": "fib",
                    "artifact_bytes": 1000,
                    "text_section_bytes": 500,
                    "rss_bytes": 10000,
                    "program_source_bytes": 100,
                },
                {
                    "semantic_generation": "contract-11-6-exact-d1-d7",
                    "runtime": "sens-exact",
                    "workload": "fib",
                    "artifact_bytes": 800,
                    "text_section_bytes": 400,
                    "rss_bytes": 9000,
                    "program_source_bytes": 80,
                },
            ],
        )
        return external, sens, footprint

    def run_report(
        self,
        root: Path,
        semantic: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        external, sens, footprint = self.make_inputs(root)
        out = root / "out"
        cmd = [
            sys.executable,
            str(SCRIPT),
            "--external",
            str(external),
            "--sens",
            str(sens),
            "--footprint",
            str(footprint),
            "--out",
            str(out),
        ]
        if semantic is not None:
            cmd += ["--semantic-json", str(semantic)]
        return subprocess.run(cmd, capture_output=True, text=True, check=False)

    def test_footprint_never_crosses_workload_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            proc = self.run_report(root)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            rows = list(
                csv.DictReader(
                    (root / "out" / "joined.tsv").open(encoding="utf-8"),
                    delimiter="\t",
                )
            )
            keyed = {(row["runtime"], row["workload"]): row for row in rows}
            self.assertEqual(keyed[("cpython", "fib")]["artifact_bytes"], "1000")
            self.assertEqual(keyed[("cpython", "fib")]["rss_bytes"], "10000")
            self.assertEqual(keyed[("cpython", "ackermann")]["artifact_bytes"], "")
            self.assertEqual(keyed[("cpython", "ackermann")]["rss_bytes"], "")

    def test_semantic_vector_requires_explicit_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            semantic = root / "semantic.json"
            semantic.write_text(
                json.dumps(
                    {
                        "source_issue": "#1973",
                        "contract": "11.6",
                        "completeness": "family-only",
                    }
                ),
                encoding="utf-8",
            )
            proc = self.run_report(root, semantic)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("scope", proc.stderr)

    def test_cross_contract_semantic_vector_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            semantic = root / "semantic.json"
            semantic.write_text(
                json.dumps(
                    {
                        "source_issue": "#1973",
                        "contract": "11.5",
                        "scope": "selector-family:D3-D6",
                        "completeness": "family-only",
                    }
                ),
                encoding="utf-8",
            )
            proc = self.run_report(root, semantic)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("contract mismatch", proc.stderr)

    def test_family_scope_is_preserved_not_promoted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            semantic = root / "semantic.json"
            semantic.write_text(
                json.dumps(
                    {
                        "source_issue": "#1973",
                        "contract": "11.6",
                        "scope": "selector-family:D3-D6",
                        "completeness": "family-only",
                        "metrics": {"generated_residents": 28},
                    }
                ),
                encoding="utf-8",
            )
            proc = self.run_report(root, semantic)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads((root / "out" / "pareto.json").read_text(encoding="utf-8"))
            sens_rows = [row for row in payload["joined"] if row["runtime"] == "sens-exact"]
            self.assertTrue(sens_rows)
            self.assertTrue(
                all(row["semantic_completeness"] == "family-only" for row in sens_rows)
            )
            self.assertTrue(
                all("selector-family:D3-D6" in row["semantic_axis"] for row in sens_rows)
            )
            self.assertFalse(payload["cross_language_semantic_comparable"])


if __name__ == "__main__":
    unittest.main()
