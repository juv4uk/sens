#!/usr/bin/env python3
"""М0 #5444 — відтворюваний read-only реєстр кодових шляхів T5.

Read-only. Не створює, не змінює й не мігрує жодного `.sens`/`.senc`/`.lisp`.
Не є новим кодеком і не оголошує нічого «мігрованим».

Реєстр будується **скануванням** `git ls-files` (а не ручним списком), щоб
нова ланка, що згадує `.sens`/`.senc`, не могла загубитися: `--check`
перегенеровує реєстр у пам'яті й падає, якщо живий набір ≠ закомічений
manifest. Це і є fail-closed негативний свідок рівня CI.

Ролі: producer | consumer | validator | projection | benchmark.
migration_status: T5_REQUIRED | SENC_RESEARCH | MIGRATION_CANDIDATE | BLOCKED.
Без доказу (роль/оракул не визначено) — BLOCKED, а не здогад.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

SCHEMA = "sens-t5-migration-inventory/v1"
# Незмінна база цього зрізу; перегляд/re-pin потребує окремого PR і рев'ю.
PINNED_BASE_SHA = "33bd5a32877f63de78eee28b0f97ea629e83a4fa"

EXT = {".rs", ".py", ".sh", ".yml", ".yaml", ".toml", ".lisp"}
EXCLUDE_PREFIXES = (
    "vendor/", "target/", "archive/", "docs/",
    "knowledge/", "memory/", "дослідження/", "public/",
)

# Терміни, за якими ланка вважається такою, що торкається фізичного SENS.
DISCOVERY = re.compile(
    r"\.sens\b|\.senc\b|sens-trit|sens_t5_codec|PhysicalT5|"
    r"\btriplet\b|triple-projection|source_packing|canonical_reader|"
    r"binary_execution|\bT5\b|sens_triplet|physical_t5|physical-t5",
    re.IGNORECASE,
)

# Канонічний T5-оракул / межі authority (те, що НЕ переробляється на .senc).
T5_AUTHORITY = {
    # Physical-byte codec owns T5 framing and byte validity.
    "crates/sens/src/ternary_transport.rs": "crates/sens/src/ternary_transport.rs",
    # This parser owns D2 grammar, not physical byte transport.
    "crates/sens/src/canonical_reader.rs":
        "crates/sens/src/canonical_reader.rs (D2 grammar; not physical codec)",
    # Execution consumes the physical transport; it does not define framing.
    "crates/sens/src/binary_execution.rs": "crates/sens/src/ternary_transport.rs",
    "crates/sens-cli/src/bin/sens-trit.rs": "crates/sens/src/ternary_transport.rs",
    "scripts/sens_t5_codec.py": "scripts/sens_t5_codec.py",
    "scripts/audit_t5_file_pairs.py": "scripts/sens_t5_codec.py",
    "scripts/report_t5_triplet_inventory.py": "scripts/audit_t5_file_pairs.py",
    "scripts/check-triple-projection.sh": "scripts/sens_t5_codec.py",
}

# Related to exact source words, but deliberately NOT physical T5 authority:
# no separators, transport framing, or T5 byte validation is defined here.
NON_T5_COMPONENTS = {
    "crates/sens/src/source_packing.rs":
        "NONE (dense source-payload packer; no T5 framing)",
}

ROLE_OVERRIDES = {
    "crates/sens/src/ternary_transport.rs":
        ("producer", "physical T5 encode/decode and byte-validity authority"),
    "crates/sens/src/canonical_reader.rs":
        ("validator", "canonical D2 grammar over already bounded source words"),
    "crates/sens/src/binary_execution.rs":
        ("consumer", "physical T5 consumer/execution adapter"),
    "crates/sens/src/source_packing.rs":
        ("consumer", "dense exact-width source-payload packing; no T5 framing"),
    "crates/sens-cli/src/bin/sens-trit.rs":
        ("producer", "CLI delegates byte encoding/decoding to physical T5 codec"),
    ".github/workflows/admit-t5-migration.yml":
        ("validator", "CI workflow orchestration; not a physical-byte producer"),
    ".github/workflows/guarded-t5-mirror-transaction.yml":
        ("validator", "CI workflow orchestration; not a physical-byte producer"),
    ".github/workflows/migrate-entrypoint.yml":
        ("validator", "CI workflow orchestration; not a physical-byte producer"),
    ".github/workflows/migrate-one-to-sens.yml":
        ("validator", "CI workflow orchestration; not a physical-byte producer"),
    ".github/workflows/migrate-selected-lisp.yml":
        ("validator", "CI workflow orchestration; not a physical-byte producer"),
    ".github/workflows/migrate-sens-cli.yml":
        ("validator", "CI workflow orchestration; not a physical-byte producer"),
    ".github/workflows/migrate-t5-batch.yml":
        ("validator", "CI workflow orchestration; not a physical-byte producer"),
    ".github/workflows/publish-binary-master.yml":
        ("validator", "CI workflow orchestration; not a physical-byte producer"),
}

T5_AUTHORITY_REASONS = {
    "crates/sens/src/ternary_transport.rs":
        "канонічний фізичний T5: кодування/декодування байтів і межа фізичної валідності",
    "crates/sens/src/canonical_reader.rs":
        "граматика D2 для точних слів; не власник фізичного байтового кодування",
    "crates/sens/src/binary_execution.rs":
        "споживач фізичного T5: decode → D2 → execute",
    "crates/sens-cli/src/bin/sens-trit.rs":
        "CLI producer/consumer делегує фізичні байти T5 спільному codec",
}

ROLE_RULES = [
    (re.compile(r"^benchmarks/"), "benchmark", "шлях під benchmarks/"),
    (re.compile(r"^packaging/"), "consumer", "інсталятор/пакувальник островів"),
    (re.compile(r"projection|project|text7|_view|view\.|bits|python3 -m|d7_|d10|render|sens_uk"), "projection",
     "назва вказує на проєкцію/читабельний view"),
    (re.compile(r"migrate|encode|publish|mirror|admit|guarded_sens|"
                r"canonical_reader|source_packing|binary_execution|ternary_transport|"
                r"sens-trit|sens_t5_codec"), "producer",
     "назва вказує на видавця/читача фізичних байтів T5"),
    (re.compile(r"bench|performance|latency|throughput"), "benchmark",
     "назва вказує на вимірювання"),
    (re.compile(r"(^|/)tests?/|tests?\b|audit|guard|check|verify|report|"
                r"inventory|parity|roundtrip|delta|census|migration|classify|"
                r"scope|triage|plan|prove|diff|snapshot|ledger"), "validator",
     "назва вказує на аудит/ґейт/аналіз/свідка"),
    (re.compile(r"codec"), "producer", "файловий codec (кодує/декодує носій)"),
    (re.compile(r"reader|execution|trit|repl|\brun\b|eval|load|decode"),
     "consumer", "назва вказує на читача/виконавця"),
    (re.compile(r"^\.github/workflows/"), "validator",
     "CI-воркфлоу (ґейт/обв'язка)"),
    (re.compile(r"^crates/"), "consumer", "ядро crates/: читає/виконує SENS"),
]

RESEARCH = re.compile(
    r"\.senc|\bF3\b|\bF4\b|framed3|adaptive|tb33|tb-33|рамк|frame", re.IGNORECASE
)
EXTERNAL_REPOS = {"cml", "fpga-lisp", "sens-futhark", "wsm-graalvm"}


def git_root(root: Path) -> Path:
    p = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True, check=False)
    if p.returncode:
        raise SystemExit("BLOCKED: not a git worktree")
    return Path(p.stdout.strip())


def base_sha(root: Path, override: str | None) -> str:
    if override:
        return override
    p = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                       capture_output=True, text=True, check=False)
    if p.returncode:
        raise SystemExit("BLOCKED: cannot resolve HEAD")
    return p.stdout.strip()


def tracked(root: Path) -> list[str]:
    p = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                       capture_output=True, check=False)
    if p.returncode:
        raise SystemExit("BLOCKED: git ls-files failed")
    return [os.fsdecode(x) for x in p.stdout.split(b"\0") if x]


def is_candidate(path: str, root: Path) -> bool:
    if any(path.startswith(p) for p in EXCLUDE_PREFIXES):
        return False
    if Path(path).suffix.lower() not in EXT:
        return False
    if path in T5_AUTHORITY or path in NON_T5_COMPONENTS:
        return True
    try:
        text = (root / path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return bool(DISCOVERY.search(text))


def classify_role(path: str) -> tuple[str, str]:
    if path in ROLE_OVERRIDES:
        return ROLE_OVERRIDES[path]
    for pat, role, reason in ROLE_RULES:
        if pat.search(path):
            return role, reason
    return "unknown", "жодне правило ролі не збіглося"


def codec_of(path: str, root: Path) -> str:
    try:
        text = (root / path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "NONE"
    t5 = bool(re.search(
        r"\.sens|PhysicalT5|sens-trit|sens_t5|canonical_reader|source_packing|binary_execution|t5",
        text, re.IGNORECASE))
    senc = bool(re.search(r"\.senc|framed3|tb33|\bF3\b|\bF4\b", text))
    if senc and t5:
        return "T5+SENC"
    if senc:
        return "SENC_F3_F4"
    if t5:
        return "T5"
    return "NONE"


def owner_lane(path: str) -> str:
    if path.startswith("crates/"):
        return "#5439"
    if path.startswith("benchmarks/"):
        return "#5447"
    if path.startswith(".github/"):
        return "#5442"
    if path.startswith("research/"):
        return "#5439"
    if re.search(r"migrate|publish|mirror|encode", path):
        return "#5440"
    if path.startswith("scripts/"):
        return "#5440"
    return "UNKNOWN"


def classify(path: str, root: Path) -> dict:
    role, reason = classify_role(path)
    codec = codec_of(path, root)
    lane = owner_lane(path)
    is_senc = (path.startswith("research/")
               or bool(re.search(r"framed3|tb33|adaptive|senc", path, re.IGNORECASE)))

    if path in T5_AUTHORITY:
        status = "T5_REQUIRED"
        authority = T5_AUTHORITY[path]
        reason = T5_AUTHORITY_REASONS.get(
            path, "канонічна межа T5 (authority)")
    elif path in NON_T5_COMPONENTS:
        status = "BLOCKED"
        authority = NON_T5_COMPONENTS[path]
        reason = "пов'язане щільне пакування payload без T5 framing; не фізичний T5 codec"
    elif path.endswith(".lisp"):
        status = "BLOCKED"
        authority = "UNKNOWN"
        reason = "Lisp-ланка потребує незалежного доказу producer/consumer T5"
    elif role == "unknown" or lane == "UNKNOWN":
        # Не оголошуємо шлях дослідним/міграційним, доки немає ролі й owner lane.
        status = "BLOCKED"
        authority = "UNKNOWN"
        reason = "роль або owner_lane не визначено → BLOCKED"
    elif is_senc:
        status = "SENC_RESEARCH"
        authority = "research/framed3 (не canonic)"
        reason = "дослідний .senc/F3/F4-носій"
    elif role in ("producer", "consumer") and codec in ("T5", "T5+SENC"):
        status = "MIGRATION_CANDIDATE"
        authority = "T5 oracle (crates/sens)"
        reason = "видавець/читач фізичного T5 → у спільний API (М1/М2)"
    elif role in ("validator", "projection", "benchmark"):
        status = "T5_REQUIRED"
        authority = "T5 oracle (crates/sens)"
        reason = reason if path in ROLE_OVERRIDES else "перевіряє/проєктує канонічний T5"
    else:
        status = "BLOCKED"
        authority = "UNKNOWN"
        reason = "немає достатнього доказу → BLOCKED"

    canonical = "n/a" if path.endswith(".lisp") else ("*.sens" if "T5" in codec else ("*.senc" if "SENC" in codec else "n/a"))
    return {
        "schema": SCHEMA,
        "repository": "juv4uk/sens",
        "path": path,
        "role": role,
        "canonical_path": canonical,
        "extension": Path(path).suffix.lower(),
        "codec": codec,
        "authority": authority,
        "dependency": "#5444" if path.endswith(".lisp") and status == "BLOCKED" else status_dep(status),
        "base_sha": None,  # заповнюється у build()
        "owner_lane": lane,
        "migration_status": status,
        "reason": reason,
    }


def status_dep(status: str) -> str:
    return {
        "T5_REQUIRED": "#5439,#5442",
        "SENC_RESEARCH": "#5429,#5439",
        "MIGRATION_CANDIDATE": "#5440",
        "BLOCKED": "UNKNOWN",
    }[status]


def build(root: Path, sha: str) -> list[dict]:
    rows = []
    for path in tracked(root):
        if is_candidate(path, root):
            row = classify(path, root)
            row["base_sha"] = sha
            rows.append(row)
    rows.sort(key=lambda r: r["path"])
    return rows


def to_jsonl(rows: list[dict]) -> str:
    import json
    return "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n"
                   for r in rows)


def validate_manifest_provenance(
    manifest_text: str, root: Path, head_sha: str
) -> tuple[bool, str]:
    """Validate the manifest's shared base pin against real Git history."""
    import json

    try:
        rows = [json.loads(line) for line in manifest_text.splitlines() if line.strip()]
    except json.JSONDecodeError as exc:
        return False, f"invalid JSONL: {exc}"
    if not rows:
        return False, "empty manifest"
    pins = {row.get("base_sha") for row in rows}
    if len(pins) != 1:
        return False, f"expected one shared base_sha, found {len(pins)}"
    pin = next(iter(pins))
    if not isinstance(pin, str) or not re.fullmatch(r"[0-9a-f]{40}", pin):
        return False, "base_sha must be one full lowercase 40-hex Git commit"
    if pin != PINNED_BASE_SHA:
        return False, f"unexpected provenance pin: {pin}; expected {PINNED_BASE_SHA}"
    exists = subprocess.run(
        ["git", "-C", str(root), "cat-file", "-e", f"{pin}^{{commit}}"],
        capture_output=True, text=True, check=False,
    )
    if exists.returncode:
        return False, f"base_sha is not an available Git commit: {pin}"
    ancestor = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", pin, head_sha],
        capture_output=True, text=True, check=False,
    )
    if ancestor.returncode:
        return False, f"base_sha is not an ancestor of checked HEAD: {pin}"
    return True, pin


