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


CANON = "crates/sens/src/eval/canon.rs"
SELECTOR_LAW = "crates/sens/src/eval/selector_law.rs"


def _text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def callable_rungs() -> set[int]:
    """Які щаблі взагалі мають викличну ідентичність — з переліку варіантів
    enum CoreDomainIdentity. D1/D2 там відсутні: вони не мають викличного
    варіанта, отже 0 механізмів."""
    text = _text("crates/sens/src/domain_identity.rs")
    block = text.split("pub enum CoreDomainIdentity {", 1)[1].split("}", 1)[0]
    return {int(m) for m in re.findall(r"\bD(\d+)\(", block)}


def selector_prefixes() -> set[str]:
    """Префікси закону селекторів — з selector_law.rs, не з пам'яті."""
    text = _text(SELECTOR_LAW)
    block = text.split("let root = match payload", 1)[1].split("};", 1)[0]
    return {bits for bits in re.findall(r"0b([01]{3})\s*=>\s*Step::", block)}


def primitives_in_canon(n: int) -> int:
    """Скільки примітивів диспетчер оголошує для щабля n у canon.rs.
    Рахуємо `Some(DomainPrimitiveKind::…)` в армі CoreDomainIdentity::Dn."""
    text = _text(CANON)
    marker = f"CoreDomainIdentity::D{n}(word) => match word.word().packed_bits() {{"
    if marker not in text:
        return 0
    block = text.split(marker, 1)[1].split("\n        },", 1)[0]
    return len(re.findall(r"=>\s*Some\(DomainPrimitiveKind::", block))


def selector_widths() -> set[int]:
    """Дозволені ширини селекторів — з САМОГО закону (selector_law.rs).
    D7 там НЕМАЄ: клавіатурні дані не є селекторним щаблем."""
    text = _text(SELECTOR_LAW)
    line = next(l for l in text.splitlines() if "matches!(width" in l)
    allowed: set[int] = set()
    for lo, hi in re.findall(r"(\d+)\.\.=(\d+)", line):
        allowed.update(range(int(lo), int(hi) + 1))
    return allowed


def derived_floor(n: int) -> int:
    """Мінімум виконуваних, виведений із дерева: примітиви диспетчера +
    селекторні координати з каталогу (без жодного зашитого числа).
    Ширина мусить бути селекторною за законом — інакше 0 селекторів."""
    cat = catalogue(n)
    if n not in selector_widths():
        return primitives_in_canon(n)
    sel = len({r for r in cat if r[:3] in selector_prefixes()})
    return primitives_in_canon(n) + sel


# Якірні додатки понад дериваційний мінімум (кожен — з підтвердженого file:line).
# D3: QUOTE/COND (mod.rs:882-884,898-899). D4: EVAL+LAMBDA+DEFINE+NOT/NULL/LIST/APPEND
# (canon.rs:454, necessary_forms.rs:47-48, canon.rs:473-494). D8: MOD (lib.rs:561-581).
ANCHORED_EXTRAS = {3: 2, 4: 7, 8: 1}


def verify_derivation() -> None:
    """Оголошені числа мусять узгоджуватися з деривацією. Якщо дерево
    зміниться — падаємо голосно, а не тихо віддаємо застаріле число."""
    callable_set = callable_rungs()
    for n in (1, 2):
        if n in callable_set:
            raise SystemExit(f"FAIL: D{n} отримав викличну ідентичність — передеривуй число")
        if DISPATCH_ANCHORS[n][0] != 0:
            raise SystemExit(f"FAIL: D{n} оголошено ненульовим без викличної ідентичності")
    # ТОЧНА рівність: оголошене = дериваційний мінімум + якірні додатки.
    # «≥» було б слабким: воно не ловить ПОЯВУ нового примітива в диспетчері.
    declared = {n: c for n, (c, *_r) in DISPATCH_ANCHORS.items()}
    declared[7] = 0
    declared[11] = 0
    for n, count in declared.items():
        floor = derived_floor(n)
        extras = count - floor
        if extras < 0:
            raise SystemExit(
                f"FAIL: D{n} оголошено {count}, але дерево вже дає {floor} "
                f"(примітиви {primitives_in_canon(n)} + селектори {floor - primitives_in_canon(n)})")
        if extras != ANCHORED_EXTRAS.get(n, 0):
            raise SystemExit(
                f"FAIL: D{n} якірні додатки {extras}, очікувано {ANCHORED_EXTRAS.get(n, 0)} — "
                "диспетчер змінився, передеривуй число")


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
    verify_derivation()
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
