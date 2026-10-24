#!/usr/bin/env python3
"""Гра «Драбина»: окремі щаблі мовних законів і експериментів кодеку.

    python3 scripts/domain-game.py
    python3 scripts/domain-game.py --brief
    python3 scripts/domain-game.py --track codec
    python3 scripts/domain-game.py --track codec --verify
    python3 scripts/domain-game.py --track d11-codec --verify
    python3 scripts/domain-game.py --track memory --domain D3 --list
    python3 scripts/domain-game.py --track d13-candidates --brief
    python3 scripts/domain-game.py --track memory --domain ALL --count 20 --seed 42

Мовні файли — не тотожні доведеним законам. Codec-щабель зараховується
лише після успішного нативного Zig test; Python не перевіряє семантику SENS.
"""
from __future__ import annotations

import argparse
import random
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DENSE = Path("research/zig-codecs/d12_dense_experiment.zig")
D13_DENSE = Path("research/zig-codecs/d13_dense_experiment.zig")
D13_RESEARCH = Path("research/d13/function-candidates.lisp")

LEVELS = [
    ("D1", "основа: тотожність, атом, хибне/істинне"),
    ("D2", "структура й керування: межі, розділювачі, ліниві гілки"),
    ("D3", "списки: перше, решта, сполучити"),
    ("D4", "селектори: CAAR, CADR, CDAR, CDDR"),
    ("D5", "bootstrap: LAMBDA, DEFINE, EVAL та похідні"),
    ("D6", "селектори й похідні"),
    ("D7", "клавіатура/проєкція"),
    ("D8", "рядки, масиви, властивості"),
    ("D9", "сховище, файли"),
    ("D10", "бібліотеки й сімейства"),
    ("D11", "НОВІ сімейства (селекторні похідні, кандидати)"),
    ("D12", "початок математики: малі точні числа"),
]

# Опис квестів. Назви повинні точно збігатися з нативними Zig test.
# None = наступний квест, якому ще бракує нативного тесту/реалізації.
CODEC_LEVELS = [
    ("C1", "Межі й порядок 12-бітних слів", (
        "D12 dense fixed vector preserves boundaries and leading zeros",
        "D12 dense exact byte ordering and run lengths",
    )),
    ("C2", "Усі 4096 значень із доповняльним партнером", (
        "D12 dense exhaustive 4096 raw words with complementary partner",
    )),
    ("C3", "Відмова без часткового запису", (
        "D12 dense rejects invalid payload without modifying output",
    )),
    ("C4", "Реальні довгі й непарні цикли encode/decode/reencode", (
        "D12 dense long and odd runs preserve bytes on reencode",
    )),
    ("C5", "Явний кадр: версія, домен, довжина, цілісність", None),
]

# D13 тут лише дослідний 13-бітний carrier, а не числовий чи викличний домен.
D13_CODEC_LEVELS = [
    ("R1", "Повний перебір 8192 13-бітних слів", (
        "D13 research: all 8192 possible raw words roundtrip",
    )),
    ("R2", "Точний порядок бітів і довжини", (
        "D13 research: exact order, leading zeros and useful lengths",
    )),
    ("R3", "Довгі цикли та повторне кодування", (
        "D13 research: long streams are bit- and byte-exact",
    )),
    ("R4", "Відмова без зміни буфера", (
        "D13 research: malformed input fails without touching output",
    )),
    ("R5", "Сім неканонічних хвостів і повний байт", (
        "D13 research: all seven padding residues fail closed; aligned eight-word run succeeds",
    )),
]

