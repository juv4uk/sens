#!/usr/bin/env python3
"""Перевіряє semantic ownership inventory і детерміновано генерує звіт."""

from __future__ import annotations

import argparse
import collections
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAP_PATH = ROOT / "knowledge" / "semantic-ownership.lisp"
REPORT_PATH = ROOT / "docs" / "semantic-ownership-report.md"
META_EVIDENCE_PATH = ROOT / "knowledge" / "meta-eval-evidence.lisp"

CLASSES = {
    "canon-ground",
    "canon-operation",
    "necessary-form",
    "host-observation",
    "host-authorization",
    "host-mechanism",
    "lisp-owned",
    "derived-tooling",
    "unknown",
}
STATUSES = {"confirmed", "partial", "broken", "unknown"}
LAYERS = {
    "canon",
    "bootstrap",
    "stdlib",
    "reasoning",
    "knowledge",
    "self-hosting",
    "host-capability",
    "tooling",
}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
SID8 = re.compile(r"^[01]{8}$")
QUOTED_SID8_OWNERSHIP = re.compile(r'^\(ownership\s+\S+\s+"[01]{8}"(?:\s|\))')


@dataclass(frozen=True)
class Ownership:
    key: str
    semantic_id: str
    owner_class: str
    layer: str
    status: str
    policy_candidate: str
    behavior: str
    implementation_paths: str
    evidence_paths: str
    previous_owner: str
    migration_ref: str


@dataclass(frozen=True)
class Migration:
    key: str
    from_owner: str
    to_owner: str
    status: str
    commit: str
    behavior: str
    evidence_paths: str


def forms(path: Path) -> list[list[str]]:
    parsed: list[list[str]] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        if not (line.startswith("(") and line.endswith(")")):
            raise ValueError(f"{path}:{number}: очікувалася одна завершена форма на рядок")
        try:
            tokens = shlex.split(line[1:-1], comments=False, posix=True)
        except ValueError as error:
            raise ValueError(f"{path}:{number}: {error}") from error
        if tokens:
            parsed.append(tokens)
    return parsed


