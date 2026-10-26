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
  python3 scripts/guard-domain-function-reuse.py --catalog [запит]
  python3 scripts/guard-domain-function-reuse.py --better "обробити список"
  python3 scripts/guard-domain-function-reuse.py --staged
  python3 scripts/guard-domain-function-reuse.py --paths-from FILE
  python3 scripts/guard-domain-function-reuse.py --file lib/x.lisp
  python3 scripts/guard-domain-function-reuse.py --self-test

Код виходу: 0 — дублів немає; 1 — знайдено дубль (BLOCKED); 2 — помилка вживання або драбину не перевірено.
"""
from __future__ import annotations

import argparse
from collections import Counter
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

# Коди причин BLOCKED. Класифікація в --advise ухвалює рішення за ТОЧНИМ кодом
# причини, а не за підрядком у її тексті: інакше «дубль наявної поверхні драбини»
# (клас А) зливається з «нове ім'я без виклику драбини…» (окремий клас), бо
# обидві причини містять підрядок «драбини» — і клас А виходить завищеним.
REASON_DUP_IN_FILE = "повторне визначення в одному файлі"
REASON_SHADOW_LADDER = "дубль наявної поверхні драбини"
REASON_SHADOW_PROJECT = "дубль наявного визначення проєкту"
REASON_FRESH_NAME = "нове ім'я без виклику драбини і без маркера D11-пропозиції"


_DISCOVER_MODULE = None


def _load_discover():
    """Імпорт ЄДИНОГО механізму виявлення поверхонь — без власної копії логіки.

    Модуль кешується: каталог і підказка звертаються до нього багато разів, а
    повторний exec_module — зайва праця. Логіка виявлення лишається одна.
    """
    global _DISCOVER_MODULE
    if _DISCOVER_MODULE is not None:
        return _DISCOVER_MODULE
    spec = importlib.util.spec_from_file_location("discover_domain_function_candidates", DISCOVER)
    if spec is None or spec.loader is None:
        raise SystemExit("GUARD-DOMAIN-REUSE: не вдалося завантажити discover_domain_function_candidates.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _DISCOVER_MODULE = module
    return module


def ladder_names(root: Path) -> set[str]:
    """Усі людські назви поверхонь драбин — через наявний механізм."""
    discover = _load_discover()
    names: set[str] = set()
    for domain, rows in discover.load_domain_tables(root).items():
        # D11 — робочий домен похідних, а не ратифікована драбина D1–D10.
        if domain > 10:
            continue
        for row in rows:
            names.update(discover.aliases(row))
    return names


def definitions(text: str) -> list[str]:
    """Лише виконувані Lisp DEFINE: цитовані дані, коментарі й рядки ігноруємо."""
    return [m.group(1) for m in DEF.finditer(_mask_quotes(text))]



MARKER = re.compile(
    r"^[ \t]*;+[ \t]*D11-пропозиція[ \t]*:[ \t]*\S[^\r\n]*$",
    re.IGNORECASE | re.MULTILINE,
)

# Клас А («дубль наявної поверхні драбини»): закон може НАВМИСНЕ визначити
# однойменну функцію з ІНШИМ тілом (не дубль). Маркер діє ЛИШЕ з непорожньою
# причиною після `—`/`:` — порожній маркер не приймається, інакше це діра
# для вимкнення охоронця.
MARKER_INTENT = re.compile(
    r"^[ \t]*;+[ \t]*НАВМИСНО[ \t]*:[ \t]*інший закон[ \t]*[—–:\-][ \t]*\S[^\r\n]*$",
    re.IGNORECASE | re.MULTILINE,
)


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


def _norm_path(rel: str) -> str:
    """Один формат шляху: без провідного `./`, з прямими слешами."""
    rel = str(rel).replace("\\", "/").strip()
    while rel.startswith("./"):
        rel = rel[2:]
    return rel.lstrip("/")


def hot_paths() -> dict[str, dict]:
    """Гарячі файли з індексу історії: шлях → запис {commits, last_date, …}.

    Індекс будує scripts/build-guard-history-index.py. Ключ `hot_files` —
    список словників із полем `path`, але приймаємо й словник {шлях: дані}.
    Порожній результат означає «індексу немає» — тоді попередження мовчить.
    """
    raw = _history_index().get("hot_files")
    out: dict[str, dict] = {}
    if isinstance(raw, list):
        for h in raw:
            if isinstance(h, dict) and h.get("path"):
                out[_norm_path(h["path"])] = h
    elif isinstance(raw, dict):
        for key, val in raw.items():
            entry = dict(val) if isinstance(val, dict) else {}
            entry.setdefault("path", key)
            out[_norm_path(key)] = entry
    return out


def hot_warning(paths) -> None:
    """Попередження (НЕ змінює код виходу): гарячі файли правлять МАЛЕНЬКИМИ кроками.

    Урок №1 з docs/guard-history-reference.uk.md, тепер дією: щойно охоронець
    бере на перевірку гарячий файл, він попереджає — і для OK, і для BLOCKED.
    """
    hot = hot_paths()
    if not hot:
        return  # індексу немає — тихо, це не помилка перевірки
    seen: set[str] = set()
    for rel in paths:
        key = _norm_path(rel)
        if key in seen or key not in hot:
            continue
        seen.add(key)
        entry = hot[key]
        print(
            f"ГАРЯЧИЙ ФАЙЛ: {key} — {entry.get('commits')} змін, "
            f"остання {entry.get('last_date')}. "
            "Прав МАЛЕНЬКИМИ кроками (одне визначення), не переписуй файл.",
            file=sys.stderr,
        )


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

    # БЛОКОВІ КОМЕНТАРІ #| … |# — не семантичний носій.
    # Раніше маскувались лише рядкові `;`, тому `(визначити довжина …)`
    # усередині #| … |# вважалось справжнім визначенням і давало фальшивий
    # BLOCKED. Коментар — не код: це те саме правило, що strip_comments
    # у scripts/migrate-three-pass.py і «коментар не потрібно кодувати».
    _depth = 0
    _start = 0
    _pos = 0
    while _pos < n - 1:
        if text[_pos] == "#" and text[_pos + 1] == "|":
            if _depth == 0:
                _start = _pos
            _depth += 1
            _pos += 2
            continue
        if text[_pos] == "|" and text[_pos + 1] == "#" and _depth:
            _depth -= 1
            _pos += 2
            if _depth == 0:
                blank(_start, _pos)
            continue
        _pos += 1
    if _depth:
        blank(_start, n)

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


def _preceding_comment_block(text: str, start: int) -> str:
    """Коментарі безпосередньо перед DEFINE, без сусідніх визначень."""
    line_start = text.rfind("\n", 0, start) + 1
    if text[line_start:start].strip():
        return ""
    lines = text[:line_start].splitlines()
    comments = []
    while lines and lines[-1].lstrip().startswith(";"):
        comments.append(lines.pop())
    return "\n".join(reversed(comments))


def definitions_with_bodies(text: str):
    """Return each DEFINE's own body, D11 marker and intent-marker presence."""
    out = []
    masked = _mask_quotes(text)
    for m in DEF.finditer(masked):
        name = m.group(1)
        comments = _preceding_comment_block(text, m.start())
        marked = bool(MARKER.search(comments))
        intent = bool(MARKER_INTENT.search(comments))
        end = _form_end(masked, m.start())
        # A malformed form has no executable body for purposes of this guard;
        # the caller must not treat unrelated later text as use of the ladder.
        body = masked[m.end():end - 1] if end is not None else ""
        out.append((name, body, marked, intent))
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
    # Порожній stdout від помилки Git не є доказом відсутності дублів.
    # -z зберігає пробіли/переноси у назвах файлів без розділення за whitespace.
    command = ["git", "-c", "core.quotepath=false", "ls-files", "-z", "--", "lib"]
    try:
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    except (OSError, UnicodeError) as exc:
        print(f"GUARD-DOMAIN-REUSE: НЕ ПЕРЕВІРЕНО — git ls-files lib: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    if result.returncode != 0:
        print(
            f"GUARD-DOMAIN-REUSE: НЕ ПЕРЕВІРЕНО — git ls-files lib code={result.returncode} "
            f"stderr={result.stderr.strip()}",
            file=sys.stderr,
        )
        raise SystemExit(2)
    files = result.stdout.split("\0")
    for rel in files:
        # core4-parts — проєкційні дзеркала lib/core4.lisp. Вони не є
        # незалежними визначеннями проєкту; інакше будь-який новий
        # SENS-помічник Core4 стає хибним «дублем іншого файла».
        # Мовні DEFINE частин перевіряє окремий парний SENS/T5M guard.
        if not rel.endswith(".lisp") or rel.startswith(
            ("lib/domains/", "lib/generated/", "lib/surface/", "lib/core4-parts/")
        ):
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
        # -z не втрачає Unicode, пробіли та вбудовані переноси рядків у шляхах Git.
        command = ["git", "-c", "core.quotepath=false", "diff", "--name-only", "--cached", "--diff-filter=ACMR", "-z"]
        try:
            result = subprocess.run(
                command, cwd=ROOT, capture_output=True, text=True, check=False,
            )
        except (OSError, UnicodeError) as exc:
            print(f"GUARD-DOMAIN-REUSE: НЕ ПЕРЕВІРЕНО — git diff --cached: {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
        if result.returncode != 0:
            print(
                f"GUARD-DOMAIN-REUSE: НЕ ПЕРЕВІРЕНО — git diff --cached code={result.returncode} "
                f"detail={result.stderr.strip()}",
                file=sys.stderr,
            )
            raise SystemExit(2)
        # Ніколи не strip(): пробіли можуть бути частиною реального імені файлу.
        return [rel for rel in result.stdout.split("\0") if rel]
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


# --- База знань охоронця у формі CLIPS: проста ВИБІРКА фактів (не рушій правил). ---
# Факт відрізняється від взірця в правилі наявністю слота (source ...).
GUARD_FACT = re.compile(r"\(guard-fact\s+(?:\([^()]*\)\s*)+\)")

KNOWLEDGE_ADVICE = {
    "hot-file": "правити МАЛЕНЬКИМИ кроками",
    "layer": "перевіряй Zig-тестами",
    "error-class": "ужий наявну поверхню драбини",
}


def _knowledge_slot(chunk: str, slot: str) -> str | None:
    m = re.search(r"\(" + slot + r"\s+\"?([^\")]*)\"?\)", chunk)
    return m.group(1).strip() if m else None


def knowledge_advice(kind: str) -> str:
    """Порада за класом факта (kind) — те саме, що виводять правила CLIPS."""
    return KNOWLEDGE_ADVICE.get(kind, "дій за правилами бази знань")


def knowledge_facts(text: str) -> list[tuple[str, str, str, str]]:
    """Витягти guard-fact із CLIPS-тексту ПРОСТИМ розбором (regex), без рушія.

    Беремо лише ті форми, де є всі чотири слоти (kind, name, value, source):
    взірці всередині (defrule …) слота source не мають, тож не рахуються як
    факти. Якщо чогось не збіглось — не падаємо, а повертаємо те, що знайшли.
    """
    out: list[tuple[str, str, str, str]] = []
    for m in GUARD_FACT.finditer(text):
        chunk = m.group(0)
        kind = _knowledge_slot(chunk, "kind")
        name = _knowledge_slot(chunk, "name")
        value = _knowledge_slot(chunk, "value")
        source = _knowledge_slot(chunk, "source")
        if kind and name and value and source:
            out.append((kind, name, value, source))
    return out


# --- Міні-(run): застосувати правила (defrule …) до фактів і ВИВЕСТИ поради. ---
# Це не повний рушій CLIPS (Rust не тягнемо): беремо перший патерн
# (guard-fact (kind K) …) як УМОВУ й (assert (guard-advice …)) як ДІЮ. Цього
# досить, щоб доданий факт або правило справді ДІЯЛО, а не лежало декларацією.


def _clips_atoms(text: str) -> list:
    """Токенізувати CLIPS: дужки, символи й рядки (з урахуванням ;-коментарів).

    Рядки беремо ЦІЛКОМ — лапки всередині дужок не плутають розбір
    (напр. порада "перевіряй Zig-тестами (ізоляція), не Rust").
    """
    tokens: list = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == ";":
            while i < n and text[i] != "\n":
                i += 1
        elif ch in " \t\r\n":
            i += 1
        elif ch in "()":
            tokens.append(ch)
            i += 1
        elif ch == '"':
            j = i + 1
            buf: list[str] = []
            while j < n:
                if text[j] == "\\" and j + 1 < n:
                    buf.append(text[j + 1])
                    j += 2
                    continue
                if text[j] == '"':
                    break
                buf.append(text[j])
                j += 1
            tokens.append(("str", "".join(buf)))
            i = j + 1
        else:
            j = i
            while j < n and text[j] not in " \t\r\n()\"":
                j += 1
            tokens.append(("sym", text[i:j]))
            i = j
    return tokens


def _clips_forms(text: str) -> list:
    """Розібрати токени у вкладені списки (S-вирази). Стійко до обірваних форм."""
    tokens = _clips_atoms(text)
    pos = 0

    def parse_one():
        nonlocal pos
        tok = tokens[pos]
        if tok == "(":
            pos += 1
            items: list = []
            while pos < len(tokens) and tokens[pos] != ")":
                items.append(parse_one())
            pos += 1  # закриваюча дужка
            return items
        pos += 1
        return tok

    forms: list = []
    while pos < len(tokens):
        forms.append(parse_one())
    return forms


def _sym(node) -> str | None:
    return node[1] if isinstance(node, tuple) and node[0] == "sym" else None


def _atom_text(node) -> str | None:
    return node[1] if isinstance(node, tuple) and node[0] in ("sym", "str") else None


def _slot(node, name: str):
    """Значення слота (name …) у формі; None, якщо слота немає."""
    if not isinstance(node, list):
        return None
    for child in node[1:]:
        if isinstance(child, list) and _sym(child[0]) == name and len(child) >= 2:
            return child[1]
    return None


def _find_guard_advice(nodes) -> list | None:
    """Знайти (guard-advice …) у піддереві дії (assert …)."""
    for node in nodes:
        if isinstance(node, list):
            if _sym(node[0]) == "guard-advice":
                return node
            found = _find_guard_advice(node[1:])
            if found is not None:
                return found
    return None


def knowledge_rules(text: str) -> list[dict]:
    """Витягти (defrule …) із CLIPS-тексту простим розбором (без рушія).

    Для кожного правила беремо:
      • УМОВУ — перший патерн (guard-fact (kind K) …): kind (обов'язково) і,
        якщо value — ЛІТЕРАЛ (не ?змінна), то його значення (решта слотів —
        зв'язування, не умова);
      • ДІЮ — (assert (guard-advice (file …) (advice "…") (why …))).
    Нерозібране правило ПРОПУСКАЄМО (попередження в stderr), не падаємо.
    """
    rules: list[dict] = []
    for form in _clips_forms(text):
        if not (isinstance(form, list) and _sym(form[0]) == "defrule"):
            continue
        name = _sym(form[1]) or "?"
        arrow = next(
            (k for k, node in enumerate(form) if _sym(node) == "=>"), None)
        if arrow is None:
            print(f"GUARD-DOMAIN-REUSE --knowledge: правило «{name}» без => — пропущено",
                  file=sys.stderr)
            continue
        pattern = next(
            (node for node in form[2:arrow]
             if isinstance(node, list) and _sym(node[0]) == "guard-fact"), None)
        if pattern is None:
            print(f"GUARD-DOMAIN-REUSE --knowledge: правило «{name}» без патерна guard-fact — пропущено",
                  file=sys.stderr)
            continue
        kind = _atom_text(_slot(pattern, "kind"))
        if not kind or kind.startswith("?"):
            print(f"GUARD-DOMAIN-REUSE --knowledge: правило «{name}» без літерального kind — пропущено",
                  file=sys.stderr)
            continue
        value_node = _slot(pattern, "value")
        value_literal = _atom_text(value_node)
        if value_literal is not None and value_literal.startswith("?"):
            value_literal = None  # ?змінна — це зв'язування, не умова
        advice_node = _find_guard_advice(form[arrow + 1:])
        advice = _atom_text(_slot(advice_node, "advice")) if advice_node else None
        if not advice:
            print(f"GUARD-DOMAIN-REUSE --knowledge: правило «{name}» без поради advice — пропущено",
                  file=sys.stderr)
            continue
        rules.append({
            "name": name,
            "kind": kind,
            "value": value_literal,
            "file": _slot(advice_node, "file") if advice_node else None,
            "why": _slot(advice_node, "why") if advice_node else None,
            "advice": advice,
        })
    return rules


def _resolve_binding(node, name: str, value: str) -> str:
    """Зв'язати ?f/?n → name, ?v → value; літерал лишаємо як є."""
    text = _atom_text(node)
    if text is None:
        return name
    if text.startswith("?"):
        if text in ("?f", "?n"):
            return name
        if text == "?v":
            return value
        return text
    return text


def knowledge_inference(text: str, facts: list[tuple[str, str, str, str]]):
    """Застосувати правила до КОЖНОГО факту, чий kind (і літеральний value)
    збігається; повернути (правила, [(файл/ім'я, порада, чому), …])."""
    rules = knowledge_rules(text)
    inferred: list[tuple[str, str, str]] = []
    for rule in rules:
        for kind, name, value, _source in facts:
            if kind != rule["kind"]:
                continue
            if rule["value"] is not None and value != rule["value"]:
                continue
            target = _resolve_binding(rule["file"], name, value)
            why = _resolve_binding(rule["why"], name, value)
            inferred.append((target, rule["advice"], why))
    return rules, inferred


# --- КАТАЛОГ наявних функцій драбини (для агента ПЕРЕД писанням) -------------- #
# Мета власника: агент, перш ніж писати програму, має ВЗАГАЛІ бачити, ЯКІ в нас
# є функції d1–d11 — і брати наявну/влучнішу, а не винаходити наново.
#
# Джерело істини — discover_domain_function_candidates (ІМПОРТ, не копія):
# load_domain_tables + aliases + classify. Це ЧИТАННЯ поверхонь (каталог), а не
# рушій і не реєстр; той самий механізм уже вживають search-domain-function.py
# і сам охоронець — тож другого сканера драбин не заводимо.

_HUMAN_COLS = ("ук", "укр", "san", "en", "LISP")


def _catalog_entries(root: Path):
    """(domain, row, aliases, object_kind, callable) на кожну поверхню драбини."""
    discover = _load_discover()
    entries = []
    for domain, rows in discover.load_domain_tables(root).items():
        for row in rows:
            kind, callable_ = discover.classify(row)
            entries.append((domain, row, discover.aliases(row), kind, callable_))
    return entries


def _entry_names(entry) -> dict:
    """Людиночитані колонки поверхні (порожні/цитовані пропускаємо)."""
    _domain, row, _aliases, _kind, _callable = entry
    out: dict[str, str] = {}
    for col in _HUMAN_COLS:
        value = row[col]
        if row.get(col + "_quoted") or value in {"", "()", "<compound>"}:
            continue
        out[col] = value
    return out


def _entry_line(entry) -> str:
    """Один рядок каталогу: укр-ім'я, координата, домен, призначення(en), роль."""
    domain, row, _aliases, kind, _callable = entry
    names = _entry_names(entry)
    ukr = names.get("укр") or names.get("ук") or "?"
    en = names.get("en", "")
    lisp = names.get("LISP", "")
    parts = [f"{ukr}  [D{domain}:{row['bits']}]  домен D{domain}"]
    purpose = en or lisp
    if purpose:
        parts.append(f"призначення(en): {purpose}")
    if lisp and lisp != purpose:
        parts.append(f"LISP={lisp}")
    parts.append(f"роль: {kind}")
    return "  ".join(parts)


def catalog_overview(root: Path) -> int:
    """Огляд: скільки функцій у кожному домені + кілька прикладів."""
    entries = _catalog_entries(root)
    by_domain: dict[int, list] = {}
    for entry in entries:
        by_domain.setdefault(entry[0], []).append(entry)
    callable_n = sum(1 for entry in entries if entry[4])
    print("КАТАЛОГ ФУНКЦІЙ ДРАБИНИ D1–D11 (що вже Є — бери наявне, не вигадуй)")
    print("джерело: discover_domain_function_candidates (lib/domains/d1..d11.lisp)")
    print(f"усього поверхонь: {len(entries)}; викличних кандидатів: {callable_n}")
    print()
    for d in sorted(by_domain):
        rows = by_domain[d]
        n_call = sum(1 for entry in rows if entry[4])
        examples = [(names.get("укр") or names.get("ук") or "?")
                    for names in (_entry_names(entry) for entry in rows[:5])]
        print(f"  D{d}: {len(rows)} поверхонь ({n_call} викличних) — напр.: {', '.join(examples)}")
    print()
    print("ПОШУК за назвою/призначенням:  --catalog <запит>")
    print("ПІДКАЗКА влучніших:           --better \"обробити список\"")
    return 0


def catalog_search(root: Path, query: str) -> int:
    """Пошук за підрядком (укр./en/призначення) — відсортований список наявного."""
    entries = _catalog_entries(root)
    q = query.strip().lower()
    hits = []
    for entry in entries:
        hay = [value.lower() for value in _entry_names(entry).values()]
        hay.append(entry[3].lower())
        if any(q in item for item in hay):
            hits.append(entry)
    hits.sort(key=lambda entry: (entry[0], entry[1]["bits"]))
    if not hits:
        print(f"НЕ ЗНАЙДЕНО у каталозі D1–D11: {query}")
        print("Якщо операції справді немає — визнач її й познач `; D11-пропозиція: <причина>` перед визначенням.")
        return 0
    print(f"КАТАЛОГ D1–D11 за запитом «{query}» — знайдено {len(hits)}:")
    for entry in hits[:60]:
        print("  " + _entry_line(entry))
    if len(hits) > 60:
        print(f"  … ще {len(hits) - 60}")
    return 0


# --- Підказка ВЛУЧНІШИХ функцій -------------------------------------------- #
# Для типової задачі показати наявні ВИЩІ функції драбини (map/filter/reduce/
# apply/compose…), а не ручну рекурсію чи цикл. Джерело — наявні поверхні
# драбини (шукаємо за призначенням, не вигадуємо імена).
BETTER_RULES = (
    (("список", "перебрати", "кожен", "обробити", "елемент", "перетворити"),
     ("map", "filter", "reduce", "scan"), "замість ручної рекурсії/циклу по списку"),
    (("відібрати", "фільтр", "фільтрувати", "лишити", "відсіяти"),
     ("filter",), "замість ручного відбору з умовою"),
    (("порахувати", "підсумувати", "сума", "звести", "згорнути", "накопичити", "добуток"),
     ("reduce", "scan"), "замість ручного накопичення в циклі"),
    (("застосувати функцію", "викликати функцію", "apply", "розкласти аргументи"),
     ("apply",), "замість ручного розкладання аргументів"),
    (("скласти", "композиція", "скомпонувати", "об'єднати функції"),
     ("compose",), "замість вкладеного виклику"),
    (("рекурсія", "рекурсивно", "цикл", "вручну"),
     ("map", "filter", "reduce", "scan", "apply", "compose"),
     "вища функція дешевша за ручну рекурсію"),
)
DEFAULT_BETTER = ("map", "filter", "reduce", "scan", "apply", "compose")


def _by_en(root: Path) -> dict:
    """Індекс en-ім'я → список поверхонь (одне ім'я може стояти в кількох доменах)."""
    index: dict[str, list] = {}
    for entry in _catalog_entries(root):
        en = _entry_names(entry).get("en")
        if en:
            index.setdefault(en.lower(), []).append(entry)
    return index


def better_advice(root: Path, task: str) -> int:
    """Показати наявні влучніші (вищі) функції драбини для типової задачі."""
    index = _by_en(root)
    tl = task.lower()
    matched: list[str] = []
    notes: list[str] = []
    for keywords, names, note in BETTER_RULES:
        if any(keyword in tl for keyword in keywords):
            matched.extend(names)
            notes.append(note)
    if not matched:
        matched = list(DEFAULT_BETTER)
        notes = ["вищі функції драбини дешевші за ручну рекурсію/цикл"]
    ordered = list(dict.fromkeys(matched))
    print(f"ПІДКАЗКА ВЛУЧНІШИХ для задачі «{task}» (наявні функції драбини — не вигадуй):")
    shown = 0
    for name in ordered:
        for entry in index.get(name, [])[:1]:
            print("  " + _entry_line(entry))
            shown += 1
    if notes:
        print("  → " + "; ".join(dict.fromkeys(notes)))
    print("  глянь ширше: --catalog <запит>")
    return 0


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
    ap.add_argument("--lessons", action="store_true", help="показати ЦІННІ ЗНАННЯ: уроки історії з довідника")
    ap.add_argument("--knowledge", action="store_true", help="показати БАЗУ ЗНАНЬ охоронця (CLIPS-факти й поради)")
    ap.add_argument("--catalog", nargs="?", const="", default=None, metavar="ЗАПИТ",
                    help="КАТАЛОГ наявних функцій d1–d11: без запиту — огляд, із запитом — пошук")
    ap.add_argument("--better", metavar="ЗАДАЧА",
                    help="підказка влучніших наявних функцій (map/reduce/filter…) для задачі")
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

    # КАТАЛОГ і підказка влучніших — ЧИТАННЯ драбини ДО писання програми.
    # Повертаються раніше за project_sites: тут git-індекс не потрібен.
    if args.catalog is not None:
        return catalog_overview(ROOT) if args.catalog == "" else catalog_search(ROOT, args.catalog)
    if args.better:
        return better_advice(ROOT, args.better)

    project_sites = project_definition_sites(ROOT)

    if args.self_test:
        ok = len(ladder) >= MINIMUM_RATIFIED_SURFACES
        print(f"GUARD-DOMAIN-REUSE self-test: {'OK' if ok else 'FAIL'} (поверхонь у драбинах: {len(ladder)}, джерело: discover_domain_function_candidates)")
        # Дозвіл на інший закон стосується рівно одного наступного DEFINE.
        marked = definitions_with_bodies(
            "; НАВМИСНО: інший закон — окрема семантика\n"
            "(визначити перша (функція (х) х))\n"
            "(визначити друга (функція (х) х))\n"
        )
        empty = definitions_with_bodies(
            "; НАВМИСНО: інший закон —\n"
            "(визначити перша (функція (х) х))\n"
            "(визначити друга (функція (х) х))\n"
        )
        intent_ok = (
            [row[3] for row in marked] == [True, False]
            and [row[3] for row in empty] == [False, False]
        )
        print(f"GUARD-DOMAIN-REUSE self-test: маркер іншого закону {'OK' if intent_ok else 'FAIL'}")
        # Пропозиція D11 мусить мати причину і стосуватися одного DEFINE.
        d11_marked = definitions_with_bodies(
            "; D11-пропозиція: нова операція\n"
            "(визначити перша (функція (х) х))\n"
            "(визначити друга (функція (х) х))\n"
        )
        d11_empty = definitions_with_bodies(
            "; D11-пропозиція:\n"
            "(визначити перша (функція (х) х))\n"
            "(визначити друга (функція (х) х))\n"
        )
        d11_ok = (
            [row[2] for row in d11_marked] == [True, False]
            and [row[2] for row in d11_empty] == [False, False]
        )
        print(f"GUARD-DOMAIN-REUSE self-test: маркер D11 {'OK' if d11_ok else 'FAIL'}")
        # Недоступний Git index не може означати «немає змінених файлів».
        from contextlib import redirect_stderr
        from io import StringIO
        from unittest.mock import patch
        with patch.object(
            subprocess, "run",
            return_value=subprocess.CompletedProcess(
                ["git", "diff"], 128, "", "fatal: simulated index failure"
            ),
        ), redirect_stderr(StringIO()):
            try:
                changed_files(argparse.Namespace(file=None, paths_from=None, staged=True))
            except SystemExit as exc:
                staged_ok = exc.code == 2
            else:
                staged_ok = False
        print(f"GUARD-DOMAIN-REUSE self-test: git staged fail-closed {'OK' if staged_ok else 'FAIL'}")
        # Як і ls-files, staged diff читає NUL, а не розрізає назви за рядками.
        # Злам цього контракту приховує DEFINE в незвично названих Lisp-файлах.
        staged_paths = ["lib/назва із пробілами.lisp", "lib/другий" + chr(10) + "рядок.lisp"]
        with patch.object(
            subprocess, "run",
            return_value=subprocess.CompletedProcess(
                ["git", "diff"], 0, chr(0).join(staged_paths) + chr(0), ""
            ),
        ) as staged_mock:
            staged_paths_ok = (
                changed_files(argparse.Namespace(file=None, paths_from=None, staged=True)) == staged_paths
                and "-z" in staged_mock.call_args.args[0]
            )
        print(f"GUARD-DOMAIN-REUSE self-test: git staged NUL-шляхи {'OK' if staged_paths_ok else 'FAIL'}")
        # Недоступний індекс проєкту не повинен приховувати дубль DEFINE.
        with patch.object(
            subprocess, "run",
            return_value=subprocess.CompletedProcess(
                ["git", "ls-files"], 128, "", "fatal: simulated repository failure"
            ),
        ), redirect_stderr(StringIO()):
            try:
                project_definition_sites(ROOT)
            except SystemExit as exc:
                project_sites_ok = exc.code == 2
            else:
                project_sites_ok = False
        print(f"GUARD-DOMAIN-REUSE self-test: git ls-files fail-closed {'OK' if project_sites_ok else 'FAIL'}")
        # Git -z лишає шлях із пробілами єдиним іменем, без втрати визначення.
        sample_file = ROOT / "lib" / "назва із пробілами.lisp"
        with patch.object(
            subprocess, "run",
            return_value=subprocess.CompletedProcess(
                ["git", "ls-files"], 0, "lib/назва із пробілами.lisp\0", ""
            ),
        ), patch.object(
            Path, "is_file", lambda path: path == sample_file
        ), patch.object(
            Path, "read_text", return_value="(визначити перевірка (функція (х) х))"
        ):
            paths_ok = project_definition_sites(ROOT).get("перевірка") == {
                "lib/назва із пробілами.lisp"
            }
        print(f"GUARD-DOMAIN-REUSE self-test: шлях з пробілами {'OK' if paths_ok else 'FAIL'}")
        # Перевіряємо і ВЛАСНУ активацію: невиконуваний гачок = мертвий охоронець.
        hok, hmsg = hook_installed()
        print(f"GUARD-DOMAIN-REUSE self-test: гачок {'OK' if hok else 'НЕ УВІМКНЕНО (попередження)'} — {hmsg}")
        # Стан гачка — ПОПЕРЕДЖЕННЯ, не падіння: свіжий клон законно не має
        # ввімкненого гачка, доки не виконано scripts/install-hooks.sh.
        return 0 if ok and intent_ok and d11_ok and staged_ok and staged_paths_ok and project_sites_ok and paths_ok else 1

    if args.lessons:
        # Знання живуть у САМОМУ охоронці: агент, який ним користується,
        # дістає уроки однією командою, а не шукає окремий документ.
        doc = ROOT / "docs" / "guard-history-reference.uk.md"
        if not doc.is_file():
            print("GUARD-DOMAIN-REUSE --lessons: немає docs/guard-history-reference.uk.md", file=sys.stderr)
            return 2
        print(doc.read_text(encoding="utf-8"))
        return 0

    if args.knowledge:
        # ЗНАННЯ охоронця тепер у ФОРМІ CLIPS (knowledge/guard-knowledge.clp):
        # факти — ЩО Є (гарячий файл, шар, клас помилки), правила — ЩО РОБИТИ.
        # Це ЧИТАННЯ (проста вибірка фактів), а не повний рушій правил: Rust не тягнемо.
        kpath = ROOT / "knowledge" / "guard-knowledge.clp"
        if not kpath.is_file():
            print("GUARD-DOMAIN-REUSE --knowledge: немає knowledge/guard-knowledge.clp", file=sys.stderr)
            return 2
        ktext = kpath.read_text(encoding="utf-8", errors="replace")
        facts = knowledge_facts(ktext)
        if facts:
            print("БАЗА ЗНАНЬ ОХОРОНЦЯ (knowledge/guard-knowledge.clp)")
            print("ФАКТ → ПОРАДА:")
            for kind, name, value, source in facts:
                print(f"  [{kind}] {name} ({value}) → {knowledge_advice(kind)}  (джерело: {source})")
        else:
            # Стійкість: щось не збіглось — не падаємо, показуємо сирий вміст.
            print("УВАГА: не вдалося розібрати факти — сирий вміст knowledge/guard-knowledge.clp:")
            print(ktext)
        rules = len(re.findall(r"\(defrule\b", ktext))
        # Міні-(run): застосовуємо правила (defrule …) до фактів і ВИВОДИМО поради.
        # Досі --knowledge лише ПОКАЗУВАВ факти; тепер охоронець справді ВИВОДИТЬ
        # guard-advice, тож доданий факт або правило ДІЄ, а не лежить декларацією.
        _rules, inferred = knowledge_inference(ktext, facts)
        print()
        print("ВИВЕДЕНІ ПОРАДИ (run):")
        if inferred:
            for target, advice, why in inferred:
                print(f"  {target} → {advice}  (чому: {why})")
        else:
            print("  (жодне правило не вивело поради)")
        print(f"БАЗА ЗНАНЬ: {len(facts)} фактів, {rules} правил, {len(inferred)} виведених порад")
        return 0

    if not (args.staged or args.paths_from or args.file):
        ap.error("потрібен --staged / --paths-from / --file")

    # Урок №1 з docs/guard-history-reference.uk.md стає перевіркою: гарячі файли
    # (напр. lib/core4.lisp) правлять МАЛЕНЬКИМИ кроками. Це ПОПЕРЕДЖЕННЯ —
    # воно не змінює код виходу й друкується і для OK, і для BLOCKED.
    hot_warning(changed_files(args))

    blocked: list[tuple[str, str, str]] = []
    intentional_shadows: list[tuple[str, str]] = []
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
        if not args.staged and not path.is_file():
            continue
        if args.staged:
            try:
                staged = subprocess.run(
                    ["git", "show", f":{rel}"], cwd=ROOT,
                    capture_output=True, text=True, check=False,
                )
            except (OSError, UnicodeError) as exc:
                print(f"GUARD-DOMAIN-REUSE: НЕ ПЕРЕВІРЕНО — Git index {rel}: {exc}", file=sys.stderr)
                return 2
            if staged.returncode != 0:
                print(f"GUARD-DOMAIN-REUSE: НЕ ПЕРЕВІРЕНО — неможливо прочитати Git index {rel}: {staged.stderr.strip()}", file=sys.stderr)
                return 2
            text = staged.stdout
        else:
            text = path.read_text(encoding="utf-8")
        checked += 1
        # Рахуємо входження, а не лише імена: у --base друге DEFINE
        # з тією самою назвою є новим, навіть якщо перше вже існувало.
        known_counts: Counter[str] = Counter()
        if args.base:
            try:
                old_text = subprocess.run(
                    ["git", "show", f"{args.base}:{rel}"], cwd=ROOT,
                    capture_output=True, text=True, check=False).stdout
            except Exception:
                old_text = ""
            known_counts.update(n for n, *_ in definitions_with_bodies(old_text))
        seen_counts: Counter[str] = Counter()
        active_text = _mask_quotes(text)
        usage[rel] = sum(
            1 for head in re.findall(r"\(\s*([^\s()]{2,})", active_text)
            if head in ladder and head not in STRUCTURAL
        )
        for name, body, marked, intent in definitions_with_bodies(text):
            seen_counts[name] += 1
            if args.base and seen_counts[name] <= known_counts[name]:
                continue  # наявне входження; перевіряємо лише приріст
            new_defs[rel] = new_defs.get(rel, 0) + 1
            if seen_counts[name] > 1:
                blocked.append((rel, name, REASON_DUP_IN_FILE))
                continue
            if name in ladder:
                if intent:
                    # Клас А з маркером: закон НАВМИСНЕ визначає однойменну
                    # функцію з ІНШИМ тілом (не дубль) — не блокуємо.
                    intentional_shadows.append((rel, name))
                    continue
                blocked.append((rel, name, REASON_SHADOW_LADDER))
                continue
            if duplicates_project_definition(project_sites, name, rel):
                blocked.append((rel, name, REASON_SHADOW_PROJECT))
                continue
            if not marked and not _calls_ladder(body, ladder):
                # Нове ім'я без жодного виклику поверхні драбини і без маркера —
                # це або перевинахід наявної операції, або неусвідомлена нова.
                blocked.append((rel, name, REASON_FRESH_NAME))
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
    if intentional_shadows:
        print(f"НАВМИСНИЙ ІНШИЙ ЗАКОН (клас А, позначено маркером): {len(intentional_shadows)}")
        for rel, name in intentional_shadows:
            print(f"     {rel}: «{name}» — позначено `; НАВМИСНО: інший закон — <причина>`")
    # Заблокований зріз не має змінювати реєстр кандидатів D11.
    if args.register and candidates and not blocked:
        n = register_candidates(candidates)
        print(f"ЗАРЕЄСТРОВАНО в D11: {n} нових кандидатів → реєстр кандидатів D11 "
              f"(наявні не дублювались; статус кандидат, не ратифіковано)")
    elif args.register and candidates and blocked:
        print("НЕ ЗАРЕЄСТРОВАНО в D11: є BLOCKED; спершу виправ усі порушення.")

    if args.advise and blocked:
        # Точна класифікація за кодом причини, а не за підрядком у тексті.
        shadow = [(r, n) for r, n, w in blocked if w == REASON_SHADOW_LADDER]
        project = [(r, n) for r, n, w in blocked if w == REASON_SHADOW_PROJECT]
        fresh = [(r, n) for r, n, w in blocked if w == REASON_FRESH_NAME]
        dupfile = [(r, n) for r, n, w in blocked if w == REASON_DUP_IN_FILE]
        print(f"\nПОРАДИ (--advise): {len(blocked)} виправлень у {len({r for r, _, _ in blocked})} файлах")
        if shadow:
            print(f"\n  А) ЗАТІНЮЄ ДРАБИНУ ({len(shadow)}) — ужий наявну поверхню, не перевизначай:")
            for r, n in shadow[:12]:
                when = f"  [уведено {introduced_at(r, n)}]" if args.when else ""
                print(f"     {r}: «{n}» уже є поверхнею драбини — прибери своє визначення й клич драбину{when}")
                print(f"        де саме: python3 scripts/search-domain-function.py {n}")
            if len(shadow) > 12:
                print(f"     … ще {len(shadow) - 12}")
            print("     навмисний інший закон? познач `; НАВМИСНО: інший закон — <причина>` перед визначенням")
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
        if dupfile:
            print(f"\n  Г) ПОВТОРНЕ ВИЗНАЧЕННЯ ({len(dupfile)}) — лиши одне визначення на файл:")
            for r, n in dupfile[:12]:
                print(f"     {r}: «{n}» визначено двічі в одному файлі — прибери повтор")
            if len(dupfile) > 12:
                print(f"     … ще {len(dupfile) - 12}")
        print("\n  підказка: для типової задачі глянь наявні ВИЩІ функції (map/reduce/filter…) — ")
        print("     python3 scripts/guard-domain-function-reuse.py --better \"обробити список\"")
        print("     весь каталог d1–d11: python3 scripts/guard-domain-function-reuse.py --catalog")
        print()
    if blocked:
        for rel, name, why in blocked:
            print(f"BLOCKED: {rel}: «{name}» — {why}. Вжий наявну поверхню драбини, або познач "
                  f"`; D11-пропозиція: <причина>` перед визначенням, якщо операції справді немає.")
        print(f"GUARD-DOMAIN-REUSE: BLOCKED ({len(blocked)} порушень серед {checked} файлів, навмисних: {len(intentional_shadows)})")
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
    print(f"GUARD-DOMAIN-REUSE: OK ({checked} файлів, {len(candidates)} кандидатів D11, навмисних: {len(intentional_shadows)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