# Дослідний codec конкурс лише для явного 512-селекторного підпотоку D11.
D11_CODEC = Path("research/zig-codecs/d11_selector_contest.zig")
D11_CODEC_LEVELS = [
    ("S1", "Точне кодування кожного окремого селектора", (
        "D11 Драбина: усі 512 селекторів мають точний roundtrip",
    )),
    ("S2", "Golden-вектор порядку бітів на межі байта", (
        "D11 Драбина: selector9 зберігає порядок бітів на межі байта",
    )),
    ("S3", "Один канонічний потік із усіх 512 селекторів", (
        "D11 Драбина: один потік selector9 переносить усі 512 слів",
    )),
    ("S4", "Звірка всіх кодів та імен із таблицею D11", (
        "D11 Драбина: запам'ятати всі 512 координат і Lisp-імен таблиці",
    )),
    ("S5", "Однаковий облік payload для 9/11/16 бітів", (
        "D11 Драбина: 9, 11 і 16 біт — чесний облік байтів",
    )),
    ("S6", "Повний 512-слівний raw16 базис без обрізання", (
        "D11 Драбина: повний raw16 раунд 512 селекторів у буфері конкурсу",
    )),
    ("S7", "Відхилення чужих координат і неканонічного хвоста", (
        "D11 Драбина: чужі координати, обрізання та хвіст не змінюють вихід",
    )),
]

def tracked(pattern: str) -> list[str]:
    out = subprocess.run(
        ["git", "-c", "core.quotepath=false", "ls-files", pattern],
        cwd=ROOT, capture_output=True, text=True,
    ).stdout
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def codec_coverage() -> tuple[int, int, int]:
    """Стан кодеку: скільки lib/*.lisp мають фізичну пару .sens (T5M).

    Це «гра для кодеку»: кожна нова пара — це ще один файл, який кодек
    справді переносить. Три числа: з парою, без пари, усього.
    """
    lisp = [p for p in tracked("lib/*.lisp")]
    with_pair = [p for p in lisp if (ROOT / (p[:-5] + ".sens")).is_file()]
    return len(with_pair), len(lisp) - len(with_pair), len(lisp)


def progress() -> Counter:
    """Кількість ФАЙЛІВ за префіксом домену, не число доведених законів."""
    c: Counter = Counter()
    for p in tracked("tests/semantic/*.lisp"):
        name = Path(p).stem.lower()
        m = re.match(r"d(\d+)", name)
        if m:
            c[f"D{m.group(1)}"] += 1
    return c


def visible_levels(counts: Counter) -> list[tuple[str, str]]:
    """Показати всі домени з файлами, не надаючи їм нової ратифікації."""
    known = {domain for domain, _ in LEVELS}
    extra = sorted(
        (domain for domain in counts if domain not in known),
        key=lambda domain: int(domain[1:]),
    )
    descriptions = {
        "D24": "точна математика: числові закони та негативні свідки",
    }
    return LEVELS + [
        (domain, descriptions.get(domain, "виявлені файли; звірити доменний контракт"))
        for domain in extra
    ]


