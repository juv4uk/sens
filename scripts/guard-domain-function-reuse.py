#!/usr/bin/env python3
"""Guard: програма мусить спиратися на драбини D1–D10, а не винаходити наново.

Правило (AGENTS.md): при написанні програм функції беруться з D1–D10.
  • наявне — вжити (дубль заборонено);
  • немає в програмі — визначити;
  • немає в жодній драбині — кандидат D11 (далі D12…), а не локальний дубль.

ЄДИНИЙ механізм. Цей охоронець НЕ читає драбини сам і НЕ має власної логіки
розпізнавання поверхонь — він ІМПОРТУЄ наявний
`scripts/discover_domain_function_candidates.py` (load_domain_tables + aliases)
і користується ним. Так само має робити будь-який новий інструмент: спершу
шукай наявний механізм, а не плоди дубль.

Статика, fail-closed:
  • нове визначення у зміненому .lisp, чиє ім'я збігається з
    ратифікованою поверхнею D1–D10 → BLOCKED (це дубль);
  • нові імена, яких немає в драбинах → КАНДИДАТИ D11 (інформативно).

Використання:
  python3 scripts/guard-domain-function-reuse.py --staged
  python3 scripts/guard-domain-function-reuse.py --paths-from FILE
  python3 scripts/guard-domain-function-reuse.py --file lib/x.lisp
  python3 scripts/guard-domain-function-reuse.py --self-test

Код виходу: 0 — дублів немає; 1 — знайдено дубль (BLOCKED); 2 — помилка вживання або драбину не перевірено.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISCOVER = ROOT / "scripts" / "discover_domain_function_candidates.py"

EXCLUDED_PREFIXES = (
    "lib/generated/", "lib/surface/", "lib/domains/", "lib/machine/",
    "vendor/", "benchmarks/",
    # lib/core4-parts/** — копії визначень із lib/core4.lisp для контрольованого
    # розбиття. Пари T5M перевіряються окремо; тут фрагменти пропускаємо лише
    # щоб не рахувати їхні дубльовані визначення як нові доменні функції.
    "lib/core4-parts/",
)
# tests/semantic/** — це МОВНІ ЗАКОНИ (Lisp), а не службові тести. Саме там рій
# визначає функції за принципом «мова тесту відповідає шару», тож охоронець
# мусить їх бачити. Решта tests/** лишається поза увагою (фікстури, помічники).
SEMANTIC_PREFIX = "tests/semantic/"
MINIMUM_RATIFIED_SURFACES = 1001
DEF = re.compile(r"\(" + "визначити" + r"\s+([^\s()]+)")


def _load_discover():
    """Імпорт ЄДИНОГО механізму виявлення поверхонь — без власної копії логіки."""
    spec = importlib.util.spec_from_file_location("discover_domain_function_candidates", DISCOVER)
    if spec is None or spec.loader is None:
        raise SystemExit("GUARD-DOMAIN-REUSE: не вдалося завантажити discover_domain_function_candidates.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def ladder_names(root: Path) -> set[str]:
    """Усі людські назви поверхонь драбин — через наявний механізм."""
    discover = _load_discover()
    names: set[str] = set()
    for _domain, rows in discover.load_domain_tables(root).items():
        for row in rows:
            names.update(discover.aliases(row))
    return names


def definitions(text: str) -> list[str]:
    """Лише виконувані Lisp DEFINE: цитовані дані, коментарі й рядки ігноруємо."""
    return [m.group(1) for m in DEF.finditer(_mask_quotes(text))]



MARKER = re.compile(r";\s*D11-пропозиція\s*:", re.IGNORECASE)


_HISTORY_INDEX: dict | None = None


def _history_index() -> dict:
    """Кеш історії: індекс будує scripts/build-guard-history-index.py (один прохід)."""
    global _HISTORY_INDEX
    if _HISTORY_INDEX is None:
        p = ROOT / "knowledge" / "guard-history-index.json"
        try:
            _HISTORY_INDEX = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            _HISTORY_INDEX = {}
    return _HISTORY_INDEX


def introduced_at(rel: str, name: str) -> str:
    """Коли й яким комітом уведено — спершу з ІНДЕКСУ (миттєво), потім з git.

    Індекс: knowledge/guard-history-index.json (будує build-guard-history-index.py).
    Якщо чогось немає — запасний шлях git log -S, повільний, але точний.
    """
    idx = _history_index()
    d = (idx.get("defs") or {}).get(f"{rel}:{name}")
    if d:
        return f"{d['sha']} {d['date']}"
    f = (idx.get("files") or {}).get(rel)
    if f:
        return f"{f['first_sha']} {f['first_date']} (створено файл)"
    try:
        out = subprocess.run(
            ["git", "-c", "core.quotepath=false", "log", "-S", "(" + "визначити " + name,
             "--format=%h %ad", "--date=short", "-1", "--", rel],
            cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip()
        return out or "?"
    except Exception:
        return "?"


def _mask_quotes(text: str) -> str:
    """Mask comments, strings and quoted forms before looking for executable DEFINEs.

    A quoted Lisp form is data, not a new function definition. This scanner is
    deliberately structural: it preserves offsets/newlines and does not decide
    language semantics.
    """
    out = list(text)
    n = len(text)

    def blank(start: int, stop: int) -> None:
        for pos in range(start, stop):
            if text[pos] != "\n":
                out[pos] = " "

    def string_end(start: int) -> int | None:
        pos = start + 1
        while pos < n:
            if text[pos] == "\\":
                pos += 2
                continue
            if text[pos] == '"':
                return pos + 1
            pos += 1
        return None

    def form_end(start: int) -> int | None:
        depth = 0
        pos = start
        while pos < n:
            char = text[pos]
            if char == ";":
                newline = text.find("\n", pos)
                pos = n if newline < 0 else newline + 1
                continue
            if char == '"':
                after = string_end(pos)
                if after is None:
                    return None
                pos = after
                continue
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    return pos + 1
            pos += 1
        return None

    pos = 0
    while pos < n:
        char = text[pos]
        if char == ";":
            newline = text.find("\n", pos)
            stop = n if newline < 0 else newline
            blank(pos, stop)
            pos = stop
            continue
        if char == '"':
            stop = string_end(pos)
            if stop is None:
                blank(pos, n)
                break
            blank(pos, stop)
            pos = stop
            continue
        if text.startswith("(" + "як-є", pos):
            boundary = pos + len("(" + "як-є")
            if boundary == n or text[boundary].isspace() or text[boundary] in "()":
                stop = form_end(pos)
                if stop is not None:
                    blank(pos, stop)
                    pos = stop
                    continue
        pos += 1
    return "".join(out)


def _form_end(masked: str, start: int) -> int | None:
    """End offset of one balanced Lisp form in a code-only view.

    Strings, comments and quoted data have already been blanked while keeping
    offsets. This bounds a DEFINE's body to its own form, so a later top-level
    call cannot accidentally satisfy the ladder-use rule for an earlier one.
    """
    depth = 0
    for pos in range(start, len(masked)):
        if masked[pos] == "(":
            depth += 1
        elif masked[pos] == ")":
            depth -= 1
            if depth == 0:
                return pos + 1
            if depth < 0:
                return None
    return None


def definitions_with_bodies(text: str):
    """Return each DEFINE's own body and whether its D11 marker is present."""
    out = []
    masked = _mask_quotes(text)
    for m in DEF.finditer(masked):
        name = m.group(1)
        before = text[max(0, m.start() - 200):m.start()]
        marked = bool(MARKER.search(before))
        end = _form_end(masked, m.start())
        # A malformed form has no executable body for purposes of this guard;
        # the caller must not treat unrelated later text as use of the ladder.
        body = masked[m.end():end - 1] if end is not None else ""
        out.append((name, body, marked))
    return out


