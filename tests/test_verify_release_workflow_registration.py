#!/usr/bin/env python3
"""Negative witnesses for independent release-preflight GitHub registration."""

import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "verify_release_workflow_registration.py"
SPEC = importlib.util.spec_from_file_location("sens_release_preflight_registration", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class RegistrationTests(unittest.TestCase):
    @staticmethod
    def active():
        return {
            "id": 123456,
            "name": "Release Preflight",
            "path": ".github/workflows/release-preflight.yml",
            "state": "active",
        }

    def test_only_exact_active_path_name_and_id_admitted(self):
        self.assertEqual(MODULE.validate(self.active()), self.active())

    def test_missing_or_disabled_workflow_never_admitted(self):
        for state in (None, "", "disabled_manually", "disabled_inactivity", "deleted", "unknown"):
            with self.subTest(state=state):
                payload = {**self.active(), "state": state}
                with self.assertRaisesRegex(MODULE.RegistrationBlocked, "expected active"):
                    MODULE.validate(payload)

    def test_forged_workflow_identity_or_malformed_api_response_is_blocked(self):
        for payload in (
            None,
            [],
            {},
            {**self.active(), "id": 0},
            {**self.active(), "id": True},
            {**self.active(), "id": "123456"},
            {**self.active(), "name": "Hosted CI"},
            {**self.active(), "path": ".github/workflows/ci-hosted.yml"},
        ):
            with self.subTest(payload=payload), self.assertRaises(MODULE.RegistrationBlocked):
                MODULE.validate(payload)

    def test_api_404_fails_closed(self):
        def missing(req, timeout=15):
            raise HTTPError(req.full_url, 404, "Not Found", {}, None)

        with self.assertRaisesRegex(MODULE.RegistrationBlocked, "HTTP 404"):
            MODULE.verify("juv4uk/sens", "test-token", missing)

    def test_actual_api_document_is_validated_not_assumed(self):
        def fake_open(payload):
            def open_response(req, timeout=15):
                self.assertEqual(req.full_url,
                                 "https://api.github.com/repos/juv4uk/sens/actions/workflows/release-preflight.yml")
                self.assertEqual(timeout, 15)
                return io.BytesIO(json.dumps(payload).encode("utf-8"))
            return open_response

        self.assertEqual(
            MODULE.verify("juv4uk/sens", "test-token", fake_open(self.active())),
            self.active(),
        )
        with self.assertRaisesRegex(MODULE.RegistrationBlocked, "workflow state"):
            MODULE.verify("juv4uk/sens", "test-token",
                          fake_open({**self.active(), "state": "disabled_manually"}))

    def test_absent_token_bad_repository_and_invalid_json_are_blocked(self):
        for repo in ("", "juv4uk", "juv4uk/sens/evil", "../sens", "https://github.com/juv4uk/sens"):
            with self.subTest(repo=repo), self.assertRaises(MODULE.RegistrationBlocked):
                MODULE.verify(repo, "test-token")
        with self.assertRaises(MODULE.RegistrationBlocked):
            MODULE.verify("juv4uk/sens", "")
        with self.assertRaisesRegex(MODULE.RegistrationBlocked, "cannot obtain trusted"):
            MODULE.verify("juv4uk/sens", "test-token", lambda req, timeout: io.BytesIO(b"<html>"))

    def test_active_hosted_ci_executes_registration_probe(self):
        source = (ROOT / ".github/workflows/ci-hosted.yml").read_text(encoding="utf-8")
        self.assertIn("python3 scripts/verify_release_workflow_registration.py", source)
        self.assertIn("test_verify_release_workflow_registration.py", source)
        self.assertIn("actions: read", source)
        self.assertIn("GITHUB_TOKEN: ${{ github.token }}", source)


if __name__ == "__main__":
    unittest.main()