def semantic_game(brief: bool) -> int:
    prog = progress()
    total = sum(prog.values())
    levels = visible_levels(prog)
    if brief:
        print(f"ДРАБИНА: рівнів {len(levels)}, файлів Lisp {total}, "
              f"найбільше {max(prog, key=prog.get) if prog else '—'}")
        return 0

    print("═══ ГРА «ДРАБИНА» / МОВА ═══")
    print("Лічильник показує файли, не результат виконання законів.\n")
    print(f"{'рівень':<6} {'файлів':>7}  опис")
    for dom, desc in levels:
        n = prog.get(dom, 0)
        bar = "█" * min(n // 5, 20)
        print(f"{dom:<6} {n:>7}  {bar} {desc}")
    print(f"\nУсього файлів Lisp із доменним префіксом: {total}")
    wp, wo, tot = codec_coverage()
    pct = (100 * wp // tot) if tot else 0
    bar = "█" * (pct // 5) + "·" * (20 - pct // 5)
    print(f"\nКОДЕК (фізичні пари .lisp↔.sens): {wp}/{tot} ({pct}%)")
    print(f"  [{bar}]  без пари: {wo}")
    ranked = sorted(levels, key=lambda kv: prog.get(kv[0], 0))
    gaps = ranked[:3]
    print("\nНАСТУПНИЙ КВЕСТ (найменше файлів):")
    for dom, desc in gaps:
        print(f"  ★ {dom} — {prog.get(dom, 0)} файлів. {desc}")
    dom, desc = gaps[0]
    print(f"\n  Бери {dom}. Кроки:")
    print("    1) python3 scripts/new-program.py <назва>")
    print("    2) напиши закон ліспом: закон → D1:1, мутант → D1:0")
    print("    3) охоронець перевірить → кодек перетворить у SENS")
    print(f"\n  Обери щось із теми «{desc}» і додай наступну пару.")
    print("\nЕКСПЕРИМЕНТ КОДЕКУ — підмножина D2 без крапки (11):")
    print("    ★ перевірка: 243/243 груп, пошкоджені байти, неканонічні хвости")
    print("    ★ D2:11 (крапка) за межами цього досліду: повний D2 має 4 слова")
    print("    ★ виграш: 20 D2 → 4 байти проти 5 сирих")
    print("    ★ чесна межа: у змішаному CAAR 10 серій → 10 байтів без карти позицій")
    print("    перевірка: zig test research/zig-codecs/d2_ladder_game.zig")
    return 0


def codec_game(
    brief: bool,
    verify: bool,
    experimental_d13: bool = False,
    experimental_d11: bool = False,
) -> int:
    if experimental_d13:
        selected, levels, track, heading = D13_DENSE, D13_CODEC_LEVELS, "D13", "D13 RESEARCH"
    elif experimental_d11:
        selected, levels, track, heading = D11_CODEC, D11_CODEC_LEVELS, "D11", "D11 SELECTOR CODEC"
    else:
        selected, levels, track, heading = DENSE, CODEC_LEVELS, "D12", "DENSE-D12"
    source_path = ROOT / selected
    source = source_path.read_text(encoding="utf-8") if source_path.is_file() else ""
    declared = set(re.findall(r'^test "([^"]+)"', source, flags=re.MULTILINE))
    present = {
        code: tests is not None and all(name in declared for name in tests)
        for code, _, tests in levels
    }
    tested = False
    return_code = 0
    zig_version = "NOT_RUN"
    if verify:
        if not source:
            print(f"НЕМАЄ ФАЙЛУ: {selected}", file=sys.stderr)
            return 2
        try:
            version = subprocess.run(
                ["zig", "version"], cwd=ROOT, capture_output=True, text=True,
            )
            zig_version = version.stdout.strip() or "UNKNOWN"
            result = subprocess.run(
                ["zig", "test", "-lc", str(selected)],
                cwd=ROOT, capture_output=True, text=True,
            )
        except FileNotFoundError:
            print("Zig недоступний: щаблі не зараховано.", file=sys.stderr)
            return 2
        # Відсутній запуск тестів не дає очок навіть при exit=0.
        output = result.stdout + result.stderr
        executed = re.search(r"All\s+[1-9]\d*\s+tests?\s+passed", output) is not None
        tested = result.returncode == 0 and executed and any(present.values())
        return_code = 0 if tested else 1
        if not tested:
            print(output, file=sys.stderr)
            print("Немає підтвердженого ненульового PASS Zig; очки не нараховано.", file=sys.stderr)
    score = sum(1 for code, _, _ in levels if tested and present[code])
    proof = "PASS" if tested else ("FAIL" if verify else "NOT_RUN")
    if brief:
        print(f"ДРАБИНА/CODEC-{track}: verified={score}/{len(levels)} "
              f"native={proof} semantics=NOT_TESTED")
        return return_code

    print("═══ ГРА «ДРАБИНА» / " + heading + " ═══")
    if experimental_d11:
        print("Явний селекторний підпотік D11: локальний 9-бітний індекс проти щільних 11 і raw16.")
        print("Не загальний codec D1–24+ і не самодостатній кадр.")
    else:
        print("Фізичний " + ("13" if experimental_d13 else "12") + "-бітний payload; не самодостатній кадр.")
    if experimental_d13:
        print("D13 НЕ ратифіковано як математичний чи викличний домен.")
    print("Семантика чисел і SENS: NOT_TESTED.\n")
    for code, desc, tests in levels:
        status = "ДОВЕДЕНО" if tested and present[code] else (
            "Є ТЕСТ / НЕ ЗАПУЩЕНО" if present[code] else "ЩЕ НЕМАЄ"
        )
        print(f"  {code}  [{status}] {desc}")
    print(f"\nНагорода: {score}/{len(levels)} доведених щаблів; Zig={proof}")
    if verify:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,
        ).stdout.strip()
        blob = subprocess.run(
            ["git", "hash-object", str(selected)], cwd=ROOT, capture_output=True, text=True,
        ).stdout.strip()
        print(f"Свідчення запуску: commit={sha or 'UNKNOWN'} blob={blob or 'UNKNOWN'} zig={zig_version}")
        print(f"Команда: zig test -lc {selected}")
    next_track = "d11-codec" if experimental_d11 else "d13" if experimental_d13 else "codec"
    if not tested:
        print("\nНАСТУПНИЙ ХІД: "
              f"python3 scripts/domain-game.py --track {next_track} --verify")
    else:
        missing = next((code for code, _, _ in levels if not present[code]), None)
        if missing:
            print(f"\nНАСТУПНИЙ КВЕСТ: {missing} — додай точний Zig test у {selected}.")
        else:
            print("\nУсі описані щаблі пройшли нативну перевірку.")
    return return_code


def ratified_domain_surfaces() -> set[str]:
    """Exact names from current ratified domains; D7 is keyboard/data, not callable code."""
    names: set[str] = set()
    for width in range(1, 12):
        if width == 7:
            continue
        path = ROOT / "lib" / "domains" / f"d{width}.lisp"
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if re.match(r"^\s*\([01]{1,11}\s+", line) is None:
                continue
            for field in ("ук", "укр", "en", "LISP"):
                found = re.search(r"\(" + re.escape(field) + r"\s+([^()\s]+)\)", line)
                if found is not None and found.group(1) != "()":
                    names.add(found.group(1).casefold())
    return names


def d13_candidates(source: str) -> list[tuple[str, str]]:
    """Рахувати гіпотези D13, не присвоюючи координат чи викличності."""
    for required in (
        "(schema . d13-experimental-function-candidates-1)",
        "(status . experimental-unratified)",
        "(domain . D13)",
        "(coordinates . unassigned)",
        "(callable . no)",
        "(semantic-proof . not-run)",
    ):
        if source.count(required) != 1:
            raise ValueError(f"D13: відсутнє або повторене поле {required}")
    blocks = re.split(r"(?m)^[ \t]*\(candidate[ \t]+", source)[1:]
    if not blocks:
        raise ValueError("D13: немає жодної дослідницької функції")
    entries: list[tuple[str, str]] = []
    seen_ukr: set[str] = set()
    seen_en: set[str] = set()
    ratified_surfaces = ratified_domain_surfaces()
    for block in blocks:
        match = re.match(r"\(укр\s+([^\s()]+)\)\s+\(en\s+([^\s()]+)\)", block)
        if match is None:
            raise ValueError("D13: кандидат не має пари укр/en")
        ukr, en = match.groups()
        fields = {}
        for field, label in (
            ("(signature .", "signature"),
            ("(law .", "law"),
            ("(counterexample .", "counterexample"),
        ):
            if block.count(field) != 1:
                raise ValueError(f"D13: {ukr} не має єдиного поля {field}")
            found = re.search(re.escape(field) + r'\s*"([^"]*)"\)', block)
            if found is None or not found.group(1).strip():
                raise ValueError(f"D13: {ukr} має порожнє або некоректне поле {label}")
            fields[label] = found.group(1).strip()
        signature = fields["signature"]
        if "Z*" in signature or "Q*" in signature:
            raise ValueError(f"D13: {ukr} має неоднозначне скорочення Z*/Q*; задайте точну область")
        if not any(token in signature for token in ("ℤ", "ℚ", "ℕ₀")):
            raise ValueError(f"D13: {ukr} не задає точну числову область")
        for surface in (ukr, en):
            if surface.casefold() in ratified_surfaces:
                raise ValueError(
                    f"D13: {ukr}/{en} дублює чинну поверхню D1–D11: {surface}"
                )
        if ukr.casefold() in seen_ukr or en.casefold() in seen_en:
            raise ValueError(f"D13: дубльована назва {ukr}/{en}")
        seen_ukr.add(ukr.casefold())
        seen_en.add(en.casefold())
        entries.append((ukr, en))
    return entries


def d13_game(brief: bool) -> int:
    """Дослідницька дошка D13: кандидати ≠ призначені коди ≠ доказ."""
    try:
        source = (ROOT / D13_RESEARCH).read_text(encoding="utf-8")
        entries = d13_candidates(source)
    except (OSError, ValueError) as exc:
        print(f"ДРАБИНА/D13: помилка каталогу: {exc}", file=sys.stderr)
        return 2
    print(f"ДРАБИНА/D13: кандидатів={len(entries)} координат=0 "
          "викличних=0 семантика=НЕ_ДОВЕДЕНО")
    if not brief:
        print("Експериментальні сімейства над точними D12+; "
              "це не ратифікація і не таблиця кодів.")
        for ukr, en in entries:
            print(f"  ★ {ukr} / {en}")
        print("Закони та контрприклади: research/d13/function-candidates.lisp")
    return 0


# Конкурс пам'яті читає тільки канонічні людиночитані таблиці.
# Це перевірка знання координат, не перевірка семантики або викличності SENS.
MEMORY_DOMAINS = ("D1", "D2", "D3", "D4", "D5", "D6", "D8", "D9", "D10", "D11")
MEMORY_SURFACES = ("укр", "ук", "LISP", "en", "san")


def memory_rows(domain: str, surface: str) -> list[tuple[str, str]]:
    """Точні біти та обрана людська проєкція, без домислювання порожніх назв."""
    path = ROOT / "lib" / "domains" / f"{domain.lower()}.lisp"
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Не вдалося прочитати {path}: {exc}") from exc
    width = int(domain[1:])
    rows: list[tuple[str, str]] = []
    seen: set[str] = set()
    for line in source.splitlines():
        match = re.match(r"^\s*\(([01]+)\s", line)
        if not match:
            continue
        bits = match.group(1)
        if len(bits) != width:
            raise ValueError(f"{path}: неправильна ширина координати {bits}")
        if bits in seen:
            raise ValueError(f"{path}: повторена координата {bits}")
        seen.add(bits)
        label = re.search(r"\(" + re.escape(surface) + r"\s+([^()]*)\)", line)
        if label is None or not label.group(1).strip():
            continue
        rows.append((bits, label.group(1).strip()))
    if not seen:
        raise ValueError(f"{path}: не знайдено точних доменних координат")
    return sorted(rows)


def memory_game(brief: bool, domain: str, surface: str,
                mode: str, count: int, seed: int, list_only: bool) -> int:
    if count < 0:
        print("Кількість запитань має бути невід'ємною.", file=sys.stderr)
        return 2
    domains = MEMORY_DOMAINS if domain == "ALL" else (domain,)
    entries: list[tuple[str, str, str]] = []
    try:
        for dom in domains:
            entries.extend((dom, bits, label)
                           for bits, label in memory_rows(dom, surface))
    except ValueError as exc:
        print(f"ДРАБИНА/ПАМ'ЯТЬ: {exc}", file=sys.stderr)
        return 2
    if not entries:
        print("ДРАБИНА/ПАМ'ЯТЬ: обрана поверхня не має названих координат; тур не зараховано.", file=sys.stderr)
        return 2
    if brief:
        print(f"ДРАБИНА/ПАМ'ЯТЬ: {domain} поверхня={surface} "
              f"названих координат={len(entries)} режим={mode} "
              "семантика=НЕ_ТЕСТУВАЛАСЬ")
        return 0
    if list_only:
        print(f"═══ ДРАБИНА / ДОВІДНИК {domain} · {surface} ═══")
        for dom, bits, label in entries:
            print(f"{dom}:{bits}  {label}")
        print(f"Усього названих координат: {len(entries)}")
        return 0

    rng = random.Random(seed)
    rng.shuffle(entries)
    selected = entries if count == 0 else entries[:count]
    correct = 0
    answered = 0
    print(f"═══ ДРАБИНА / КОНКУРС ПАМ'ЯТІ {domain} ═══")
    print("Тільки точні тотожності з таблиць; викличність не перевіряється.")
    print("Команда :q завершує тур. Літери назв нечутливі до регістру.")
    for index, (dom, bits, label) in enumerate(selected, 1):
        ask_code = mode == "code" or (mode == "mixed" and index % 2 == 0)
        question = label if ask_code else f"{dom}:{bits}"
        expected = f"{dom}:{bits}" if ask_code else label
        target = "домен:біти" if ask_code else f"назва ({surface})"
        try:
            answer = input(f"{index}/{len(selected)}  {question} → {target}: ").strip()
        except EOFError:
            print("\nВвід завершився.")
            break
        if answer == ":q":
            break
        answered += 1
        good = answer == expected if ask_code else answer.casefold() == expected.casefold()
        if good:
            correct += 1
            print("  ✓ Точно")
        else:
            print(f"  ✗ Очікувалось {dom}:{bits} = {label}; отримано {answer or '∅'}")
    print(f"ПІДСУМОК ПАМ'ЯТІ: {correct}/{answered} правильних; "
          f"запитань у турі {len(selected)}; домен={domain}; поверхня={surface}")
    return 0 if correct == answered and answered == len(selected) else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="гра «Драбина»")
    ap.add_argument("--brief", action="store_true")
    ap.add_argument("--track", choices=("semantic", "codec", "d11-codec", "d13", "d13-candidates", "memory"), default="semantic")
    ap.add_argument("--verify", action="store_true",
                    help="запустити нативні Zig-тести для --track codec, d11-codec або d13")
    ap.add_argument("--domain", choices=("ALL",) + MEMORY_DOMAINS, default="D3",
                    help="домен для конкурсу пам'яті")
    ap.add_argument("--surface", choices=MEMORY_SURFACES, default="укр",
                    help="колонка людиночитаної назви")
    ap.add_argument("--mode", choices=("name", "code", "mixed"), default="mixed",
                    help="вгадати назву, біти або чергувати")
    ap.add_argument("--count", type=int, default=8,
                    help="кількість запитань; 0 = усі координати домену")
    ap.add_argument("--seed", type=int, default=0,
                    help="відтворюваний порядок запитань")
    ap.add_argument("--list", action="store_true",
                    help="показати довідник координат у режимі пам'яті")
    args = ap.parse_args(argv)
    if args.verify and args.track not in ("codec", "d11-codec", "d13"):
        ap.error("--verify дозволено лише з --track codec, d11-codec або d13")
    if args.track == "memory":
        return memory_game(args.brief, args.domain, args.surface,
                           args.mode, args.count, args.seed, args.list)
    if args.track == "codec":
        return codec_game(args.brief, args.verify)
    if args.track == "d11-codec":
        return codec_game(args.brief, args.verify, experimental_d11=True)
    if args.track == "d13":
        return codec_game(args.brief, args.verify, experimental_d13=True)
    if args.track == "d13-candidates":
        return d13_game(args.brief)
    return semantic_game(args.brief)


if __name__ == "__main__":
    sys.exit(main())
