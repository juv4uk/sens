"""One targeted mechanical test for Q_TRIAGE_24H and non-suppression."""
import datetime as dt
import importlib.util
import pathlib
import unittest

P = pathlib.Path(__file__).resolve().parents[1] / "scripts/aged_red_quarantine.py"
spec = importlib.util.spec_from_file_location("aged_red_quarantine", P)
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)
CLOCK = dt.datetime(2026, 10, 13, 18, 0, tzinfo=dt.timezone.utc)


class AgedRedQuarantine(unittest.TestCase):
    def test_24h_boundary_provenance_no_false_flake_and_single_report(self):
        def run(n, age, conclusion="failure"):
            return {
                "id": n, "created_at": q.iso(CLOCK - dt.timedelta(hours=age)),
                "conclusion": conclusion, "html_url": f"https://github.com/juv4uk/sens/actions/runs/{n}",
                "head_sha": "a" * 40, "head_branch": "main",
                "path": ".github/workflows/domain-ladder.yml",
            }
        got = q.candidates([run(1, 23), run(2, 24), run(3, 48),
                            run(4, 72, "success")], CLOCK)
        self.assertEqual(set(got), {2, 3})
        self.assertTrue(all(x["status"] == "Q_TRIAGE_24H" and
                            x["cause"] == "UNCLASSIFIED" and
                            x["original_conclusion"] == "failure" for x in got.values()))
        body = q.render(got, [], 1, CLOCK, 7)
        self.assertIn(q.MARKER, body)
        self.assertIn("Червоних", body)
        self.assertIn("не FLAKE/TRANSITIONAL", body)
        self.assertEqual(body.count("| `.github/workflows/domain-ladder.yml`"), 1)
        self.assertIn("INCOMPLETE_API", q.render(got, ["over-cap"], 1, CLOCK, 7))


if __name__ == "__main__":
    unittest.main()
