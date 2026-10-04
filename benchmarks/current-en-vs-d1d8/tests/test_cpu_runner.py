import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cpu_runner", ROOT / "cpu_runner.py")
cpu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cpu)


class CpuRunnerTests(unittest.TestCase):
    def test_parse_helper_output(self):
        parsed = cpu.parse_helper_output(
            "ELAPSED_NS=42\n"
            "TRACE_HEX=69643a44333a303031\n"
            "VALUE_HEX=2829\n"
            "OUTPUT_HEX=\n"
        )
        self.assertEqual(parsed["elapsed_ns"], 42)
        self.assertEqual(parsed["trace"], "id:D3:001")
        self.assertEqual(parsed["value"], "()")
        self.assertEqual(parsed["output"], "")

    def test_manifest_rejects_duplicate_workload_ids(self):
        data = {
            "schema": cpu.WORKLOAD_SCHEMA,
            "workloads": [
                {"id": "x", "status": "blocked"},
                {"id": "x", "status": "blocked"},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "m.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate workload id"):
                cpu.load_manifest(path)

    def test_production_manifest_marks_all_headline_workloads_explicitly(self):
        data = cpu.load_manifest(ROOT / "workloads.json")
        ids = {item["id"] for item in data["workloads"]}
        self.assertEqual(
            ids,
            {
                "ackermann",
                "assoc",
                "closures",
                "evenodd",
                "fib",
                "flatten",
                "lists",
                "loop",
                "mapfold",
                "member",
                "tree",
            },
        )
        self.assertTrue(all(item["status"] == "blocked" for item in data["workloads"]))


if __name__ == "__main__":
    unittest.main()
