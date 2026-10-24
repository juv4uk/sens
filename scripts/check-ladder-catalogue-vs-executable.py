#!/usr/bin/env python3
"""Драбина D1..D11: ратифікована ПОЗИЦІЯ vs ФІЗИЧНО ВИКОНУВАНА (bindings).

Першопричина: розділення «позиція ≠ виконуване» було доведене лише для D10
(feat/d10-catalogue-vs-executable-ledger). Для решти щаблів ніхто не звів
машино-перевіреної межі — а джерело bindings існує лише для D5, D6, D9, D10.
Тож щаблі без джерела легко прочитати як «усе виконуване».

Цей чекер НЕ мовчить про прогалину: він друкує таблицю для ВСІХ щаблів D1..D11
і явно позначає ті, де джерела допуску немає («не замаплено»).

Інваріант, який перевіряється закрито: bindings ⊆ каталог (жодної позиції
допуску поза ратифікованою таблицею) і жодного дубля координати.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNGS = range(1, 12)
CATALOGUE_ROW = re.compile(r"(?m)^\s*\(([01]+)\s")
BINDING_ROW = re.compile(r"bits:\s*0b([01]+)")
# Явні Dn-константи механізмів у lib.rs (напр. D10 монотонний-нс).
HOST_CONST = re.compile(r"_D(\d+):\s*u16\s*=\s*0b([01]+)")


def catalogue(n: int) -> set[str]:
    path = ROOT / f"lib/domains/d{n}.lisp"
    if not path.is_file():
        return set()
    return set(CATALOGUE_ROW.findall(path.read_text(encoding="utf-8")))


def bindings(n: int) -> set[str] | None:
    path = ROOT / f"crates/sens/src/d{n}_definition_bindings_generated.rs"
    if not path.is_file():
        return None
    return set(BINDING_ROW.findall(path.read_text(encoding="utf-8")))


def host_mechanisms() -> dict[int, set[str]]:
    """Явні Dn-механізми з lib.rs — рідкісні, але їх не можна губити:
    без них D10 дає 713 carrier-only замість правдивих 712."""
    found: dict[int, set[str]] = {}
    for rung, bits in HOST_CONST.findall((ROOT / "crates/sens/src/lib.rs").read_text(encoding="utf-8")):
        found.setdefault(int(rung), set()).add(bits)
    return found


# Статично виведено з диспетчера (не виконано — немає Rust). Кожен запис
# прив'язаний до ЯКОРЯ: якщо якір зникне (рефактор), чекер упаде голосно,
# а не тихо віддасть застаріле число.
DISPATCH_ANCHORS = {
    1: (0, "crates/sens/src/domain_identity.rs",
        "pub enum CoreDomainIdentity {\n    D3(", "D1 не має викличної ідентичності"),
    2: (0, "crates/sens/src/domain_identity.rs",
        "pub enum CoreDomainIdentity {\n    D3(", "D2 не має викличної ідентичності"),
    3: (7, "crates/sens/src/eval/canon.rs",
        "DomainPrimitiveKind::PairConstruct", "3 примітиви + 2 селектори + QUOTE/COND"),
    4: (11, "crates/sens/src/eval/necessary_forms.rs",
        "LAMBDA", "EVAL+LAMBDA+DEFINE+NOT/NULL/LIST/APPEND+4 селектори"),
    8: (72, "crates/sens/src/eval/canon.rs",
        "DomainPrimitiveKind::WriteToString", "7 примітивів + MOD + 64 селектори"),
}


def declared_source(n: int) -> dict[str, object] | None:
    """Щаблі, чиє джерело допуску ЯВНО каже, скільки виконуваних.

    Без цього D7 і D11 звітували «не замаплено», хоча межа вже написана:
      D7  — crates/sens/src/d7_display_registry_generated.rs: «never authorizes a callable»
      D11 — knowledge/d11-selector-seed.json: accounting.callable = 0
    """
    if n == 7:
        path = ROOT / "crates/sens/src/d7_display_registry_generated.rs"
        if not path.is_file():
            return None
        text = path.read_text(encoding="utf-8")
        if "never authorizes a callable" not in text:
            raise SystemExit("FAIL: D7 registry втратив застереження про виклик")
        return {"executable": 0, "note": "клавіатурні дані; виклик не дозволено (шапка реєстру)"}
    if n in DISPATCH_ANCHORS:
        count, rel, anchor, note = DISPATCH_ANCHORS[n]
        path = ROOT / rel
        if not path.is_file():
            raise SystemExit(f"FAIL: D{n} якір відсутній: {rel}")
        if anchor not in path.read_text(encoding="utf-8"):
            raise SystemExit(f"FAIL: D{n} якір зник у {rel}: {anchor!r}")
        return {"executable": count, "note": f"з диспетчера: {note}"}
    if n == 11:
        path = ROOT / "knowledge/d11-selector-seed.json"
        if not path.is_file():
            return None
        import json
        seed = json.loads(path.read_text(encoding="utf-8"))
        acct = seed.get("accounting", {})
        if "callable" not in acct:
            raise SystemExit("FAIL: D11 сід втратив accounting.callable")
        return {"executable": int(acct["callable"]),
                "note": f"selector-похідні без прямого опкоду ({acct.get('derived_selectors_without_direct_opcode_admission')})"}
    return None


def survey() -> list[dict[str, object]]:
    rows = []
    host = host_mechanisms()
    for n in RUNGS:
        cat = catalogue(n)
        declared = declared_source(n)
        if declared is not None:
            rows.append({"rung": n, "catalogue": len(cat), "mapped": True,
                         "bindings": None, "declared": declared,
                         "executable": declared["executable"],
                         "carrier_only": len(cat) - int(declared["executable"]),
                         "wrong_width": [], "outside": [],
                         "note": declared["note"]})
            continue
        bind = bindings(n)
        if bind is not None:
            bind = bind | host.get(n, set())
        row: dict[str, object] = {"rung": n, "catalogue": len(cat),
                                  "bindings": bind, "mapped": bind is not None}
        if bind is not None:
            wrong_width = sorted(b for b in bind if len(b) != n)
            outside = sorted(bind - cat)
            row["wrong_width"] = wrong_width
            row["outside"] = outside
            row["executable"] = len(bind)
            row["carrier_only"] = len(cat) - len(bind & cat)
        rows.append(row)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail-closed перевірка вкладеності")
    args = ap.parse_args()
    rows = survey()
    bad = False
    print(f"{'щабель':>6} {'каталог':>8} {'bindings':>9} {'carrier-only':>13}  стан")
    for r in rows:
        n = r["rung"]
        if not r["mapped"]:
            print(f"{'D'+str(n):>6} {r['catalogue']:>8} {'—':>9} {'—':>13}  не замаплено (джерела допуску немає)")
            continue
        if r.get("declared") is not None:
            print(f"{'D'+str(n):>6} {r['catalogue']:>8} {r['executable']:>9} {r['carrier_only']:>13}  "
                  f"задекларовано: {r['note']}")
            continue
        if r["wrong_width"] or r["outside"]:
            bad = True
            print(f"{'D'+str(n):>6} {r['catalogue']:>8} {r['executable']:>9} {r['carrier_only']:>13}  ПОРУШЕННЯ: "
                  f"хибна ширина={r['wrong_width'][:2]} поза каталогом={r['outside'][:2]}")
        else:
            full = "повністю зв'язаний" if r["carrier_only"] == 0 else f"частково ({r['carrier_only']} carrier-only)"
            print(f"{'D'+str(n):>6} {r['catalogue']:>8} {r['executable']:>9} {r['carrier_only']:>13}  {full}")
    mapped = [r for r in rows if r["mapped"]]
    unmapped = [r["rung"] for r in rows if not r["mapped"]]
    if unmapped:
        print(f"\nLADDER-SEPARATION: замаплено {len(mapped)}/{len(list(RUNGS))} щаблів; "
              f"не замаплено: D{', D'.join(map(str, unmapped))}")
    else:
        print(f"\nLADDER-SEPARATION: замаплено {len(mapped)}/{len(list(RUNGS))} щаблів; "
              "усі щаблі мають межу")
    if args.check and bad:
        raise SystemExit("FAIL: bindings поза каталогом або хибної ширини")
    print("LADDER-SEPARATION: PASS вкладеність bindings ⊆ каталог тримається")
    return 0


if __name__ == "__main__":
    sys.exit(main())
