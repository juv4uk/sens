#!/usr/bin/env python3
"""MYLISP-MULTILINGUAL-PARITY-GATE.

A lightweight, read-only parity check for the repo's trilingual (EN/UK/DE)
documentation. It detects missing or stale language counterparts and stale
generated tables WITHOUT assuming any language is unused and WITHOUT
deleting or editing any file. A language-scope reduction stays an owner
decision that needs usage evidence; this tool never performs one.

Two parts:

Part A — authoritative-section parity. Over a list of AUTHORITATIVE_DOCS
(every doc the project treats as an EN/UK/DE mirror):
  A1 presence: each doc must define all three language sections
      `## English`, `## Українська`, `## Deutsch`. A missing one is drift.
  A2 structure: for docs that use `###` subsections, the three language
      blocks must have equal subsection counts. A mismatch (mirror drifted,
      a section added in only one language) is drift.

Part B — generated-table staleness. Over a list of GENERATED_TABLES (docs
auto-produced from live source):
  For docs/FUNCTIONS.md it compares the builtin count recorded in the header
  against the live `(env)` builtin count from scripts/gen-functions.lisp. A
  mismatch means the generated table is stale relative to live source.

This only READS files and runs the (cheap) live builtin inventory. A finding
is a report to fix by hand (e.g. rerun scripts/gen-functions.lisp to refresh
FUNCTIONS.md) or in the offending doc's own next edit — never auto-corrected
here.

EN / UK / DE documentation lives in lib/*.lisp and the repo README; keeping the
three in step is what this gate protects.

--------------------

MYLISP-MULTILINGUAL-PARITY-GATE — легка, лише-для-читання перевірка
тримовної (EN/UK/DE) документації репозиторію. Вона виявляє відсутні або
застарілі мовні відповідники та застарілі згенеровані таблиці, НЕ
припускаючи, що якась мова не використовується, і НЕ видаляючи/редагуючи
жоден файл. Скорочення мовної області залишається рішенням власника, що
потребує доказів використання; цей інструмент ніколи його не виконує.

Дві частини:

Частина A — паритет авторитетних секцій. За списком AUTHORITATIVE_DOCS
(кожен документ, який проєкт вважає дзеркалом EN/UK/DE):
  A1 наявність: кожен документ має визначати всі три мовні секції
      `## English`, `## Українська`, `## Deutsch`. Відсутня — це дрейф.
  A2 структура: для документів із підсекціями `###` три мовні блоки мають
      мати рівну кількість підсекцій. Розбіжність (дзеркало відстало,
      секцію додано лише в одній мові) — це дрейф.

Частина B — застарілість згенерованих таблиць. За списком GENERATED_TABLES
(документи, автостворені з живої сирці):
  Для docs/FUNCTIONS.md звіряється кількість builtin, зафіксована в шапці,
  із живою кількістю `(env)` builtin зі scripts/gen-functions.lisp.
  Розбіжність означає, що згенерована таблиця застаріла відносно живої сирці.

Це лише ЧИТАЄ файли й виконує (дешеву) живу інвентаризацію builtin. Знахідка —
це звіт для ручного виправлення (напр. повторний запуск
scripts/gen-functions.lisp для оновлення FUNCTIONS.md) або в наступному
редагуванні проблемного документа — ніколи не автоматичне виправлення тут.

EN/UK/DE документація живе в lib/*.lisp і README репозиторію; узгодженість
трьох мов — саме те, що захищає цей gate.

--------------------

MYLISP-MULTILINGUAL-PARITY-GATE — eine leichte, rein lesende Prüfung der
dreisprachigen (EN/UK/DE) Dokumentation des Repos. Sie erkennt fehlende oder
veraltete Sprach-Gegenstücke und veraltete generierte Tabellen, OHNE
anzunehmen, dass eine Sprache ungenutzt ist, und OHNE Dateien zu löschen oder
zu bearbeiten. Eine Reduktion des Sprachumfangs bleibt eine Entscheidung des
Eigentümers, die Nutzungsnachweise braucht; dieses Werkzeug führt nie eine
durch.

Zwei Teile:

Teil A — Parität der maßgeblichen Abschnitte. Über die Liste AUTHORITATIVE_DOCS
(jedes Dokument, das das Projekt als EN/UK/DE-Spiegel behandelt):
  A1 Vorhandensein: jedes Dokument muss alle drei Sprachabschnitte
      `## English`, `## Українська`, `## Deutsch` definieren. Fehlt einer,
      ist das Drift.
  A2 Struktur: für Dokumente mit `###`-Unterabschnitten müssen die drei
      Sprachblöcke gleiche Unterabschnitt-Anzahlen haben. Eine Abweichung
      (Spiegel veraltet, Abschnitt nur in einer Sprache ergänzt) ist Drift.

Teil B — Veraltung generierter Tabellen. Über die Liste GENERATED_TABLES
(Dokumente, die automatisch aus der Live-Quelle erzeugt werden):
  Für docs/FUNCTIONS.md wird die im Kopf verzeichnete Builtin-Anzahl mit der
  Live-`(env)`-Builtin-Anzahl aus scripts/gen-functions.lisp verglichen. Eine
  Abweichung bedeutet, dass die generierte Tabelle gegenüber der Live-Quelle
  veraltet ist.

Das liest nur DATEIEN und führt die (billige) Live-Builtin-Inventur aus. Ein
Befund ist ein Bericht zur manuellen Korrektur (z. B. scripts/gen-functions.lisp
erneut ausführen, um FUNCTIONS.md zu aktualisieren) oder in der nächsten
Bearbeitung des betroffenen Dokuments — nie eine automatische Korrektur hier.

Die EN/UK/DE-Dokumentation lebt in lib/*.lisp und im Repo-README; die drei
Sprachen in Schritt zu halten, schützt genau dieser Gate.

Usage:
    python3 scripts/check-multilingual-parity.py [--root /home/agents/GitHub/sens]
    python3 scripts/check-multilingual-parity.py --generated-tables docs/FUNCTIONS.md

Exit code: 0 if no drift, 1 if any gate-level finding (missing section,
structural mismatch, or stale generated table).

Trust: this tool only reports; it never edits. Verify consequential claims
against live files before acting on a finding.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# The docs the project treats as authoritative EN/UK/DE mirrors. Only add a
# doc here once it is genuinely maintained in all three languages — a wrong
# guess or a bilingual-only doc (e.g. benchmarks.md) is deliberately excluded
# so the gate does not invent a requirement the owner never accepted.
AUTHORITATIVE_DOCS = [
    "README.md",
    "docs/capabilities.md",
    "docs/testing.md",
    "docs/advice-ingestion.md",
]

# Generated tables: docs auto-produced from live source. Each entry is a path
# plus how to read its recorded live-count claim from the header.
GENERATED_TABLES = [
    {
        "path": "docs/FUNCTIONS.md",
        # e.g. '**Всього:** 23 builtin'ів + 421 бібліотечних функцій'
        "count_re": r"(\d+)\s+builtin",
    },
]

LANG_MARKERS = ["English", "Українська", "Deutsch"]

# Regexes for privilege escalation of the claim "N builtin'ів".
def find_recorded_count(text: str, pattern: str) -> int | None:
    m = re.search(pattern, text)
    if not m:
        return None
    return int(m.group(1))


def live_builtin_count(binary: Path, gen_script: Path) -> int | None:
    """Run the live builtin inventory and count the primitive lines.

    Returns None if the subprocess fails (so the check reports "cannot
    verify" rather than guessing).
    """
    try:
        out = subprocess.run(
            [str(binary), str(gen_script)],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    lines = [ln for ln in out.stdout.splitlines() if ln.strip()]
    # The last line is the script's own return value (a list of names); the
    # live builtin count is the number of individual name-lines above it.
    return max(len(lines) - 1, 0)


def language_blocks(lines: list[str]):
    """Yield (marker, block_lines) for each detected ## language section."""
    h2 = [(i, ln) for i, ln in enumerate(lines) if ln.startswith("## ")]
    for n, (idx, header) in enumerate(h2):
        tag = header[3:].strip()
        marker = next((lm for lm in LANG_MARKERS if lm in tag), None)
        if marker is None:
            continue
        end = h2[n + 1][0] if n + 1 < len(h2) else len(lines)
        yield marker, lines[idx + 1 : end]


def check_section_parity(path: Path, findings: list[str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    present = {m: False for m in LANG_MARKERS}
    counts: dict[str, int] = {}
    for marker, block in language_blocks(lines):
        present[marker] = True
        counts[marker] = sum(1 for ln in block if ln.startswith("### "))
    for marker in LANG_MARKERS:
        if not present[marker]:
            findings.append(
                f"[A1 MISSING-SECTION] {path}: no '## {marker}' section"
            )
    # Only run the structural check when at least two languages have sections
    # (a bilingual-only doc is reported, not gated as structural drift).
    have = [m for m in LANG_MARKERS if present[m]]
    if len(have) == len(LANG_MARKERS) and any(counts[m] > 0 for m in have):
        base = counts[have[0]]
        for marker in have:
            if counts[marker] != base:
                findings.append(
                    f"[A2 SECTION-MISMATCH] {path}: {marker} has "
                    f"{counts[marker]} subsections, expected {base} "
                    f"(mirror of {have[0]})"
                )


def check_generated_tables(root: Path, table_cfgs: list[dict], findings: list[str]) -> None:
    binary = root / "target" / "debug" / "my-lisp"
    gen_script = root / "scripts" / "gen-functions.lisp"
    live = live_builtin_count(binary, gen_script)
    for cfg in table_cfgs:
        path = root / cfg["path"]
        if not path.exists():
            findings.append(f"[B STALE-TABLE] {cfg['path']}: file missing")
            continue
        text = path.read_text(encoding="utf-8")
        recorded = find_recorded_count(text, cfg["count_re"])
        if recorded is None:
            findings.append(
                f"[B UNVERIFIABLE] {cfg['path']}: no recorded builtin count "
                f"found in header"
            )
            continue
        if live is None:
            findings.append(
                f"[B UNVERIFIABLE] {cfg['path']}: could not read live builtin "
                f"count from scripts/gen-functions.lisp"
            )
            continue
        if recorded != live:
            findings.append(
                f"[B STALE-TABLE] {cfg['path']}: header records {recorded} "
                f"builtins, live (env) has {live} — rerun "
                f"scripts/gen-functions.lisp to refresh"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=str, default=str(Path(__file__).resolve().parent.parent))
    args = parser.parse_args()
    root = Path(args.root).resolve()

    findings: list[str] = []
    for rel in AUTHORITATIVE_DOCS:
        path = root / rel
        if not path.exists():
            findings.append(f"[A MISSING-DOC] {rel}: file not found")
            continue
        check_section_parity(path, findings)

    check_generated_tables(root, GENERATED_TABLES, findings)

    if not findings:
        print(
            "multilingual-parity: OK — no missing/stale EN/UK/DE "
            "sections, no stale generated tables."
        )
        return 0

    print("multilingual-parity: findings")
    for f in findings:
        print("  " + f)
    print("(Read-only report; fix by editing the doc or rerunning the generator.)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
