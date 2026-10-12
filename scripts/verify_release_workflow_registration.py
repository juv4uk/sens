#!/usr/bin/env python3
"""Read-only, fail-closed GitHub registration probe for independent Release Preflight.

A YAML file in main and a passing YAML path-scope unit test are NOT proof that
GitHub Actions has registered its workflow. A separate full-workspace
Release Preflight job must exist and be active before release GO.
"""

from __future__ import annotations

import json
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

WORKFLOW_PATH = ".github/workflows/release-preflight.yml"
WORKFLOW_NAME = "Release Preflight"
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\\Z")


class RegistrationBlocked(ValueError):
    """Registration evidence missing, incomplete, or untrusted."""


def validate(payload: object) -> dict:
    """Validate actual GitHub Actions workflow API fields; never assume active."""
    if not isinstance(payload, dict):
        raise RegistrationBlocked("RELEASE_PREFLIGHT_BLOCKED: non-object workflow response")
    if payload.get("path") != WORKFLOW_PATH:
        raise RegistrationBlocked("RELEASE_PREFLIGHT_BLOCKED: wrong workflow path")
    if payload.get("name") != WORKFLOW_NAME:
        raise RegistrationBlocked("RELEASE_PREFLIGHT_BLOCKED: wrong workflow name")
    workflow_id = payload.get("id")
    if type(workflow_id) is not int or workflow_id <= 0:
        raise RegistrationBlocked("RELEASE_PREFLIGHT_BLOCKED: invalid workflow id")
    state = payload.get("state")
    if state != "active":
        raise RegistrationBlocked(f"RELEASE_PREFLIGHT_BLOCKED: workflow state {state!r} (expected active)")
    return {"id": workflow_id, "path": WORKFLOW_PATH, "name": WORKFLOW_NAME, "state": state}


def verify(repo: str, token: str, opener=urlopen) -> dict:
    if not isinstance(repo, str) or not REPOSITORY.fullmatch(repo):
        raise RegistrationBlocked("RELEASE_PREFLIGHT_BLOCKED: malformed repository")
    if not isinstance(token, str) or not token.strip():
        raise RegistrationBlocked("RELEASE_PREFLIGHT_BLOCKED: missing GitHub Actions read token")
    url = f"https://api.github.com/repos/{repo}/actions/workflows/release-preflight.yml"
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "sens-release-registration-probe",
        },
    )
    try:
        with opener(request, timeout=15) as response:
            payload = json.load(response)
    except HTTPError as exc:
        raise RegistrationBlocked(
            f"RELEASE_PREFLIGHT_BLOCKED: GitHub workflow API HTTP {exc.code}"
        ) from exc
    except (URLError, OSError, TimeoutError, ValueError) as exc:
        raise RegistrationBlocked(
            f"RELEASE_PREFLIGHT_BLOCKED: cannot obtain trusted GitHub workflow state ({type(exc).__name__})"
        ) from exc
    return validate(payload)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise RegistrationBlocked("usage: verify_release_workflow_registration.py owner/repo")
    receipt = verify(argv[1], os.environ.get("GITHUB_TOKEN", ""))
    print(json.dumps({"schema": "sens-release-preflight-registration/v1", **receipt}, sort_keys=True))
    print(f"RELEASE_PREFLIGHT_REGISTRATION_PASS id={receipt['id']} state=active")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except RegistrationBlocked as exc:
        raise SystemExit(str(exc)) from exc