def summarize(rows: list[dict]) -> str:
    from collections import Counter
    roles = Counter(r["role"] for r in rows)
    status = Counter(r["migration_status"] for r in rows)
    codecs = Counter(r["codec"] for r in rows)
    blocked = [r["path"] for r in rows if r["migration_status"] == "BLOCKED"]
    lines = [
        f"{SCHEMA}: {len(rows)} rows",
        "  role:   " + ", ".join(f"{k}={v}" for k, v in sorted(roles.items())),
        "  status: " + ", ".join(f"{k}={v}" for k, v in sorted(status.items())),
        "  codec:  " + ", ".join(f"{k}={v}" for k, v in sorted(codecs.items())),
        f"  UNKNOWN/BLOCKED rows: {len(blocked)}",
    ]
    for b in blocked[:20]:
        lines.append("    BLOCKED " + b)
    if len(blocked) > 20:
        lines.append(f"    ... +{len(blocked) - 20} more")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--base-sha", default=None)
    ap.add_argument("--check", metavar="MANIFEST",
                    help="перегенерувати й порівняти з закоміченим manifest")
    ap.add_argument("--output", default=None)
    args = ap.parse_args(argv)

    root = git_root(Path(args.root))
    sha = base_sha(root, args.base_sha)
    rows = build(root, sha)
    text = to_jsonl(rows)

    if args.check:
        committed = Path(args.check).read_text(encoding="utf-8")
        # base_sha є provenance pin: не мусить дорівнювати живому HEAD,
        # але має бути єдиним, реальним commit та предком checked HEAD.
        provenance_ok, provenance = validate_manifest_provenance(
            committed, root, base_sha(root, None))
        if not provenance_ok:
            print(f"FAIL: manifest provenance: {provenance}", file=sys.stderr)
            return 1

        # Порівнюємо склад шляхів/класифікацію, а base_sha перевірено окремо.
        def strip_sha(s: str) -> str:
            import json
            out = []
            for line in s.splitlines():
                d = json.loads(line)
                d.pop("base_sha", None)
                out.append(json.dumps(d, ensure_ascii=False, sort_keys=True))
            return "\n".join(out)
        if strip_sha(text) != strip_sha(committed):
            print("FAIL: живий реєстр ≠ закомічений manifest "
                  "(нова/зникла ланка або зміна класифікації)", file=sys.stderr)
            live_by_path = {r["path"]: r for r in rows}
            import json
            committed_rows = [
                json.loads(line) for line in committed.splitlines() if line.strip()
            ]
            committed_by_path = {r["path"]: r for r in committed_rows}
            live_paths = set(live_by_path)
            committed_paths = set(committed_by_path)
            for p in sorted(live_paths - committed_paths):
                print("  + " + p, file=sys.stderr)
            for p in sorted(committed_paths - live_paths):
                print("  - " + p, file=sys.stderr)
            # Path sets can match while authority, role, codec, owner, or status
            # silently drifts. Show a bounded per-path field diff so CI points
            # to the exact repair instead of emitting a content-free FAIL.
            shown = 0
            fields = sorted(
                (set(live_by_path[next(iter(live_by_path))]) |
                 set(committed_by_path[next(iter(committed_by_path))]))
                - {"base_sha", "path"}
            ) if live_by_path and committed_by_path else []
            for p in sorted(live_paths & committed_paths):
                actual = live_by_path[p]
                expected = committed_by_path[p]
                for field in fields:
                    if actual.get(field) != expected.get(field):
                        print(
                            f"  ~ {p} [{field}]: manifest={expected.get(field)!r}; "
                            f"live={actual.get(field)!r}",
                            file=sys.stderr,
                        )
                        shown += 1
                        if shown >= 80:
                            print("  ... additional field differences omitted", file=sys.stderr)
                            break
                if shown >= 80:
                    break
            return 1
        print("OK: manifest == live registry "
              f"({len(rows)} rows, base_sha={sha})", file=sys.stderr)
        return 0

    print(summarize(rows), file=sys.stderr)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
