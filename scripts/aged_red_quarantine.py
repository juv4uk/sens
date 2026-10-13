#!/usr/bin/env python3
"""Administrative 24h+ failure quarantine. Never mutates CI conclusions or SENS semantics."""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

MARKER = "<!-- SENS-AGED-RED-QUARANTINE-24H -->"
UTC = dt.timezone.utc


def utc(s):
    t = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise ValueError("timezone required")
    return t.astimezone(UTC)


def candidates(runs, clock):
    """Quarantine is an administrative review queue, not a FLAKE stamp."""
    cutoff = clock - dt.timedelta(hours=24)
    found = {}
    for r in runs:
        if r.get("conclusion") != "failure":
            continue
        if r.get("path", "").endswith("/red-cause-router.yml"):
            continue
        when = utc(r["created_at"])
        if when > cutoff:
            continue
        ident = r["id"]
        if not isinstance(ident, int) or not r.get("html_url") or not r.get("head_sha"):
            raise ValueError("untraceable failed run")
        found[ident] = {
            "id": ident, "url": r["html_url"], "path": r.get("path", "UNKNOWN"),
            "branch": r.get("head_branch") or "UNKNOWN",
            "sha": r["head_sha"], "first_seen_at": r["created_at"],
            "age_hours": round((clock - when).total_seconds() / 3600, 1),
            "status": "Q_TRIAGE_24H", "cause": "UNCLASSIFIED",
            "owner": "swarm", "original_conclusion": "failure",
        }
    return found


def api(repo, token, verb, endpoint, data=None):
    url = "https://api.github.com/repos/" + repo + endpoint
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "sens-aged-red-quarantine",
    }
    raw = json.dumps(data).encode("utf-8") if data is not None else None
    if raw:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=raw, headers=headers, method=verb)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def iso(t):
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_window(repo, token, start, end, depth=0):
    """Time-shard dense GitHub searches; no successful audit on partial coverage."""
    period = iso(start) + ".." + iso(end)
    params = {"status": "failure", "created": period, "per_page": 100, "page": 1}
    first = api(repo, token, "GET", "/actions/runs?" + urllib.parse.urlencode(params))
    total = first.get("total_count")
    rows = first.get("workflow_runs")
    if type(total) is not int or not isinstance(rows, list):
        raise ValueError("missing workflow API count/items for " + period)
    # GitHub caps search results: split the interval instead of dropping anything.
    if total >= 1000:
        middle = start + (end - start) / 2
        if depth >= 20 or (end - start) <= dt.timedelta(seconds=2):
            return [], [period], 1
        middle = middle.replace(microsecond=0)
        if middle <= start or middle >= end:
            return [], [period], 1
        left, lg, lc = fetch_window(repo, token, start, middle, depth + 1)
        right, rg, rc = fetch_window(repo, token, middle, end, depth + 1)
        return left + right, lg + rg, 1 + lc + rc
    batch = list(rows)
    pages = (total + 99) // 100
    for page in range(2, pages + 1):
        params["page"] = page
        more = api(repo, token, "GET", "/actions/runs?" + urllib.parse.urlencode(params))
        items = more.get("workflow_runs", [])
        if not isinstance(items, list):
            raise ValueError("invalid API workflow_runs for " + period)
        batch.extend(items)
    if len(batch) < total:
        return batch, [period], 1
    return batch, [], 1


def scan(repo, token, clock, days):
    """Collect 24h+ failures in the rolling lookback, splitting every API cap."""
    upper = clock - dt.timedelta(hours=24)
    lower = clock - dt.timedelta(days=days)
    found = {}
    windows = 0
    incomplete = []
    while lower < upper:
        end = min(upper, lower + dt.timedelta(days=1))
        batch, gaps, calls = fetch_window(repo, token, lower, end)
        found.update(candidates(batch, clock))
        incomplete.extend(gaps)
        windows += calls
        lower = end
    return found, incomplete, windows


