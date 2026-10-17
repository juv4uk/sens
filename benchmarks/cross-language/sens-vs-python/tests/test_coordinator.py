import sys
import json
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
from coordinate import create_run_directory, record_failure, validate_build_profile, validate_pair, validate_run_id


def run(output, samples=100, warmups=10):
    return {"status": "PASS", "parity": "PASS", "n": samples, "warmups": warmups,
            "samples": [{"ordinal": i + 1, "elapsed_ns": i + 1} for i in range(samples)], "output": output,
            "runtime_metadata": {"os": "Linux", "architecture": "x86_64"}}


class CoordinatorTests(unittest.TestCase):
  def test_pair_accepts_same_expected_result(self):
    validate_pair(run("987"), run(987), 987, "fib")


  def test_pair_rejects_semantic_mismatch(self):
    with self.assertRaisesRegex(RuntimeError, "differs"):
        validate_pair(run("987"), run(986), 987, "fib")


  def test_pair_rejects_incomplete_raw_samples(self):
    with self.assertRaisesRegex(RuntimeError, "exactly 100"):
        validate_pair(run("987", samples=99), run(987), 987, "fib")


  def test_pair_rejects_wrong_warmup_count(self):
    with self.assertRaisesRegex(RuntimeError, "exactly 10"):
        validate_pair(run("987", warmups=9), run(987), 987, "fib")

  def test_debug_runner_is_rejected_before_timing(self):
    with self.assertRaisesRegex(RuntimeError, "release build"):
        validate_build_profile("debug")
    self.assertEqual(validate_build_profile("release"), "release")

  def test_run_id_cannot_escape_evidence_directory(self):
    for value in ("..", "../outside", "/tmp/run", "bad/name"):
      with self.subTest(value=value), self.assertRaises(RuntimeError):
        validate_run_id(value)
    validate_run_id("20261017T051528Z")

  def test_started_run_failure_is_saved_with_exact_error(self):
    with tempfile.TemporaryDirectory() as temp_dir:
      directory = Path(temp_dir)
      record_failure(directory, "fib", RuntimeError("expected test failure"))
      record = json.loads((directory / "failure.json").read_text())
      self.assertEqual(record, {"status": "FAIL", "workload": "fib", "error": "expected test failure"})

  def test_existing_run_directory_is_never_overwritten(self):
    with tempfile.TemporaryDirectory() as temp_dir:
      root = Path(temp_dir)
      existing = create_run_directory(root, "fixed-run")
      marker = existing / "marker"
      marker.write_text("keep")
      with self.assertRaises(FileExistsError):
        create_run_directory(root, "fixed-run")
      self.assertEqual(marker.read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
