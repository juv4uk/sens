"""Fail closed unless the independent release-critical GitHub Actions checks pass.

No check status is inferred from a workflow name, old SHA, queued run, or
successful packaging job. The tag workflow executes this on the exact SHA.
"""

import json
import os
import re
import subprocess
import sys
from urllib.parse import urlsplit

REQUIRED_CHECKS = (
    "portable critical gates",
    "oracle-native-smoke",
    "Lisp-owned pair to real CPU, with fail-closed rejection",
    "Physical SENS T5 file-admission oracle",
    "triple",
    "physical T5 to D2 D3 D4 D7 runtime",
    "physical-binary-cli",
    "d2-grammar-audit",
    "focused release preflight",
    "Охоронець · Rust · Zig · SENS",
    # The real ci.yml/lisp-guards job runs native Zig T5M + SENS checks on main.
    # Use its exact published check-run name; never require a retired label.
    "Українська проєкція та заборона сирих літералів",
)

SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
REPO_RE = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")


def _trusted_actions_url(url, repo):
    """Accept only a real GitHub Actions run URL on the expected repository."""
    if not isinstance(url, str):
        return False
    try:
        parts = urlsplit(url)
    except ValueError:
        return False
    if parts.scheme != "https" or parts.netloc != "github.com" or parts.fragment:
        return False
    match = re.fullmatch(
        r"/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/actions/runs/[1-9][0-9]*"
        r"(?:/job/[1-9][0-9]*)?/?", parts.path
    )
    return match is not None and (
        repo is None or f"{match.group(1)}/{match.group(2)}" == repo
    )


def verify_check_runs(payload, sha, repo=None):
    """Return a check-run receipt, or reject any absent/red/pending/untrusted gate.

    Check-run IDs increase for reruns. Use the newest per exact name and SHA;
    never let an older green run override a newer failure or queued rerun.
    """
    if not isinstance(sha, str) or SHA_RE.fullmatch(sha) is None:
        raise ValueError("RELEASE_BLOCKED: invalid exact source SHA")
    pages = payload if isinstance(payload, list) else [payload]
    if not pages:
        raise ValueError("RELEASE_BLOCKED: no check-run API pages")
    by_name = {}
    for page in pages:
        if not isinstance(page, dict) or not isinstance(page.get("check_runs"), list):
            raise ValueError("RELEASE_BLOCKED: malformed check-run API response")
        for run in page["check_runs"]:
            if not isinstance(run, dict):
                raise ValueError("RELEASE_BLOCKED: malformed check-run record")
            name = run.get("name")
            if name not in REQUIRED_CHECKS:
                continue
            rid = run.get("id")
            if not isinstance(rid, int) or rid <= 0 or isinstance(rid, bool):
                raise ValueError(f"RELEASE_BLOCKED: invalid check-run ID for {name}")
            if run.get("head_sha") != sha:
                raise ValueError(f"RELEASE_BLOCKED: wrong check-run SHA for {name}")
            if rid > by_name.get(name, {}).get("id", 0):
                by_name[name] = run

    receipt = []
    for name in REQUIRED_CHECKS:
        run = by_name.get(name)
        if run is None:
            raise ValueError(f"RELEASE_BLOCKED: missing exact-SHA check {name}")
        app = run.get("app") or {}
        url = run.get("details_url") or ""
        if not isinstance(app, dict) or app.get("slug") != "github-actions" or not _trusted_actions_url(url, repo):
            raise ValueError(f"RELEASE_BLOCKED: untrusted check provider for {name}")
        if run.get("status") != "completed" or run.get("conclusion") != "success":
            raise ValueError(
                f"RELEASE_BLOCKED: {name} not green "
                f"({run.get('status')}/{run.get('conclusion')})"
            )
        receipt.append({"name": name, "id": run["id"], "sha": sha,
                        "status": "success", "url": url})
    return receipt


def main(argv):
    if len(argv) != 3:
        raise ValueError("usage: verify_release_ci.py GIT_SHA OWNER/REPO")
    sha, repo = argv[1:]
    if SHA_RE.fullmatch(sha) is None or REPO_RE.fullmatch(repo) is None:
        raise ValueError("RELEASE_BLOCKED: malformed SHA or repository")
    request = ["gh", "api", "--paginate", "--slurp", "-H",
               "Accept: application/vnd.github+json",
               f"repos/{repo}/commits/{sha}/check-runs?per_page=100"]
    result = subprocess.run(request, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise ValueError("RELEASE_BLOCKED: cannot retrieve live GitHub check-runs")
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("RELEASE_BLOCKED: invalid GitHub check-run JSON") from exc
    receipt = verify_check_runs(data, sha, repo)
    print(json.dumps({"schema": "sens-release-ci-checks/v1", "sha": sha,
                      "repo": repo, "checks": receipt}, sort_keys=True))
    print(f"RELEASE_REQUIRED_CI_PASS {len(receipt)}/{len(REQUIRED_CHECKS)} exact-SHA gates")


if __name__ == "__main__":
    try:
        main(sys.argv)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