def render(found, incomplete, windows, clock, days, maximum=150):
    grouped = {}
    for run in found.values():
        key = (run["path"], run["branch"])
        grouped.setdefault(key, []).append(run)
    lines = [
        MARKER,
        "## КАРАНТИН RED 24h+ · операційна черга рою",
        "",
        "Оригінальні GitHub Actions conclusions **не змінені**. "
        "Це Q_TRIAGE для діагностики, **не FLAKE/TRANSITIONAL** і не дозвіл обходити required CI.",
        "",
        "Snapshot UTC: `" + iso(clock) + "`. Вікно: останні " + str(days) +
        " діб, тільки завершені `failure` віком ≥24 год. "
        "Клас причини невідомий без доказів; власник первинної діагностики — рій.",
        "",
        f"**Запусків в адміністративному карантині: {len(found)}. Груп workflow/branch: {len(grouped)}. "
        f"Вікон API: {windows}.**",
    ]
    if incomplete:
        lines += ["", "**PARTIAL/INCOMPLETE_API**: cap 1000 results/search; "
                  "не всі знайдені. Потрібно зменшити UTC-вікно:", ", ".join(incomplete)]
    else:
        lines += ["", "API-вибірка повна лише в межах вказаного часу; старші за це вікно не перевірені."]
    lines += ["", "| Workflow · гілка | Червоних | Останній RED (SHA) | Вік, год |",
              "|---|---:|---|---:|"]
    order = sorted(grouped.items(), key=lambda kv: max(x["age_hours"] for x in kv[1]), reverse=True)
    for (workflow, branch), xs in order[:maximum]:
        newest = max(xs, key=lambda x: utc(x["first_seen_at"]))
        path = workflow.replace("|", "/")[-72:]
        bn = branch.replace("|", "/")[-45:]
        lines.append(f"| `{path}` · `{bn}` | {len(xs)} | "
                     f"[{newest['id']}]({newest['url']}) `{newest['sha'][:12]}` | {newest['age_hours']} |")
    if len(order) > maximum:
        lines += ["", f"**TRUNCATED DISPLAY**: {len(order)-maximum} інших груп. "
                  "Жодну з них не оголошено зеленою."]
    lines += ["", "### Контракт Q_TRIAGE",
              "Рій зобов'язаний установити 4-класну причину та REGRESSION/TRANSITIONAL/FLAKE "
              "за доказами, додати ticket+owner+provenance, після чого усувати збій. "
              "Не штампувати FLAKE за віком. OWNER_UNCLEAR → вердикт власника один раз; "
              "решта — робота рою. Перегляд цієї черги кожні 2 години.",
              "",
              "Без точного успішного CI на SHA це не RESOLVED. Ніяких silent skip.",
              ""]
    return "\n".join(lines)


def publish(repo, token, issue, body):
    # Stable single comment, not hundreds of new issues or comments.
    found = None
    for page in range(1, 11):
        comments = api(repo, token, "GET", f"/issues/{issue}/comments?per_page=100&page={page}")
        for comment in comments:
            if MARKER in comment.get("body", ""):
                if found is not None:
                    raise ValueError("multiple quarantine report comments; manual reconciliation required")
                found = comment["id"]
        if len(comments) < 100:
            break
    else:
        raise ValueError("issue comment pagination incomplete")
    if found is not None:
        return api(repo, token, "PATCH", f"/issues/comments/{found}", {"body": body})
    return api(repo, token, "POST", f"/issues/{issue}/comments", {"body": body})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "juv4uk/sens"))
    p.add_argument("--issue", type=int, default=5741)
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    if not 1 <= args.days <= 60 or args.issue < 1 or args.repo.count("/") != 1:
        p.error("invalid scope")
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("::error::GITHUB_TOKEN required (fail closed)", file=sys.stderr)
        return 1
    try:
        clock = dt.datetime.now(UTC)
        found, gaps, windows = scan(args.repo, token, clock, args.days)
        body = render(found, gaps, windows, clock, args.days)
        if args.dry_run:
            print(body)
        else:
            comment = publish(args.repo, token, args.issue, body)
            print("Q_TRIAGE_24H issue_comment=" + str(comment.get("html_url", "")))
        print(f"Q_TRIAGE_24H runs={len(found)} windows={windows} gaps={len(gaps)}")
        # Even if the report posts, incomplete collection cannot be called a passed audit.
        if gaps:
            print("::error::INCOMPLETE_AGED_RED_INVENTORY " + ", ".join(gaps))
            return 1
        return 0
    except (OSError, ValueError, TypeError, KeyError, urllib.error.URLError) as exc:
        print("::error::AGED_RED_QUARANTINE_BLOCKED " + str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