# Структурні/синтаксичні голови — це не «вживання операції», а будова форми.
# Їх не рахуємо як виклик драбини, інакше кожне визначення з анонімною функцією «кликало б» драбину.
STRUCTURAL = {
    "визначити", "функція", "за-умовою", "як-є", "нехай", "нехай-послідовно",
    "нехай*", "пропустити", "так", "ні",
}


def _calls_ladder(body: str, ladder: set[str]) -> bool:
    calls = set(re.findall(r"\(\s*([^\s()]{2,})", body))
    return bool((calls & ladder) - STRUCTURAL)



def project_definition_sites(root: Path) -> dict[str, set[str]]:
    """Позиції чинних DEFINE: власне визначення не є власним дублем."""
    sites: dict[str, set[str]] = {}
    files = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files", "lib"],
                           cwd=root, capture_output=True, text=True).stdout.split()
    for rel in files:
        if not rel.endswith(".lisp") or rel.startswith(("lib/domains/", "lib/generated/", "lib/surface/")):
            continue
        path = root / rel
        if path.is_file():
            # Цитована DEFINE є даними, а не ще одним визначенням функції.
            for name in definitions(path.read_text(encoding="utf-8", errors="ignore")):
                sites.setdefault(name, set()).add(rel)
    return sites


def project_names(root: Path) -> set[str]:
    """Зберігаємо інтерфейс пошуку вже визначених функцій проєкту."""
    return set(project_definition_sites(root))


