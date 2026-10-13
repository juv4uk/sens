#!/usr/bin/env python3
"""Operational CI cause routing; SENS semantics remain in SENS binary programs.

Distinct axes: cause (ownership) and stamp (failure treatment). Never guess either.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

SCHEMA = "sens-red-cause-v1"
CAUSES = {"OWNER_UNCLEAR", "AGENT_DEFECT", "TEST_DEFECT", "LEGACY_BINDING"}
STAMPS = {"REGRESSION", "TRANSITIONAL", "FLAKE"}
SAMPLE_HOURS = 24
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SHA = re.compile(r"^[0-9a-f]{40}$")
RUN = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/actions/runs/(\d+)$")


def utc(value):
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must have timezone")
    return parsed.astimezone(dt.timezone.utc)


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def validate_case(case, clock):
    errors = []
    ident = case.get("run_id")
    if type(ident) is not int or ident <= 0:
        errors.append("INVALID_RUN_ID")
    url = case.get("run_url", "")
    match = RUN.fullmatch(url) if isinstance(url, str) else None
    if not match or (type(ident) is int and str(ident) != match.group(3)):
        errors.append("INVALID_RUN_URL")
    try:
        first = utc(case["first_seen_at"])
        if first > clock + dt.timedelta(minutes=5):
            errors.append("FUTURE_FIRST_SEEN")
    except (ValueError, KeyError, TypeError, AttributeError):
        first = clock - dt.timedelta(hours=25)
        errors.append("MISSING_FIRST_SEEN")

    cause = case.get("cause")
    stamp = case.get("stamp")
    if cause not in CAUSES or stamp not in STAMPS:
        errors.append("UNCLASSIFIED")
        if clock - first >= dt.timedelta(hours=SAMPLE_HOURS):
            errors.append("ESCALATE_24H")
        return errors

    owner = case.get("owner")
    if not isinstance(owner, str) or not owner.strip():
        errors.append("MISSING_OWNER")
    if cause == "OWNER_UNCLEAR":
        if owner != "juv4uk":
            errors.append("OWNER_UNCLEAR_MUST_ROUTE_TO_OWNER")
        if case.get("state") == "resolved" and not case.get("ratified_rule"):
            errors.append("MISSING_RATIFIED_RULE")
    elif owner == "juv4uk":
        errors.append("SWARM_MUST_OWN_MECHANICAL_CAUSE")

    if cause == "LEGACY_BINDING" and not (case.get("legacy_marker") and case.get("provenance")):
        errors.append("MISSING_LEGACY_PROVENANCE")
    if stamp in {"FLAKE", "TRANSITIONAL"}:
        if not re.fullmatch(r"#\d+", str(case.get("ticket", ""))):
            errors.append("MISSING_QUARANTINE_TICKET")
        if not case.get("investigation"):
            errors.append("MISSING_INVESTIGATION")
        try:
            start = utc(case["since"])
            end = utc(case["expires"])
            if start > first or end <= start:
                errors.append("INVALID_QUARANTINE_DATES")
            if end <= clock:
                errors.append("EXPIRED_QUARANTINE")
        except (KeyError, TypeError, ValueError, AttributeError):
            errors.append("INVALID_QUARANTINE_DATES")
    state = case.get("state")
    if state not in {"open", "resolved"}:
        errors.append("INVALID_STATE")
    if state == "resolved":
        proof = case.get("proof_run_url", "")
        if not isinstance(proof, str) or not RUN.fullmatch(proof):
            errors.append("MISSING_PROOF_RUN")
        sha = case.get("proof_sha", "")
        if not SHA.fullmatch(sha if isinstance(sha, str) else ""):
            errors.append("MISSING_PROOF_SHA")
        if case.get("resolved_by") not in {"swarm", "owner"}:
            errors.append("MISSING_RESOLVER")
    return errors


def audit(records, clock):
    seen = set()
    findings = []
    for record in records:
        ident = record.get("run_id")
        if ident in seen:
            findings.append((ident, "DUPLICATE_RUN"))
        seen.add(ident)
        findings += [(ident, e) for e in validate_case(record, clock)]
    valid_resolved = [r for r in records if r.get("state") == "resolved" and
                      not validate_case(r, clock)]
    ownerless = sum(r.get("resolved_by") == "swarm" for r in valid_resolved)
    return findings, (ownerless, len(valid_resolved))


def api_get(url, token):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "sens-red-cause-router",
    })
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)


def failure_inventory(repo, token, clock, hours, max_pages):
    # APIs report workflow-level failures even when jobs API returns [].
    oldest = clock - dt.timedelta(hours=hours)
    result = {}
    for page in range(1, max_pages + 1):
        query = urllib.parse.urlencode({"status": "failure", "per_page": 100, "page": page})
        obj = api_get(f"https://api.github.com/repos/{repo}/actions/runs?{query}", token)
        runs = obj.get("workflow_runs", [])
        for run in runs:
            if run.get("path", "").endswith("/red-cause-router.yml"):
                continue
            try:
                when = utc(run["created_at"])
            except (KeyError, TypeError, ValueError, AttributeError):
                raise ValueError("workflow_run lacks verified created_at")
            if when >= oldest:
                result[run["id"]] = {
                    "run_id": run["id"], "run_url": run["html_url"],
                    "first_seen_at": run["created_at"],
                    "workflow": run.get("path", "UNKNOWN"),
                    "head_sha": run.get("head_sha", "UNKNOWN"),
                }
        if len(runs) < 100:
            return result
        if all(utc(x["created_at"]) < oldest for x in runs):
            return result
    raise ValueError("INCOMPLETE_INVENTORY: max page limit reached; no silent green")


def report(findings, stats, live=None):
    for ident, tag in findings[:60]:
        print(f"::error::SENS-RED run={ident} {tag}")
    if len(findings) > 60:
        print(f"::error::OMITTED_DISPLAY {len(findings)-60} additional findings; not counted as green")
    num, den = stats
    metric = "N/A" if den == 0 else f"{100*num/den:.1f}%"
    print(f"SENS_RED_CAUSE_SUMMARY findings={len(findings)} verified_swarm={num} verified_total={den} autonomy={metric}")
    if live is not None:
        print(f"SENS_RED_CAUSE_INVENTORY failed_runs={live}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as dst:
            dst.write(f"### SENS RED: cause routing\n\nUnresolved/audit findings: **{len(findings)}**. "
                      f"Verified without owner: **{num}/{den}** ({metric}). "
                      f"Run inventory: **{live if live is not None else 'offline'}**.\n")
    return 1 if findings else 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=["audit", "live"])
    p.add_argument("--ledger", default="knowledge/red-cause-ledger.json")
    p.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "juv4uk/sens"))
    p.add_argument("--hours", type=int, default=48)
    p.add_argument("--max-pages", type=int, default=10)
    args = p.parse_args()
    try:
        if not REPO.fullmatch(args.repo) or not 1 <= args.hours <= 720 or not 1 <= args.max_pages <= 100:
            raise ValueError("invalid repository or audit bounds")
        data = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
        if data.get("schema") != SCHEMA or not isinstance(data.get("cases"), list):
            raise ValueError("invalid cause ledger schema")
        clock = now_utc()
        findings, stats = audit(data["cases"], clock)
        live = None
        if args.mode == "live":
            token = os.environ.get("GITHUB_TOKEN")
            if not token:
                raise ValueError("missing GITHUB_TOKEN: cannot claim live coverage")
            inventory = failure_inventory(args.repo, token, clock, args.hours, args.max_pages)
            live = len(inventory)
            registered = {r.get("run_id") for r in data["cases"]}
            for ident, failed in sorted(inventory.items()):
                if ident not in registered:
                    findings.append((ident, "UNCLASSIFIED " + failed["run_url"]))
                    if clock - utc(failed["first_seen_at"]) >= dt.timedelta(hours=24):
                        findings.append((ident, "ESCALATE_24H SWARM_TRIAGE " + failed["run_url"]))
        return report(findings, stats, live)
    except (OSError, ValueError, KeyError, TypeError, urllib.error.URLError) as e:
        print("::error::SENS_RED_AUDIT_BLOCKED " + str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
