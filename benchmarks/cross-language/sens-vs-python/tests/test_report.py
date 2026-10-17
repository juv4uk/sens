import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
from report import nearest_rank, render, summarize
from svg import boxplot_svg, histogram_svg


class ReportTests(unittest.TestCase):
  def test_nearest_rank_percentiles_use_ceiling_rank(self):
    self.assertEqual(nearest_rank([9, 1, 8, 2], 50), 2)
    self.assertEqual(nearest_rank(list(range(1, 101)), 95), 95)
    self.assertEqual(nearest_rank(list(range(1, 101)), 99), 99)


  def test_summary_reports_raw_count_and_rss(self):
    raw = {"implementation": "SENS", "n": 4, "samples": [{"elapsed_ns": n} for n in [9, 1, 8, 2]],
           "rss_kib": {"baseline_after_warmup": 100, "peak_vmhwm": 120}}
    result = summarize(raw)
    self.assertEqual(result["n"], 4)
    self.assertEqual(result["median_ns"], 5)
    self.assertEqual(result["p95_ns"], 9)
    self.assertEqual(result["rss_kib"]["peak_vmhwm"], 120)


  def test_svg_graphs_are_generated_from_raw_samples(self):
    series = {"SENS": [2, 3, 8, 9], "CPython": [1, 4, 5, 6]}
    self.assertIn("latency (ns)", boxplot_svg(series, "fib"))
    self.assertIn("histogram", histogram_svg(series, "fib"))

  def test_report_contains_parameters_memory_and_ratio_definition(self):
    def result(name, times):
      return {"implementation": name, "n": len(times),
              "samples": [{"elapsed_ns": value} for value in times],
              "rss_kib": {"baseline_after_warmup": 100, "peak_vmhwm": 120,
                          "delta_peak_from_baseline": 20}}
    manifest = {"workloads": [{"id": "fib", "status": "candidate", "parameters": {"N": 16}}]}
    paired = {"fib": {"SENS": result("SENS", [20, 20]),
                       "CPython source": result("CPython source", [10, 10])}}
    report = render(Path("run-1"), manifest, paired)
    self.assertIn("N=16", report)
    self.assertIn("100/120/20", report)
    self.assertIn("0.500×", report)
    self.assertIn("менший час CPython", report)


if __name__ == "__main__":
    unittest.main()