def duplicates_project_definition(sites: dict[str, set[str]], name: str, rel: str) -> bool:
    """Дубль означає наявність визначення в іншому файлі, не в самому rel."""
    return bool(sites.get(name, set()) - {rel})



CANDIDATES_TSV = ROOT / "knowledge" / "d11" / "база-доступних-функцій" / "внутрішні-визначення-SENS-для-D11-20261022.tsv"


def register_candidates(cands: list[tuple[str, str]]) -> int:
    """Дописати виявлених кандидатів D11 у чинний реєстр — явно й без дублів.

    Власник: механіка має бути комфортна й нею активно користуються. Тому
    «виявив» одразу стає «додав»: рядок із джерелом і статусом
    «КАНДИДАТ (не ратифіковано)», координата порожня (опкоду не дає).
    """
    if not CANDIDATES_TSV.is_file():
        return 0
    lines = CANDIDATES_TSV.read_text(encoding="utf-8").splitlines()
    header = None
    existing: set[str] = set()
    for ln in lines:
        if ln.startswith("#") or not ln.strip():
            continue
        if header is None:
            header = ln
            continue
        existing.add(ln.split("\t")[0].strip())
    ncol = len(header.split("\t")) if header else 12
    added: list[str] = []
    for rel, name in cands:
        if name in existing:
            continue
        row = [name, rel, "", "family/невідомо", "КАНДИДАТ (не ратифіковано)",
               "", "так", "ні", "", "", "", "низька"]
        while len(row) < ncol:
            row.append("")
        added.append("\t".join(row[:ncol]))
        existing.add(name)
    if added:
        with open(CANDIDATES_TSV, "a", encoding="utf-8") as f:
            f.write("\n" + "\n".join(added) + "\n")
    return len(added)


