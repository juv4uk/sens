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
    cols = ("ук", "укр", "san", "en", "LISP", "sym")
    for _d, rows in disc.load_domain_tables(ROOT).items():
        for row in rows:
            names |= {row[c] for c in cols if isinstance(row.get(c), str) and row[c] not in ("()", "")}
    return names


def project_names() -> dict[str, str]:
    # Усі інструменти використовують одну механічну граматику DEFINE,
    # чинний охоронець драбини. Цей помічник не реалізує Lisp-семантику.
    import importlib.util
    guard_path = ROOT / "scripts" / "guard-domain-function-reuse.py"
    spec = importlib.util.spec_from_file_location("guard_domain_function_reuse", guard_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"немає механічного сканера визначень: {guard_path}")
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)

    out: dict[str, str] = {}
    for rel in _tracked("lib"):
        if not rel.endswith(".lisp") or rel.startswith(("lib/domains/", "lib/generated/", "lib/surface/")):
            continue
        p = ROOT / rel
        if p.is_file():
            for name in guard.definitions(p.read_text(encoding="utf-8", errors="ignore")):
                out.setdefault(name, rel)
    return out


def d11_candidates() -> set[str]:
    out: set[str] = set()
    base = ROOT / "knowledge" / "d11"
    for p in base.rglob("*.tsv"):
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("#") or not line.strip():
                continue
            name = line.split("\t")[0].strip()
            if name and name != "назва_укр":
                out.add(name)
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
    ap.add_argument("--suffix", help="0: перше або 1: решта")
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
    print(f"3) D11-кандидати   : {'Є в реєстрі кандидатів' if in_cands else 'немає'}")

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
    print("        з самовердиктом: хибний закон має відхилити сам SENS;")
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
