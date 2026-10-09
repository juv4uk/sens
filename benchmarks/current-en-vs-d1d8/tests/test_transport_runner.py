import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("transport_runner", ROOT / "transport_runner.py")
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)


class TransportRunnerTests(unittest.TestCase):
    def test_helper_output_keeps_unresolved_framing_null(self):
        parsed = transport.parse_helper_output(
            "TRACE_HEX=69643a44333a303031\n"
            "VALUE_HEX=2829\n"
            "OUTPUT_HEX=\n"
            "SOURCE_BYTES=12\n"
            "LOWERED_AST_NODES=3\n"
            "SEMANTIC_PAYLOAD_BITS=13\n"
            "FRAMING_BITS=NA\n"
            "TAIL_UNUSED_BITS=3\n"
            "TOTAL_WIRE_BITS=NA\n"
            "PACKED_BYTES=2\n"
            "PAYLOAD_CONTAINER_BITS=16\n"
            "PACKING_EFFICIENCY=0.8125\n"
            "CANONICAL_ARTIFACT_BYTES=NA\n"
        )
        self.assertEqual(parsed["trace"], "id:D3:001")
        self.assertEqual(parsed["value"], "()")
        self.assertEqual(parsed["metrics"]["semantic_payload_bits"], 13)
        self.assertIsNone(parsed["metrics"]["framing_bits"])
        self.assertIsNone(parsed["metrics"]["total_wire_bits"])
        self.assertEqual(parsed["metrics"]["packed_bytes"], 2)
        self.assertAlmostEqual(parsed["metrics"]["packing_efficiency"], 0.8125)

    def test_english_lane_can_report_only_surface_and_ast_metrics(self):
        parsed = transport.parse_helper_output(
            "TRACE_HEX=69643a44333a303031\n"
            "VALUE_HEX=2829\n"
            "OUTPUT_HEX=\n"
            "SOURCE_BYTES=10\n"
            "LOWERED_AST_NODES=3\n"
            "SEMANTIC_PAYLOAD_BITS=NA\n"
            "FRAMING_BITS=NA\n"
            "TAIL_UNUSED_BITS=NA\n"
            "TOTAL_WIRE_BITS=NA\n"
            "PACKED_BYTES=NA\n"
            "PAYLOAD_CONTAINER_BITS=NA\n"
            "PACKING_EFFICIENCY=NA\n"
            "CANONICAL_ARTIFACT_BYTES=NA\n"
        )
        metrics = parsed["metrics"]
        self.assertEqual(metrics["source_bytes"], 10)
        self.assertEqual(metrics["lowered_ast_nodes"], 3)
        self.assertIsNone(metrics["semantic_payload_bits"])
        self.assertIsNone(metrics["packed_bytes"])

    def test_manifest_rejects_blocked_rows_in_preflight_fixture(self):
        data = {
            "schema": transport.WORKLOAD_SCHEMA,
            "workloads": [{"id": "x", "status": "blocked"}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must be ready"):
                transport.load_manifest(path)


if __name__ == "__main__":
    unittest.main()
