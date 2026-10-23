#!/usr/bin/env python3
"""Перенести доведені SID8/Sens8 викличні голови у повну проєкцію «укр».

    python3 scripts/migrate-legacy-w8-ukr.py lib/core1.lisp --source-ref <старий-40-символьний-SHA>
    python3 scripts/migrate-legacy-w8-ukr.py lib/core1.lisp --source-ref <SHA> --write

За замовчуванням dry-run. Немає виведення D8 з байта, запису .sens
або виконання Lisp через Python. Недоведені голови залишаються без змін.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from domain_tables import read_domain_table
from report_ukr_projection_progress import UKRAINIAN_KEYBOARD_OUTPUTS, _contains_source_definitions

# Тільки ІСТОРИЧНЕ свідчення: цей Git commit передує фізичному вилученню
# сід8-реєстру з main. Данні використовує ВИКЛЮЧНО одноразовий мігратор.
# Жодних поточних runtime alias/dispatch чи відновлення lib/surface/bridge.
HISTORICAL_BRIDGE_COMMIT = "364c20e89429962928ea39027651f2bb47875aa0"
HISTORICAL_BRIDGE_BLOB = "2c776a6947dacc88b312eacff89f4f7d66ed7813"
HISTORICAL_BRIDGE_PATH = "lib/surface/sid8-to-domain-bridge.lisp"

BRIDGE_ROW = re.compile(
    r"^\s*\(sid8:([01]{8})\s+->\s+(D(?:[1-9]|10|11)):([01]+)\)\s*(?:;.*)?$",
    re.MULTILINE,
)


def shared(name):
    key = "_sens_w8_migration_" + name.replace(".", "_").replace("-", "_")
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, ROOT / "scripts" / name)
        if spec is None or spec.loader is None:
            raise ValueError(f"відсутній штатний міграційний сканер: {name}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return sys.modules[key]


def mapping():
    scanner = shared("migrate-exact-domain.py")
    engine = shared("migrate-three-pass.py")
    owner = json.loads((ROOT / "knowledge/d1-d11-foundation.json").read_text(encoding="utf-8"))
    if owner.get("status") != "owner-ratified":
        raise ValueError("драбину доменів ще не ратифіковано")
    surfaces = {
        (row.domain, row.bits): row
        for w in (3, 4, 5, 6, 8, 9, 10)
        for row in read_domain_table(ROOT / "lib/domains" / f"d{w}.lisp")
    }
    d8 = set(engine.CORE_OPERATION_D8)
    d8.update(bits for bits, w, _ in engine.core4_d1_d8_defined_rows() if w == 8)
    d9 = set(engine.CORE_OPERATION_D9) | set(engine.core4_d9_callable_rows())
    d10 = set(engine.core4_d10_defined_rows())
    result, withheld = {}, {}
    # Історичний ledger більше НЕ є активним lib-файлом. Читати точний
    # Git-об'єкт після перевірки SHA, не створюючи мостів сумісності.
    revision = f"{HISTORICAL_BRIDGE_COMMIT}:{HISTORICAL_BRIDGE_PATH}"
    blob = git("rev-parse", revision).strip()
    if blob != HISTORICAL_BRIDGE_BLOB:
        raise ValueError(f"історичний SID8-ledger змінив Git blob: {blob}")
    bridge = git("show", revision)
    for old, dom, bits in BRIDGE_ROW.findall(bridge):
        if old in result or old in withheld:
            raise ValueError(f"повтор старого W8: {old}")
        if dom == "D11":
            withheld[old] = "D11 тестовий — не executable"
            continue
        row = surfaces.get((dom, bits))
        owner_label = owner["domains"].get(dom, {}).get("residents", {}).get(bits)
        if len(bits) != int(dom[1:]) or row is None or owner_label is None:
            raise ValueError(f"bridge {old} -> {dom}:{bits} не збігається з ратифікацією")
        ukr = row.ukr
        if not ukr or ukr == "()" or any(c not in UKRAINIAN_KEYBOARD_OUTPUTS for c in ukr):
            withheld[old] = f"{dom}:{bits} — немає придатної повної колонки укр"
            continue
        admitted = (dom in {"D3", "D4", "D5", "D6"}
                    or (dom == "D8" and bits in d8)
                    or (dom == "D9" and bits in d9)
                    or (dom == "D10" and bits in d10))
        if not admitted:
            withheld[old] = f"{dom}:{bits} — немає підтвердженого callable-механізму"
            continue
        result[old] = scanner.Identity(dom, bits, str(owner_label), ukr)
    return scanner, result, withheld


def git(*args):
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    if r.returncode:
        raise ValueError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def prove(commit, historical_path, requested, scanner, table):
    if not re.fullmatch("[a-fA-F0-9]{40}", commit):
        raise ValueError("потрібен точний 40-символьний історичний commit SHA")
    date = git("show", "-s", "--format=%cI", commit).strip()
    if not date or date[:10] >= "2026-10-06":
        raise ValueError("джерело має передувати ратифікації D8 06.10.2026")
    if historical_path.is_absolute() or ".." in historical_path.parts:
        raise ValueError("некоректний історичний шлях")
    historic = git("show", f"{commit}:{historical_path.as_posix()}")
    unknown = []
    edits = scanner.plan(historic, {}, legacy_heads=table, unresolved=unknown)
    found = {e.source for e in edits} | {word for _, word in unknown}
    if requested - found:
        raise ValueError(f"{historical_path}@{commit[:12]} не містить цих старих call-head: {sorted(requested - found)}")
    return {"commit": commit, "date": date, "path": str(historical_path)}


def files(paths):
    selected = set()
    for path in paths:
        if path.is_symlink():
            raise ValueError(f"заборонений symlink: {path}")
        for p in path.rglob("*.lisp") if path.is_dir() else [path]:
            if not p.is_file() or p.is_symlink() or p.suffix != ".lisp":
                continue
            resolved = p.resolve()
            if not resolved.is_relative_to(ROOT):
                raise ValueError(f"шлях поза SENS: {p}")
            rel = resolved.relative_to(ROOT)
            if rel.parts[0] != "lib" or (len(rel.parts) > 1 and rel.parts[1] in
                    {"domains", "generated", "staged-out"}):
                continue  # таблиці доменів та згенеровані дані — не програми
            # У surface є і проєкційні таблиці, і справжні DEFINE-програми.
            # Колишнє виключення всього каталогу приховувало їхні W8-голови.
            # Та сама AST-класифікація вже діє в аудиті української проєкції.
            if (len(rel.parts) > 1 and rel.parts[1] == "surface"
                    and not _contains_source_definitions(resolved)):
                continue
            selected.add(resolved)
    return sorted(selected)


def replace_atomic(path, original, updated):
    if path.read_bytes() != original:
        raise ValueError(f"файл змінився під час планування: {path}")
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".w8-ukr-", delete=False) as f:
            temp = Path(f.name)
            f.write(updated)
        os.chmod(temp, path.stat().st_mode)
        os.replace(temp, path)
    finally:
        if temp:
            temp.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", type=Path, nargs="+")
    ap.add_argument("--source-ref", help="історичний commit до D8; потрібен лише для наявних W8-голів")
    ap.add_argument("--historical-path", type=Path, help="стара адреса одного перейменованого файла")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--report", type=Path, help="JSON діагностика")
    args = ap.parse_args()
    if args.historical_path and len(args.paths) != 1:
        ap.error("--historical-path — для одного файла")
    try:
        scanner, table, withheld = mapping()
        chosen = files(args.paths)
        if not chosen:
            raise ValueError("не знайдено активних lib/*.lisp")
        report = []
        for file in chosen:
            rel = file.relative_to(ROOT)
            try:
                original = file.read_bytes()
                text = original.decode("utf-8")
                # Це схематичний історичний об'єкт, НЕ Lisp-програма:
                # (machine-profile-1 (rows (00000010 sequence "...") ...)).
                # Числові ключі в rows не є викличними головами.
                # Стару таблицю залишаємо provenance, не підміняємо D8.
                if re.search(r"(?m)^\(machine-profile-1(?:\s|$)", text):
                    report.append({
                        "file": str(rel),
                        "status": "skipped-nonexecutable",
                        "reason": "історична machine-profile-1 таблиця, SID8 — ключі даних",
                        "sha256_before": hashlib.sha256(original).hexdigest(),
                        "replacements": [], "unresolved": [], "written": False,
                    })
                    print(f"{rel}: SKIP дані machine-profile-1, не викличний Lisp")
                    continue
                unknown = []
                edits = scanner.plan(text, {}, legacy_heads=table, unresolved=unknown)
                old_codes = {e.source for e in edits} | {code for _, code in unknown}
                if old_codes and not args.source_ref:
                    raise ValueError(
                        "для реальної заміни W8-голів потрібен --source-ref "
                        "із перевіреним історичним SHA; без нього нічого не переписуємо"
                    )
                proof = (prove(args.source_ref, args.historical_path or rel, old_codes, scanner, table)
                         if old_codes else None)
                new = scanner.apply_edits(text, edits).encode("utf-8")
                if args.write and new != original:
                    replace_atomic(file, original, new)
                pending = [{"offset": at, "old": word,
                            "reason": withheld.get(word, "немає доведеного моста")}
                           for at, word in unknown]
                item = {
                    "file": str(rel), "status": "partial" if pending else "ok",
                    "sha256_before": hashlib.sha256(original).hexdigest(),
                    "sha256_after": hashlib.sha256(new).hexdigest(),
                    "historical_source": proof,
                    "replacements": [{"offset": e.start, "old": e.source,
                                      "domain": e.identity.domain, "bits": e.identity.bits,
                                      "ukr": e.identity.українська} for e in edits],
                    "unresolved": pending, "written": bool(args.write and edits),
                }
                report.append(item)
                if edits or pending:
                    print(f"{rel}: {'замінено' if args.write else 'заплановано'} {len(edits)}, невідомо {len(pending)}")
                    for x in pending:
                        print(f"  НЕ ВГАДУЮ {x['old']} @ {x['offset']}: {x['reason']}")
            except (OSError, UnicodeError, ValueError) as error:
                report.append({"file": str(rel), "status": "error", "reason": str(error)})
                print(f"{rel}: НЕ ЗМІНЮВАТИ — {error}", file=sys.stderr)
        if args.report:
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        # Історична невиконувана схема явно показана як SKIP, але не є
        # помилкою міграції виконуваного Lisp. Незавершені й несправні
        # активні файли й надалі повертають ненульовий код.
        return 2 if any(x["status"] in {"error", "partial"} for x in report) else 0
    except (OSError, ValueError) as error:
        print(f"ПОМИЛКА: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
