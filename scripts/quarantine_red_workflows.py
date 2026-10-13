#!/usr/bin/env python3
"""Quarantine FAILED workflows on the current main SHA as administrative evidence.

No workflow is disabled, no test is skipped, no failure is relabeled FLAKE.
This is GitHub Actions metadata transport, not SENS language semantics.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

MARKER = "<!-- SENS-RED-WORKFLOW-IMMEDIATE-QUARANTINE -->"
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SHA = re.compile(r"^[0-9a-f]{40}$")


def api(repo, token, method, endpoint, data=None):
    request = urllib.request.Request(
        "https://api.github.com/repos/" + repo + endpoint,
        data=json.dumps(data).encode("utf-8") if data is not None else None,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "sens-red-workflow-quarantine",
        },
        method=method,
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.load(response)


def snapshot(repo, token):
    head = api(repo, token, "GET", "/git/ref/heads/main")["object"]["sha"]
    if not SHA.fullmatch(head):
        raise ValueError("invalid main SHA")
    found = {}
    in_progress = 0
    total_seen = 0
    for page in range(1, 11):
        query = urllib.parse.urlencode({"head_sha": head, "per_page": 100, "page": page})
        data = api(repo, token, "GET", "/actions/runs?" + query)
        runs = data.get("workflow_runs")
        count = data.get("total_count")
        if not isinstance(runs, list) or type(count) is not int:
            raise ValueError("incomplete workflow API payload")
        total_seen += len(runs)
        for r in runs:
            if r.get("head_sha") != head or r.get("head_branch") != "main":
                continue
            status = r.get("status")
            if status != "completed":
                in_progress += 1
                continue
            if r.get("conclusion") != "failure":
                continue
            if r.get("path", "").endswith("/red-cause-router.yml"):
                # Prevent the observer from marking itself as a semantic failure.
                # An observer failure still remains a normal RED in GitHub.
                continue
            workflow = r.get("path")
            ident = r.get("id")
            if not isinstance(workflow, str) or not workflow.startswith(".github/workflows/"):
                raise ValueError("invalid failed workflow path")
            if type(ident) is not int or ident < 1:
                raise ValueError("invalid failed workflow run ID")
            existing = found.get(workflow)
            if existing is None or ident > existing["id"]:
                found[workflow] = {
                    "path": workflow,
                    "id": ident,
                    "head_sha": head,
                    "created_at": r.get("created_at", "UNKNOWN"),
                    "original_conclusion": "failure",
                    "quarantine": "Q_WORKFLOW_NOW",
                    "cause": "UNCLASSIFIED",
                    "owner": "swarm",
                }
        if total_seen >= count:
            return head, found, in_progress, total_seen
        if not runs:
            raise ValueError("truncated workflow API pagination")
    raise ValueError("INCOMPLETE_WORKFLOW_SCAN: over 1000 runs at one SHA")


def render(repo, head, found, pending, seen):
    lines = [
        MARKER,
        "## НЕГАЙНИЙ КАРАНТИН ЧЕРВОНИХ WORKFLOW — main",
        "",
        "**Q_WORKFLOW_NOW** — адміністративна черга рою, без затримки 24 години. "
        "Це не `FLAKE` / `TRANSITIONAL`, не зелений CI і не дозвіл вимкнути required checks.",
        "",
        "Поточний `main`: `" + head + "`. "
        "Підтверджено `conclusion=failure` для **" + str(len(found)) + "** різних workflow.",
        "Усього перевірено запусків на цьому SHA: **" + str(seen) +
        "**; ще незавершених у вибірці: **" + str(pending) + "**.",
        "Workflow, які не запускалися на цьому SHA, не вважаються перевіреними.",
        "",
        "| Workflow | Запуск GitHub | Карантин / відповідальний |",
        "|---|---|---|",
    ]
    for r in sorted(found.values(), key=lambda x: x["path"]):
        name = r["path"].replace("|", "/").replace("`", "'")
        url = f"https://github.com/{repo}/actions/runs/{r['id']}"
        lines.append(f"| `{name}` | [#{r['id']}]({url}) | `Q_WORKFLOW_NOW` · `UNCLASSIFIED` · swarm |")
    lines += [
        "",
        "Далі: рій класифікує причину (OWNER_UNCLEAR / AGENT_DEFECT / TEST_DEFECT / "
        "LEGACY_BINDING), додає логи/відтворення/provenance та доводить виправлення CI "
        "на точному SHA. Власник отримує тільки невирішене нормативне питання.",
        "Історичні RED 24h+ відстежує окрема черга; зняття карантину "
        "лише після перевіреного успішного виконання.",
        "",
    ]
    return "\n".join(lines)


def publish(repo, token, issue, body):
    matches = []
    for page in range(1, 11):
        comments = api(repo, token, "GET", f"/issues/{issue}/comments?per_page=100&page={page}")
        if not isinstance(comments, list):
            raise ValueError("comments API not a list")
        for c in comments:
            if MARKER in str(c.get("body", "")):
                matches.append(c["id"])
        if len(comments) < 100:
            break
    else:
        raise ValueError("incomplete comment enumeration")
    if len(matches) > 1:
        raise ValueError("duplicate quarantine comments: no blind overwrite")
    if matches:
        return api(repo, token, "PATCH", f"/issues/comments/{matches[0]}", {"body": body})
    return api(repo, token, "POST", f"/issues/{issue}/comments", {"body": body})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "juv4uk/sens"))
    p.add_argument("--issue", type=int, default=5741)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    if not REPO.fullmatch(args.repo) or args.issue < 1:
        p.error("invalid repo or issue")
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("::error::MISSING_GITHUB_TOKEN", file=sys.stderr)
        return 1
    try:
        head, failed, pending, seen = snapshot(args.repo, token)
        if not failed:
            print("::warning::NO_CURRENT_HEAD_RED — retaining prior quarantine; absent rerun is not SUCCESS")
            return 0
        body = render(args.repo, head, failed, pending, seen)
        if args.dry_run:
            print(body)
        else:
            response = publish(args.repo, token, args.issue, body)
            print("Q_WORKFLOW_NOW comment=" + str(response.get("html_url", "")))
        print(f"Q_WORKFLOW_NOW head={head} failed_workflows={len(failed)} pending={pending} runs_checked={seen}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, urllib.error.URLError) as exc:
        print("::error::WORKFLOW_QUARANTINE_BLOCKED " + str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