def changed_files(args) -> list[str]:
    if args.file:
        return list(args.file)
    if args.paths_from:
        return [ln.strip() for ln in Path(args.paths_from).read_text(encoding="utf-8").splitlines() if ln.strip()]
    if args.staged:
        out = subprocess.run(
            ["git", "-c", "core.quotepath=false", "diff", "--name-only", "--cached"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        ).stdout
        return [ln.strip() for ln in out.splitlines() if ln.strip()]
    return []


def hook_installed() -> tuple[bool, str]:
    """Чи охоронець СПРАВДІ увімкнений у git — а не лише лежить у репо.

    Гачок, який не виконуваний або не в hooksPath, git МОВЧКИ ігнорує
    (це вже траплялось: режим 100644 замість 100755). Self-test мусить це бачити.
    """
    import subprocess as _sp
    hp = _sp.run(["git", "config", "--get", "core.hooksPath"], cwd=ROOT,
                 capture_output=True, text=True).stdout.strip()
    if hp != "githooks":
        return False, f"core.hooksPath={hp or '(порожньо)'} — увімкни: bash scripts/install-hooks.sh"
    hook = ROOT / "githooks" / "pre-commit"
    if not hook.is_file():
        return False, "немає githooks/pre-commit"
    import os as _os
    if not _os.access(hook, _os.X_OK):
        return False, "githooks/pre-commit не виконуваний — git його мовчки ігнорує"
    return True, "увімкнено (githooks/pre-commit виконуваний)"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="guard: вживати функції драбин D1–D10")
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--paths-from")
    ap.add_argument("--base", help="базовий SHA; перевіряти лише ДОДАНІ визначення")
    ap.add_argument("--file", action="append")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--register", action="store_true", help="дописати виявлених кандидатів у реєстр D11")
    ap.add_argument("--advise", action="store_true", help="замість BLOCKED — конкретні поради, що виправити")
    ap.add_argument("--when", action="store_true", help="додати, коли й яким комітом уведено кожне визначення")
    args = ap.parse_args(argv)

    ladder = ladder_names(ROOT)
    # Неповне виявлення драбини небезпечніше за звичайний RED: охоронець
    # може не впізнати чинну поверхню або хибно оголосити нову. Відмовляємося
    # працювати, якщо завантажено менше за мінімум, який уже вимагає self-test.
    if len(ladder) < MINIMUM_RATIFIED_SURFACES:
        print(
            "GUARD-DOMAIN-REUSE: НЕ ПЕРЕВІРЕНО — "
            f"виявлено лише {len(ladder)} поверхонь; "
            f"потрібно щонайменше {MINIMUM_RATIFIED_SURFACES}; "
            "джерело: discover_domain_function_candidates",
            file=sys.stderr,
        )
        return 2
    project_sites = project_definition_sites(ROOT)

    if args.self_test:
        ok = len(ladder) >= MINIMUM_RATIFIED_SURFACES
        print(f"GUARD-DOMAIN-REUSE self-test: {'OK' if ok else 'FAIL'} (поверхонь у драбинах: {len(ladder)}, джерело: discover_domain_function_candidates)")
        # Перевіряємо і ВЛАСНУ активацію: невиконуваний гачок = мертвий охоронець.
        hok, hmsg = hook_installed()
        print(f"GUARD-DOMAIN-REUSE self-test: гачок {'OK' if hok else 'НЕ УВІМКНЕНО'} — {hmsg}")
        return 0 if (ok and hok) else 1

    if not (args.staged or args.paths_from or args.file):
        ap.error("потрібен --staged / --paths-from / --file")

    blocked: list[tuple[str, str, str]] = []
    usage: dict[str, int] = {}
    new_defs: dict[str, int] = {}
    candidates: list[tuple[str, str]] = []
    checked = 0
    for rel in changed_files(args):
        if not rel.endswith(".lisp"):
            continue
        if any(rel.startswith(p) for p in EXCLUDED_PREFIXES):
            continue
        if rel.startswith("tests/") and not rel.startswith(SEMANTIC_PREFIX):
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        checked += 1
        text = path.read_text(encoding="utf-8")
        known: set[str] = set()
        if args.base:
            try:
                old_text = subprocess.run(
                    ["git", "show", f"{args.base}:{rel}"], cwd=ROOT,
                    capture_output=True, text=True, check=False).stdout
            except Exception:
                old_text = ""
            known = {n for n, _, _ in definitions_with_bodies(old_text)}
        active_text = _mask_quotes(text)
        usage[rel] = sum(
            1 for head in re.findall(r"\(\s*([^\s()]{2,})", active_text)
            if head in ladder and head not in STRUCTURAL
        )
        for name, body, marked in definitions_with_bodies(text):
            if args.base and name in known:
                continue  # не чіпаємо те, що вже було до зміни
            new_defs[rel] = new_defs.get(rel, 0) + 1
            if name in ladder:
                blocked.append((rel, name, "дубль наявної поверхні драбини"))
                continue
            if duplicates_project_definition(project_sites, name, rel):
                blocked.append((rel, name, "дубль наявного визначення проєкту"))
                continue
            if not marked and not _calls_ladder(body, ladder):
                # Нове ім'я без жодного виклику поверхні драбини і без маркера —
                # це або перевинахід наявної операції, або неусвідомлена нова.
                blocked.append((rel, name, "нове ім'я без виклику драбини і без маркера D11-пропозиції"))
                continue
            candidates.append((rel, name))

    # Вживання драбин: скільки разів змінений файл кличе НАЯВНІ поверхні.
    if usage:
        idle = sorted(r for r in usage if usage[r] == 0 and new_defs.get(r, 0) > 0)
        for rel in sorted(usage):
            print(f"ВЖИВАННЯ ДРАБИН: {rel}: {usage[rel]} викликів наявних поверхонь, {new_defs.get(rel,0)} нових визначень")
        if idle:
            print("УВАГА: файли з новими визначеннями, але БЕЗ жодного вживання наявних функцій D1–D10: " + ", ".join(idle))

    for rel, name in candidates:
        print(f"КАНДИДАТ D11: {rel}: {name} — немає в драбинах; пропозиція D11 (далі D12…)")
    # Заблокований зріз не має змінювати реєстр кандидатів D11.
    if args.register and candidates and not blocked:
        n = register_candidates(candidates)
        print(f"ЗАРЕЄСТРОВАНО в D11: {n} нових кандидатів → реєстр кандидатів D11 "
              f"(наявні не дублювались; статус кандидат, не ратифіковано)")
    elif args.register and candidates and blocked:
        print("НЕ ЗАРЕЄСТРОВАНО в D11: є BLOCKED; спершу виправ усі порушення.")

    if args.advise and blocked:
        shadow = [(r, n) for r, n, w in blocked if "драбини" in w]
        project = [(r, n) for r, n, w in blocked if "проєкту" in w]
        fresh = [(r, n) for r, n, w in blocked if "драбини" not in w and "проєкту" not in w]
        print(f"\nПОРАДИ (--advise): {len(blocked)} виправлень у {len({r for r, _, _ in blocked})} файлах")
        if shadow:
            print(f"\n  А) ЗАТІНЮЄ ДРАБИНУ ({len(shadow)}) — ужий наявну поверхню, не перевизначай:")
            for r, n in shadow[:12]:
                when = f"  [уведено {introduced_at(r, n)}]" if args.when else ""
                print(f"     {r}: «{n}» уже є поверхнею драбини — прибери своє визначення й клич драбину{when}")
                print(f"        де саме: python3 scripts/search-domain-function.py {n}")
            if len(shadow) > 12:
                print(f"     … ще {len(shadow) - 12}")
        if project:
            print(f"\n  Б) ЗАТІНЮЄ ПРОЄКТ ({len(project)}) — ужий наявне визначення проєкту:")
            for r, n in project[:8]:
                print(f"     {r}: «{n}» уже визначено в проєкті — не перевизначай")
                print(f"        де саме: python3 scripts/search-domain-function.py {n}")
        if fresh:
            print(f"\n  В) БЕЗ ДРАБИНИ ({len(fresh)}) — або вжий наявну поверхню, або познач причину:")
            for r, n in fresh[:12]:
                when = f"  [уведено {introduced_at(r, n)}]" if args.when else ""
                print(f"     {r}: «{n}» — додай вживання поверхні драбини, або `; D11-пропозиція: <причина>`{when}")
            if len(fresh) > 12:
                print(f"     … ще {len(fresh) - 12}")
        print()
    if blocked:
        for rel, name, why in blocked:
            print(f"BLOCKED: {rel}: «{name}» — {why}. Вжий наявну поверхню драбини, або познач "
                  f"`; D11-пропозиція: <причина>` перед визначенням, якщо операції справді немає.")
        print(f"GUARD-DOMAIN-REUSE: BLOCKED ({len(blocked)} порушень серед {checked} файлів)")
        return 1

    # Мертвий охоронець не має права казати OK. Якщо він не побачив ЖОДНОГО
    # файлу — це не «все чисто», а «перевірка не відбулась» (буває, коли шлях
    # виключено, гачок не активний, або список порожній). Мовчазне OK тут
    # небезпечніше за хибний RED: воно створює враження, що перевірку зроблено.
    if checked == 0:
        print("УВАГА: охоронець не перевірив ЖОДНОГО файлу — це не «все чисто», "
              "а «перевірка не відбулась». Переконайся, що шлях не виключено "
              "й гачок активний (bash scripts/install-hooks.sh).", file=sys.stderr)
        print(f"GUARD-DOMAIN-REUSE: НЕ ПЕРЕВІРЕНО (0 файлів)")
        return 2
    print(f"GUARD-DOMAIN-REUSE: OK ({checked} файлів, {len(candidates)} кандидатів D11)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
