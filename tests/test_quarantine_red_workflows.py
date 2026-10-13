"""Quarantine the workflow metadata, never change semantic/test verdicts."""
import importlib.util
from pathlib import Path
import unittest

P = Path(__file__).resolve().parents[1] / "scripts/quarantine_red_workflows.py"
spec = importlib.util.spec_from_file_location("quarantine_red_workflows", P)
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)
HEAD = "a" * 40


class WorkflowQuarantineTests(unittest.TestCase):
    def test_latest_main_red_is_immediate_and_keeps_original_failure(self):
        def run(n, path, conclusion="failure", status="completed"):
            return {"head_sha": HEAD, "head_branch": "main", "status": status,
                    "conclusion": conclusion, "path": path, "id": n, "created_at": "2026-10-13T18:00:00Z"}
        path = ".github/workflows/domain-ladder.yml"
        samples = [run(5, path), run(6, path), run(7, "other.yml", "success"),
                   run(8, ".github/workflows/red-cause-router.yml"),
                   run(9, ".github/workflows/ci-hosted.yml", status="in_progress")]
        original = q.api
        try:
            def fake(repo, token, method, endpoint, data=None):
                if endpoint == "/git/ref/heads/main":
                    return {"object": {"sha": HEAD}}
                return {"total_count": len(samples), "workflow_runs": samples}
            q.api = fake
            sha, found, pending, seen = q.snapshot("juv4uk/sens", "fake")
        finally:
            q.api = original
        self.assertEqual(sha, HEAD)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[path]["id"], 6)
        self.assertEqual(found[path]["cause"], "UNCLASSIFIED")
        self.assertEqual(found[path]["original_conclusion"], "failure")
        self.assertEqual(pending, 1)
        self.assertEqual(seen, 5)
        rendered = q.render("juv4uk/sens", sha, found, pending, seen)
        self.assertIn(q.MARKER, rendered)
        self.assertIn("Q_WORKFLOW_NOW", rendered)
        self.assertIn("https://github.com/juv4uk/sens/actions/runs/6", rendered)
        self.assertIn("не зелений CI", rendered)

    def test_fail_closed_on_api_truncation(self):
        old = q.api
        try:
            q.api = lambda repo, token, method, endpoint, data=None: (
                {"object": {"sha": HEAD}} if endpoint == "/git/ref/heads/main" else
                {"total_count": 4, "workflow_runs": []})
            with self.assertRaisesRegex(ValueError, "pagination"):
                q.snapshot("juv4uk/sens", "fake")
        finally:
            q.api = old


if __name__ == "__main__":
    unittest.main()