def require_bare_semantic_identity_syntax() -> None:
    for number, raw in enumerate(MAP_PATH.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if QUOTED_SID8_OWNERSHIP.match(line):
            raise ValueError(
                f"{MAP_PATH}:{number}: semantic identity must be exact bare SID8, not a quoted String"
            )


def split_paths(text: str) -> list[str]:
    if text == "-":
        return []
    return [item for item in text.split(";") if item]


def require_paths(paths: list[str], context: str) -> None:
    for relative in paths:
        if not (ROOT / relative).exists():
            raise ValueError(f"{context}: referenced path не існує: {relative}")


def unresolved_required_meta_rows() -> list[tuple[str, str]]:
    unresolved: list[tuple[str, str]] = []
    for tokens in forms(META_EVIDENCE_PATH):
        if tokens[0] != "row":
            continue
        if len(tokens) != 8:
            raise ValueError(
                f"{META_EVIDENCE_PATH}: meta-eval row має неочікувану форму: {tokens}"
            )
        _, key, required, status, *_ = tokens
        if required == "yes" and status != "confirmed":
            unresolved.append((key, status))
    return unresolved


def require_cross_evidence_gates(ownership: list[Ownership]) -> None:
    meta = next((row for row in ownership if row.key == "meta-evaluator"), None)
    if meta is None:
        return
    if meta.status != "confirmed":
        return

    unresolved = unresolved_required_meta_rows()
    if unresolved:
        detail = ", ".join(f"{key}={status}" for key, status in unresolved)
        raise ValueError(
            "meta-evaluator ownership не може бути confirmed, поки required "
            f"meta-eval evidence має unresolved rows: {detail}"
        )


def load() -> tuple[list[Ownership], list[Migration]]:
    require_bare_semantic_identity_syntax()
    ownership: list[Ownership] = []
    migrations: list[Migration] = []
    seen_keys: set[str] = set()
    seen_semantic: dict[str, str] = {}

    for tokens in forms(MAP_PATH):
        tag = tokens[0]
        if tag in {"schema", "as-of", "scope"}:
            continue

        if tag == "ownership":
            if len(tokens) != 12:
                key = tokens[1] if len(tokens) > 1 else "?"
                raise ValueError(f"ownership row {key}: очікувалося 12 полів, отримано {len(tokens)}")
            row = Ownership(*tokens[1:])
            if row.key in seen_keys:
                raise ValueError(f"дубльований ownership key: {row.key}")
            seen_keys.add(row.key)
            if row.owner_class not in CLASSES:
                raise ValueError(f"{row.key}: невідомий ownership class {row.owner_class}")
            if row.layer not in LAYERS:
                raise ValueError(f"{row.key}: невідомий layer {row.layer}")
            if row.status not in STATUSES:
                raise ValueError(f"{row.key}: невідомий status {row.status}")
            if row.policy_candidate not in {"yes", "no"}:
                raise ValueError(f"{row.key}: policy candidate мусить бути yes/no")
            if row.semantic_id != "-":
                if not SID8.fullmatch(row.semantic_id):
                    raise ValueError(
                        f"{row.key}: semantic identity must be exactly 8 binary digits or -"
                    )
                previous = seen_semantic.get(row.semantic_id)
                if previous is not None:
                    raise ValueError(
                        f"semantic identity {row.semantic_id} одночасно заявлена {previous} і {row.key}; "
                        "layered ownership треба описати явно"
                    )
                seen_semantic[row.semantic_id] = row.key
            require_paths(split_paths(row.implementation_paths), row.key)
            require_paths(split_paths(row.evidence_paths), row.key)
            if row.status == "confirmed" and not split_paths(row.evidence_paths):
                raise ValueError(f"{row.key}: confirmed row потребує executable evidence")
            if (row.previous_owner == "-") != (row.migration_ref == "-"):
                raise ValueError(
                    f"{row.key}: previous_owner і migration_ref мають бути присутні разом"
                )
            if row.migration_ref != "-" and not HEX40.fullmatch(row.migration_ref):
                raise ValueError(f"{row.key}: migration_ref мусить бути повним commit SHA")
            ownership.append(row)
            continue

        if tag == "migration":
            if len(tokens) != 8:
                key = tokens[1] if len(tokens) > 1 else "?"
                raise ValueError(f"migration row {key}: очікувалося 8 полів, отримано {len(tokens)}")
            row = Migration(*tokens[1:])
            if row.key in seen_keys:
                raise ValueError(f"дубльований key між ownership/migration rows: {row.key}")
            seen_keys.add(row.key)
            if row.status not in STATUSES:
                raise ValueError(f"{row.key}: невідомий status {row.status}")
            if row.status == "confirmed" and not HEX40.fullmatch(row.commit):
                raise ValueError(f"{row.key}: confirmed migration потребує повного commit SHA")
            require_paths(split_paths(row.evidence_paths), row.key)
            if row.status == "confirmed" and not split_paths(row.evidence_paths):
                raise ValueError(f"{row.key}: confirmed migration потребує current evidence")
            migrations.append(row)
            continue

        raise ValueError(f"невідома top-level форма: {tag}")

    if not ownership:
        raise ValueError("ownership inventory порожній")
    require_cross_evidence_gates(ownership)
    return ownership, migrations


def count_rows(rows: list[Ownership], attr: str) -> list[tuple[str, int]]:
    return sorted(collections.Counter(getattr(row, attr) for row in rows).items())


def table(rows: list[tuple[str, int]]) -> str:
    out = ["| категорія | аудитовані рядки |", "|---|---:|"]
    out.extend(f"| `{name}` | {count} |" for name, count in rows)
    return "\n".join(out)


def render(ownership: list[Ownership], migrations: list[Migration]) -> str:
    confirmed_migrations = [row for row in migrations if row.status == "confirmed"]
    host_to_lisp = [
        row
        for row in confirmed_migrations
        if row.to_owner == "lisp-owned" and row.from_owner != "lisp-owned"
    ]
    host_policy_candidates = [
        row
        for row in ownership
        if row.owner_class == "host-mechanism" and row.policy_candidate == "yes"
    ]
    legitimate_host = [
        row
        for row in ownership
        if row.status == "confirmed"
        and row.policy_candidate == "no"
        and row.owner_class in {"host-observation", "host-authorization", "host-mechanism"}
    ]
    unknown_rows = [row for row in ownership if row.status == "unknown"]

    lines = [
        "# Звіт про семантичну власність",
        "",
        "> Згенеровано детерміновано з `knowledge/semantic-ownership.lisp`.",
        "> Звіт рахує **аудитовані поведінки/відповідальності**, а не LOC і не повноту всієї мови.",
        "> Жодне число нижче не є «відсотком self-hosting».",
        "",
        "## Підсумок",
        "",
        f"- Аудитованих ownership rows: **{len(ownership)}**",
        f"- Підтверджених ownership rows: **{sum(row.status == 'confirmed' for row in ownership)}**",
        f"- Часткових ownership rows: **{sum(row.status == 'partial' for row in ownership)}**",
        f"- Підтверджених host/Rust→Lisp semantic migrations: **{len(host_to_lisp)}**",
        f"- Підтверджених записів migration ledger загалом: **{len(confirmed_migrations)}**",
        f"- Залишкових host semantic-policy candidates: **{len(host_policy_candidates)}**",
        f"- Підтверджених host mechanism/observation/authorization rows, не позначених policy candidate: **{len(legitimate_host)}**",
        f"- Ownership rows зі статусом unknown: **{len(unknown_rows)}**",
        "",
        "## Класи власності",
        "",
        table(count_rows(ownership, "owner_class")),
        "",
        "## Шари",
        "",
        table(count_rows(ownership, "layer")),
        "",
        "## Епістемічний статус",
        "",
        table(count_rows(ownership, "status")),
        "",
        "## Кандидати на перевірку host-policy ownership",
        "",
    ]

    if host_policy_candidates:
        lines.extend(
            f"- `{row.key}` — {row.behavior} (`{row.status}`)"
            for row in sorted(host_policy_candidates, key=lambda item: item.key)
        )
    else:
        lines.append("- немає")

    lines.extend(["", "## Підтверджений журнал міграцій", ""])
    if confirmed_migrations:
        lines.extend(
            f"- `{row.key}` — `{row.from_owner}` → `{row.to_owner}` у `{row.commit}`: {row.behavior}"
            for row in sorted(confirmed_migrations, key=lambda item: item.key)
        )
    else:
        lines.append("- немає")

    lines.extend(
        [
            "",
            "## Аудитовані поведінки",
            "",
            "| key | semantic id | owner | layer | status | поведінка |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in sorted(ownership, key=lambda item: item.key):
        semantic = row.semantic_id if row.semantic_id != "-" else "—"
        lines.append(
            f"| `{row.key}` | `{semantic}` | `{row.owner_class}` | `{row.layer}` | "
            f"`{row.status}` | {row.behavior} |"
        )

    lines.extend(
        [
            "",
            "## Правило інтерпретації",
            "",
            "Знаменник кожного числа — лише checked-in аудитований інвентар вище. "
            "Більша кількість `lisp-owned` сама по собі не є прогресом, а host-owned "
            "observation чи authorization boundary сама по собі не є боргом. Зміна ownership "
            "є прогресом лише тоді, коли вона прибирає дубльовану семантичну владу або "
            "переносить policy до шару, який може нею володіти без послаблення evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="перевірити map і checked-in report")
    group.add_argument("--write", action="store_true", help="перевірити map і переписати report")
    return parser.parse_args()


def main() -> int:
    args = arguments()
    try:
        ownership, migrations = load()
        report = render(ownership, migrations)
        if args.write:
            REPORT_PATH.write_text(report, encoding="utf-8")
        else:
            existing = REPORT_PATH.read_text(encoding="utf-8")
            if existing != report:
                raise ValueError(
                    "semantic ownership report drift: запустіть "
                    "`python3 scripts/semantic-ownership.py --write`"
                )
    except (OSError, ValueError) as error:
        print(f"semantic ownership check failed: {error}", file=sys.stderr)
        return 1

    print(
        f"semantic ownership: {len(ownership)} rows, "
        f"{len(migrations)} migrations, report synchronized"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
