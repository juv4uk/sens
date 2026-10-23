#!/usr/bin/env python3
"""Додати функцію в D11 — один простий шлях, зрозумілий агентові.

Навіщо: раніше додавання в D11 вимагало тримати в голові п'ять кроків (пошук по
драбинах, пошук у проєкті, селекторна похідна, сімейний закон, охоронець). Тут —
одна команда, яка все це робить і каже, що саме робити далі.

Приклади:
    python3 scripts/add-d11-function.py фільтрувати
    python3 scripts/add-d11-function.py --parent 0110000000 --suffix 1
    python3 scripts/add-d11-function.py сполучити          # уже є → вжий
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _tracked(pattern: str) -> list[str]:
    out = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files", pattern],
                         cwd=ROOT, capture_output=True, text=True).stdout
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def ladder_names() -> set[str]:
    sys.path.insert(0, str(ROOT / "scripts"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("disc", ROOT / "scripts" / "discover_domain_function_candidates.py")
    disc = importlib.util.module_from_spec(spec); sys.modules["disc"] = disc; spec.loader.exec_module(disc)
    names: set[str] = set()
    # D11 містить похідні та дослідні назви, але НЕ є ратифікованою
    # драбиною D1–D10. Єдиний механізм проєкцій — aliases() з discover.
    for domain, rows in disc.load_domain_tables(ROOT).items():
        if domain > 10:
            continue
        for row in rows:
            names.update(disc.aliases(row))
    return names


def project_names() -> dict[str, str]:
    out: dict[str, str] = {}
    for rel in _tracked("lib"):
        if not rel.endswith(".lisp") or rel.startswith(("lib/domains/", "lib/generated/", "lib/surface/")):
            continue
        p = ROOT / rel
        if p.is_file():
            for m in re.finditer(r"\(" + "визначити" + r"\s+([^\s()]+)", p.read_text(encoding="utf-8", errors="ignore")):
                out.setdefault(m.group(1), rel)
    return out


def d11_candidates() -> set[str]:
    """Лише чинний JSON, а не архівні TSV чи старі пропозиції."""
    path = ROOT / "knowledge" / "d11" / "база-доступних-функцій" / "кандидати.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "sens.available-functions/v1" or not isinstance(data.get("rows"), list):
        raise ValueError(f"невідомий формат чинного реєстру D11: {path}")
    rows = data["rows"]
    out: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"неправильний рядок чинного реєстру D11: {path}")
        for key in ("surface_name", "uk_surface_proposal"):
            name = row.get(key)
            if isinstance(name, str) and name.strip():
                out.add(name.strip())
    recorded = data.get("counts", {}).get("total")
    if recorded != len(rows):
        print(
            f"УВАГА D11: metadata counts.total={recorded}, фактичних rows={len(rows)}; "
            "для пошуку використано лише rows чинного JSON",
            file=sys.stderr,
        )
    return out


def is_selector_derived(coord: str) -> str | None:
    seed = ROOT / "knowledge" / "d11-selector-seed.json"
    if not seed.is_file():
        return None
    rows = json.loads(seed.read_text(encoding="utf-8")).get("rows", [])
    return next((lisp for bits, lisp in rows if bits == coord), None)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="додати функцію в D11 — один шлях")
    ap.add_argument("name", nargs="?", help="бажана укр-назва нової функції")
    ap.add_argument("--parent", help="10-бітна координата батька (селекторна похідна)")
    ap.add_argument("--suffix", help="0: селектор голови, 1: селектор хвоста")
    args = ap.parse_args(argv)

    print("═" * 62)
    print("ДОДАВАННЯ В D11 — покроково")
    print("═" * 62)

    # Крок 0: селекторна похідна — якщо агент уже знає батька й суфікс
    if args.parent and args.suffix:
        coord = args.parent + args.suffix
        lisp = is_selector_derived(coord)
        print(f"0) Селекторна похідна: координата {coord} → {lisp or 'нових рядок за законом'}")
        print("   Далі:  python3 scripts/derive-d11-coordinate.py "
              f"{args.parent} {args.suffix}  → готовий рядок у lib/domains/d11.lisp")
        return 0

    if not args.name:
        ap.error("дай назву (або --parent і --suffix)")

    name = args.name
    ladder = ladder_names()
    project = project_names()
    cands = d11_candidates()

    print(f"\nШУКАЮ: «{name}»\n")
    on_ladder = name in ladder
    in_project = name in project
    in_cands = name in cands

    print(f"1) Драбини D1–D10 : {'Є — ВЖИЙ, не визначай' if on_ladder else 'немає'}")
    print(f"2) Проєкт (lib)    : {'Є у ' + project[name] + ' — ВЖИЙ' if in_project else 'немає'}")
    print(f"3) D11-кандидати   : {'Є в чинному JSON (назва, не доказ закону)' if in_cands else 'немає в чинному JSON'}")

    # СХОЖІ (не точні) назви — щоб агент не створив дубль під іншим ім'ям.
    import difflib
    pool = ladder | set(project) | cands
    substr = {n for n in pool if n != name and name.lower() in n.lower()}
    # Складені імена: порівнюємо ще й за головою (перший складник до «-»),
    # бо «частота» і «частоти-елементів-унарно» різняться лише закінченням голови.
    heads = {n: n.split("-")[0].split(":")[-1] for n in pool if n != name}
    fuzzy = set(difflib.get_close_matches(name, list(heads.values()), n=12, cutoff=0.82))
    by_head = {n for n, h in heads.items() if h in fuzzy}
    fuzzy_full = set(difflib.get_close_matches(name, [n for n in pool if n != name], n=12, cutoff=0.72))
    # Сортуємо за релевантністю: підрядок → голова → решта; і обмежуємо 8.
    ordered = sorted(substr, key=str.lower) + sorted(by_head - substr, key=str.lower) + \
              sorted(fuzzy_full - substr - by_head, key=str.lower)
    near = ordered[:8]
    if near:
        print(f"\nСХОЖІ назви — перевір, чи це та сама операція:")
        for n in near:
            where = "драбина" if n in ladder else (project.get(n, "D11-кандидат"))
            print(f"   • {n:<34} ← {where}")

    print("\n" + "─" * 62)
    if on_ladder:
        print("ВЕРДИКТ: наявна поверхня драбини. Вжий її. Нічого не додавай.")
        return 0
    if in_project:
        print(f"ВЕРДИКТ: уже визначено в {project[name]}. Вжий наявне.")
        return 0
    if in_cands:
        print("ВЕРДИКТ: це вже кандидат D11 (без координати). Не дублюй —"
              " доповни/уточни наявний запис кандидата.")
        return 0

    print("ВЕРДИКТ: нова функція. Обери шлях за типом:\n")
    print("  А) СЕЛЕКТОРНА ПОХІДНА (композиція перше/решта над батьком з D10):")
    print("     python3 scripts/derive-d11-coordinate.py <батько-10біт> <0|1>")
    print("     → отримаєш координату, назви й готовий рядок для lib/domains/d11.lisp")
    print()
    print("  Б) СІМЕЙНИЙ ЗАКОН (відбір/множини/асоціації/лічба тощо):")
    print("     1. визнач функцію в lib/d11-<сімейство>.lisp, уживаючи наявні поверхні драбин;")
    print("     2. додай її до закону сімейства (knowledge/d11/закони-пропозиція-*.md);")
    print("     3. напиши SENS-свідка tests/semantic/d11-<сімейство>-{law,mutant}.lisp")
    print("        з самовердиктом D1, обчисленим нативним SENS;")
    print("     4. додай --binding-source у scripts/execute_changed_lisp_t5m.sh.")
    print()
    print("  Координата: null (сімейний закон не дає opcode). Це ПРОПОЗИЦІЯ —"
          " допуск дає доведений закон + нативний свідок + рішення власника.")
    print("─" * 62)
    print("ПЕРЕВІРКА перед пушем:")
    print("  python3 scripts/guard-domain-function-reuse.py --file <твій lib-файл> --base HEAD")
    print("  python3 scripts/search-domain-function.py <назва>   # переконайся, що бачиться")
    return 0


if __name__ == "__main__":
    sys.exit(main())
